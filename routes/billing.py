from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, Response
from flask_login import login_required, current_user
from models import db, JobCard, Invoice, AuditLog
from auth import staff_required
from datetime import datetime, timedelta
import os
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

billing_bp = Blueprint('billing', __name__)

@billing_bp.route('/')
@staff_required
def list_invoices():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    query = Invoice.query
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Invoice.created_at >= start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Add one day to include the entire end_date
            query = query.filter(Invoice.created_at < end_date + timedelta(days=1))
        except ValueError:
            pass
            
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    # Also show delivered jobs without invoices
    jobs_without_inv = JobCard.query.filter(JobCard.status == 'Delivered', ~JobCard.invoice.has()).all()
    
    return render_template('billing/list.html', 
                           invoices=invoices, 
                           pending_jobs=jobs_without_inv,
                           start_date=start_date_str,
                           end_date=end_date_str)

@billing_bp.route('/invoice/<int:job_id>', methods=['GET', 'POST'])
@staff_required
def generate_invoice(job_id):
    job = JobCard.query.get_or_404(job_id)
    
    if job.invoice:
        flash('Invoice already exists. Viewing current invoice.', 'info')
        return redirect(url_for('billing.view_invoice', id=job.invoice[0].id))
        
    if request.method == 'POST':
        # Calculate subtotal, GST (18%), and create
        subtotal_services = sum(js.price * js.quantity for js in job.job_services)
        subtotal_parts = sum(jp.unit_price * jp.quantity_used for jp in job.job_parts)
        subtotal = subtotal_services + subtotal_parts
        
        tax_amount = subtotal * 0.18  # 18% GST
        grand_total = subtotal + tax_amount
        
        inv = Invoice(
            job_card_id=job.id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=grand_total,
            payment_status='Pending'
        )
        db.session.add(inv)
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='CREATE_INVOICE', table_name='invoices', record_id=inv.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Invoice generated securely.', 'success')
        return redirect(url_for('billing.view_invoice', id=inv.id))
        
    # Pre-calculate to show preview
    subtotal = sum(js.price * js.quantity for js in job.job_services) + sum(jp.unit_price * jp.quantity_used for jp in job.job_parts)
    tax = subtotal * 0.18
    return render_template('billing/preview.html', job=job, subtotal=subtotal, tax=tax, total=subtotal+tax)

@billing_bp.route('/invoice/view/<int:id>')
@staff_required
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('billing/invoice.html', invoice=invoice)

@billing_bp.route('/invoice/<int:id>/pay', methods=['POST'])
@staff_required
def pay_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    invoice.payment_status = 'Paid'
    db.session.commit()
    
    log = AuditLog(user_id=current_user.id, action='PAY_INVOICE', table_name='invoices', record_id=invoice.id, ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    
    flash('Payment recorded successfully.', 'success')
    return redirect(url_for('billing.view_invoice', id=invoice.id))

@billing_bp.route('/invoice/<int:id>/pdf')
@staff_required
def download_pdf(id):
    invoice = Invoice.query.get_or_404(id)
    job = invoice.job_card
    
    filename = f"Invoice_{invoice.id}.pdf"
    filepath = os.path.join(current_app.config['PDF_DIR'], filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "VSMS - Vehicle Service Management System - TAX INVOICE")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Invoice #: INV-{invoice.id:05d}")
    c.drawString(50, 700, f"Date: {invoice.created_at.strftime('%Y-%m-%d')}")
    c.drawString(50, 680, f"Status: {invoice.payment_status}")
    
    c.drawString(400, 720, f"Billed To: {job.customer.name}")
    c.drawString(400, 700, f"Vehicle: {job.vehicle.license_plate}")
    
    c.line(50, 660, 550, 660)
    
    # Items
    y = 630
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Description")
    c.drawString(400, y, "Amount (USD)")
    y -= 20
    
    c.setFont("Helvetica", 11)
    
    for js in job.job_services:
        c.drawString(50, y, f"Service: {js.service.name}")
        c.drawString(400, y, f"${js.price:.2f}")
        y -= 20
        
    for jp in job.job_parts:
        c.drawString(50, y, f"Part: {jp.part.part_name} (x{jp.quantity_used})")
        c.drawString(400, y, f"${(jp.unit_price * jp.quantity_used):.2f}")
        y -= 20
        
    c.line(50, y, 550, y)
    y -= 30
    
    # Totals
    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, y, "Subtotal:")
    c.drawString(400, y, f"${invoice.subtotal:.2f}")
    y -= 20
    
    c.drawString(300, y, "GST (18%):")
    c.drawString(400, y, f"${invoice.tax_amount:.2f}")
    y -= 20
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(300, y, "TOTAL DUE:")
    c.drawString(400, y, f"${invoice.total:.2f}")
    
    c.save()
    
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@billing_bp.route('/export')
@staff_required
def export_csv():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    query = Invoice.query
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            query = query.filter(Invoice.created_at >= start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            query = query.filter(Invoice.created_at < end_date + timedelta(days=1))
        except ValueError:
            pass
            
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        
        # Header
        writer.writerow(['Invoice ID', 'Job Card ID', 'Customer Name', 'Vehicle Plate', 'Date', 'Subtotal', 'Tax', 'Total (INR)', 'Payment Status'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        for inv in invoices:
            job = inv.job_card
            customer_name = job.customer.name if job and job.customer else 'N/A'
            vehicle_plate = job.vehicle.license_plate if job and job.vehicle else 'N/A'
            
            writer.writerow([
                f"INV-{inv.id:05d}",
                f"WO-{inv.job_card_id:04d}",
                customer_name,
                vehicle_plate,
                inv.created_at.strftime('%Y-%m-%d %H:%M'),
                f"{inv.subtotal:.2f}",
                f"{inv.tax_amount:.2f}",
                f"{inv.total:.2f}",
                inv.payment_status
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
    response = Response(generate(), mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename='invoices_export.csv')
    return response
