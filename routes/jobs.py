from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from models import db, JobCard, Customer, Vehicle, Service, Inventory, JobService, JobPart, AuditLog, User
from auth import staff_required, mechanic_required
from datetime import datetime
import uuid
import os
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

jobs_bp = Blueprint('jobs', __name__)

def generate_job_qr(token, host_url):
    url = f"{host_url}status/{token}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    filename = f"{token}.png"
    filepath = os.path.join(current_app.config['QR_DIR'], filename)
    img.save(filepath)
    return f"qrcodes/{filename}"

@jobs_bp.route('/kanban')
@staff_required
def kanban():
    jobs = JobCard.query.all()
    statuses = ['Received', 'Diagnosing', 'In Progress', 'Quality Check', 'Ready', 'Delivered']
    board = {s: [] for s in statuses}
    for j in jobs:
        if j.status in board:
            board[j.status].append(j)
    
    return render_template('jobs/kanban.html', board=board, statuses=statuses)

@jobs_bp.route('/<int:id>')
@staff_required
def detail(id):
    job = JobCard.query.get_or_404(id)
    services = Service.query.all()
    inventory = Inventory.query.all()
    mechanics = User.query.filter(User.role.in_(['Admin', 'Mechanic'])).all()
    
    # Calculate current total dynamically for display
    current_total = sum(js.price * js.quantity for js in job.job_services) + sum(jp.unit_price * jp.quantity_used for jp in job.job_parts)
    
    return render_template('jobs/detail.html', job=job, services=services, inventory=inventory, mechanics=mechanics, current_total=current_total)

@jobs_bp.route('/create', methods=['GET', 'POST'])
@mechanic_required
def create():
    if request.method == 'POST':
        v_id = request.form.get('vehicle_id')
        mech_id = request.form.get('mechanic_id') or None
        notes = request.form.get('notes')
        
        vehicle = Vehicle.query.get_or_404(v_id)
        
        job = JobCard(
            vehicle_id=vehicle.id,
            customer_id=vehicle.customer_id,
            mechanic_id=mech_id,
            status='Received',
            notes=notes
        )
        db.session.add(job)
        db.session.commit() # Commit to generate ID
        
        # Generate QR code
        job.generate_qr_token()
        db.session.commit() # Save token
        
        qr_path = generate_job_qr(job.qr_token, request.host_url)
        job.qr_code_path = qr_path
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='CREATE', table_name='job_cards', record_id=job.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Job Card created successfully with QR tracking code.', 'success')
        return redirect(url_for('jobs.detail', id=job.id))
        
    v_id = request.args.get('vehicle')
    vehicles = Vehicle.query.all()
    mechanics = User.query.filter(User.role.in_(['Admin', 'Mechanic'])).all()
    return render_template('jobs/form.html', vehicles=vehicles, mechanics=mechanics, selected_vehicle=v_id)

@jobs_bp.route('/<int:id>/status', methods=['POST'])
@mechanic_required
def update_status(id):
    job = JobCard.query.get_or_404(id)
    new_status = request.form.get('status')
    
    statuses = ['Received', 'Diagnosing', 'In Progress', 'Quality Check', 'Ready', 'Delivered']
    
    if new_status in statuses:
        # Prevent jumping backwards in logic if needed, but for simplicity allow Admin/Mechanic to correct state
        job.status = new_status
        if new_status == 'Delivered':
            job.completed_at = datetime.utcnow()
            
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='UPDATE_STATUS', table_name='job_cards', record_id=job.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({'success': True, 'new_status': new_status})
        
        flash(f'Status updated to {new_status}.', 'success')
    return redirect(url_for('jobs.detail', id=job.id))

@jobs_bp.route('/<int:id>/add-service', methods=['POST'])
@mechanic_required
def add_service(id):
    job = JobCard.query.get_or_404(id)
    svc_id = request.form.get('service_id')
    
    svc = Service.query.get_or_404(svc_id)
    js = JobService(job_card_id=job.id, service_id=svc.id, price=svc.base_price, quantity=1)
    db.session.add(js)
    db.session.commit()
    
    log = AuditLog(user_id=current_user.id, action='ADD_SERVICE', table_name='job_cards', record_id=job.id, ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({'success': True, 'item': svc.name, 'price': svc.base_price})
    return redirect(url_for('jobs.detail', id=job.id))

@jobs_bp.route('/<int:id>/add-part', methods=['POST'])
@mechanic_required
def add_part(id):
    job = JobCard.query.get_or_404(id)
    part_id = request.form.get('inventory_id')
    qty = int(request.form.get('quantity', 1))
    
    part = Inventory.query.get_or_404(part_id)
    
    if part.quantity < qty:
        return jsonify({'success': False, 'message': 'Insufficient stock!'}), 400
        
    # Deduct stock
    part.quantity -= qty
    
    jp = JobPart(job_card_id=job.id, inventory_id=part.id, quantity_used=qty, unit_price=part.unit_price)
    db.session.add(jp)
    db.session.commit()
    
    log = AuditLog(user_id=current_user.id, action='ADD_PART', table_name='job_cards', record_id=job.id, ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({'success': True, 'part': part.part_name, 'price': part.unit_price, 'qty': qty})
    return redirect(url_for('jobs.detail', id=job.id))

@jobs_bp.route('/<int:id>/pdf')
@staff_required
def download_pdf(id):
    job = JobCard.query.get_or_404(id)
    
    filename = f"job_card_{job.id}.pdf"
    filepath = os.path.join(current_app.config['PDF_DIR'], filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "VSMS - Vehicle Service Management System")
    
    c.setFont("Helvetica", 14)
    c.drawString(50, 720, f"JOB CARD #WO-{job.id:04d}")
    c.drawString(400, 720, f"Date: {job.created_at.strftime('%Y-%m-%d')}")
    
    c.line(50, 710, 550, 710)
    
    # Customer Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 680, "Customer Info:")
    c.setFont("Helvetica", 12)
    c.drawString(50, 660, f"Name: {job.customer.name}")
    c.drawString(50, 640, f"Phone: {job.customer.phone or 'N/A'}")
    
    # Vehicle Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, 680, "Vehicle Info:")
    c.setFont("Helvetica", 12)
    c.drawString(300, 660, f"Vehicle: {job.vehicle.year or ''} {job.vehicle.make} {job.vehicle.model}")
    c.drawString(300, 640, f"Plate: {job.vehicle.license_plate}")
    c.drawString(300, 620, f"Mileage: {job.vehicle.mileage or 0} km")
    
    c.line(50, 600, 550, 600)
    
    # Services
    y = 570
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Services Performed:")
    y -= 20
    c.setFont("Helvetica", 11)
    if job.job_services:
        for js in job.job_services:
            c.drawString(60, y, f"- {js.service.name}")
            c.drawString(480, y, f"${js.price:.2f}")
            y -= 20
    else:
        c.drawString(60, y, "No services added yet.")
        y -= 20
        
    y -= 10
    c.line(50, y, 550, y)
    y -= 20
    
    # Parts
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Parts Used:")
    y -= 20
    c.setFont("Helvetica", 11)
    if job.job_parts:
        for jp in job.job_parts:
            c.drawString(60, y, f"- {jp.quantity_used}x {jp.part.part_name}")
            c.drawString(480, y, f"${(jp.unit_price * jp.quantity_used):.2f}")
            y -= 20
    else:
        c.drawString(60, y, "No parts used yet.")
        y -= 20
        
    # QR Code placeholder reference (if generated)
    if job.qr_code_path:
        # Assuming path is static/qrcodes/...
        full_qr_path = os.path.join(current_app.config['QR_DIR'], os.path.basename(job.qr_code_path))
        if os.path.exists(full_qr_path):
            c.drawImage(full_qr_path, 450, 50, width=100, height=100)
            c.drawString(450, 40, "Scan to track status")

    c.save()
    
    return send_file(filepath, as_attachment=True, download_name=filename)
