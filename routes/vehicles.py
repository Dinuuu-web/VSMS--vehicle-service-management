from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Vehicle, Customer, JobCard, AuditLog
from auth import staff_required
import re
from datetime import datetime

vehicles_bp = Blueprint('vehicles', __name__)

def check_edit_permission():
    if current_user.role not in ['Admin', 'Receptionist']:
        from flask import abort
        abort(403)

def sanitize_html(text):
    if not text: return text
    return re.sub(re.compile('<.*?>'), '', text)

@vehicles_bp.route('/')
@staff_required
def list_vehicles():
    search = request.args.get('search', '')
    query = Vehicle.query.join(Customer)
    if search:
        s = sanitize_html(search)
        query = query.filter(
            (Vehicle.license_plate.ilike(f'%{s}%')) | 
            (Vehicle.make.ilike(f'%{s}%')) | 
            (Vehicle.model.ilike(f'%{s}%')) |
            (Customer.name.ilike(f'%{s}%'))
        )
    vehicles = query.order_by(Vehicle.created_at.desc()).all()
    return render_template('vehicles/list.html', vehicles=vehicles, search=search)

@vehicles_bp.route('/<int:id>')
@staff_required
def detail(id):
    vehicle = Vehicle.query.get_or_404(id)
    jobs = JobCard.query.filter_by(vehicle_id=id).order_by(JobCard.created_at.desc()).all()
    
    # Simple Health Score Calculation
    score = 100
    if vehicle.mileage:
        score -= min(int(vehicle.mileage / 10000) * 2, 30) # cap mileage penalty 30
    
    if jobs:
        last_service = jobs[0].created_at
        days_since = (datetime.utcnow() - last_service).days
        if days_since > 365:
            score -= 30
        elif days_since > 180:
            score -= 15
    else:
        score -= 20
        
    score = max(min(score, 100), 0)
    
    return render_template('vehicles/detail.html', vehicle=vehicle, jobs=jobs, health_score=score)

@vehicles_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add():
    check_edit_permission()
    
    if request.method == 'POST':
        c_id = request.form.get('customer_id')
        make = sanitize_html(request.form.get('make'))
        model = sanitize_html(request.form.get('model'))
        year = request.form.get('year')
        plate = sanitize_html(request.form.get('license_plate')).upper()
        vin = sanitize_html(request.form.get('vin'))
        color = sanitize_html(request.form.get('color'))
        mileage = request.form.get('mileage')
        
        if Vehicle.query.filter_by(license_plate=plate).first():
            flash('License plate already registered.', 'error')
            customers = Customer.query.filter_by(is_active=True).all()
            return render_template('vehicles/form.html', vehicle=None, customers=customers)
            
        v = Vehicle(
            customer_id=c_id, make=make, model=model, year=year or None,
            license_plate=plate, vin=vin, color=color, mileage=mileage or None
        )
        db.session.add(v)
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='CREATE', table_name='vehicles', record_id=v.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Vehicle registered successfully.', 'success')
        return redirect(url_for('vehicles.detail', id=v.id))
        
    cid = request.args.get('customer_id')
    customers = Customer.query.filter_by(is_active=True).all()
    return render_template('vehicles/form.html', vehicle=None, customers=customers, selected_customer=cid)

@vehicles_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@staff_required
def edit(id):
    check_edit_permission()
    vehicle = Vehicle.query.get_or_404(id)
    
    if request.method == 'POST':
        vehicle.customer_id = request.form.get('customer_id')
        vehicle.make = sanitize_html(request.form.get('make'))
        vehicle.model = sanitize_html(request.form.get('model'))
        vehicle.year = request.form.get('year') or None
        plate = sanitize_html(request.form.get('license_plate')).upper()
        
        # Ensure unique plate
        existing = Vehicle.query.filter_by(license_plate=plate).first()
        if existing and existing.id != vehicle.id:
            flash('License plate already exists.', 'error')
            customers = Customer.query.filter_by(is_active=True).all()
            return render_template('vehicles/form.html', vehicle=vehicle, customers=customers)
            
        vehicle.license_plate = plate
        vehicle.vin = sanitize_html(request.form.get('vin'))
        vehicle.color = sanitize_html(request.form.get('color'))
        vehicle.mileage = request.form.get('mileage') or None
        
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='UPDATE', table_name='vehicles', record_id=vehicle.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Vehicle updated successfully.', 'success')
        return redirect(url_for('vehicles.detail', id=vehicle.id))
        
    customers = Customer.query.filter_by(is_active=True).all()
    return render_template('vehicles/form.html', vehicle=vehicle, customers=customers)
