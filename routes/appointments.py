from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user
from models import db, Appointment, Customer, Vehicle, AuditLog
from auth import staff_required
from datetime import datetime, timedelta
import calendar
import re

appointments_bp = Blueprint('appointments', __name__)

def sanitize_html(text):
    if not text: return text
    return re.sub(re.compile('<.*?>'), '', text)

@appointments_bp.route('/')
@staff_required
def index():
    now = datetime.utcnow()
    year = request.args.get('year', now.year, type=int)
    month = request.args.get('month', now.month, type=int)
    return render_template('appointments/calendar.html', year=year, month=month)

@appointments_bp.route('/api/month')
@staff_required
def api_month():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if not year or not month:
        return jsonify({'success': False, 'message': 'Missing year/month'})
    
    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    appts = Appointment.query.filter(
        Appointment.scheduled_at >= start_date,
        Appointment.scheduled_at <= end_date
    ).all()
    
    data = []
    for a in appts:
        data.append({
            'id': a.id,
            'customer': a.customer.name,
            'vehicle': f"{a.vehicle.make} {a.vehicle.model}",
            'service_type': a.service_type,
            'scheduled_at': a.scheduled_at.isoformat(),
            'status': a.status
        })
        
    return jsonify({'success': True, 'data': data})

@appointments_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add():
    if request.method == 'POST':
        c_id = request.form.get('customer_id')
        v_id = request.form.get('vehicle_id')
        sched_str = request.form.get('scheduled_at') # format: YYYY-MM-DDTHH:MM
        svc = sanitize_html(request.form.get('service_type'))
        notes = sanitize_html(request.form.get('notes'))
        
        try:
            sched = datetime.strptime(sched_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format.'}), 400
            
        # Conflict detection: within 2 hours
        conflict = Appointment.query.filter(
            Appointment.vehicle_id == v_id,
            Appointment.scheduled_at >= sched - timedelta(hours=2),
            Appointment.scheduled_at <= sched + timedelta(hours=2),
            Appointment.status.notin_(['Cancelled', 'Completed'])
        ).first()
        
        if conflict:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'message': 'Conflict: Vehicle already has an appointment within 2 hours.'}), 409
            flash('Conflict: Vehicle already has an appointment within 2 hours.', 'error')
            return redirect(url_for('appointments.add'))
            
        appt = Appointment(
            customer_id=c_id, vehicle_id=v_id, scheduled_at=sched,
            service_type=svc, notes=notes
        )
        db.session.add(appt)
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='CREATE', table_name='appointments', record_id=appt.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': True, 'message': 'Appointment booked.'})
            
        flash('Appointment scheduled successfully.', 'success')
        return redirect(url_for('appointments.index', year=sched.year, month=sched.month))
        
    customers = Customer.query.filter_by(is_active=True).all()
    vehicles = Vehicle.query.all()
    return render_template('appointments/form.html', customers=customers, vehicles=vehicles)

@appointments_bp.route('/<int:id>/status', methods=['POST'])
@staff_required
def update_status(id):
    appt = Appointment.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ['Scheduled', 'Confirmed', 'In Progress', 'Completed', 'Cancelled']:
        appt.status = new_status
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='UPDATE_STATUS', table_name='appointments', record_id=appt.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
        flash(f'Appointment status updated to {new_status}.', 'success')
    return redirect(url_for('appointments.index', year=appt.scheduled_at.year, month=appt.scheduled_at.month))
