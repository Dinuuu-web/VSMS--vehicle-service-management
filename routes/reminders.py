from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, ServiceReminder, Vehicle
from auth import staff_required
from datetime import datetime

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/')
@staff_required
def index():
    reminders = ServiceReminder.query.order_by(ServiceReminder.due_date.asc()).all()
    return render_template('reminders/index.html', reminders=reminders)

@reminders_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add():
    if request.method == 'POST':
        veh_id = request.form.get('vehicle_id')
        veh = Vehicle.query.get(veh_id)
        if not veh:
            flash('Invalid vehicle.', 'error')
            return redirect(url_for('reminders.add'))
            
        rem = ServiceReminder(
            vehicle_id=veh.id,
            customer_id=veh.customer_id,
            reminder_type=request.form.get('reminder_type'),
            due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d'),
            notes=request.form.get('notes')
        )
        db.session.add(rem)
        db.session.commit()
        flash('Reminder created.', 'success')
        return redirect(url_for('reminders.index'))
        
    vehicles = Vehicle.query.all()
    return render_template('reminders/form.html', vehicles=vehicles)

@reminders_bp.route('/<int:id>/mark-sent', methods=['POST'])
@staff_required
def mark_sent(id):
    rem = ServiceReminder.query.get_or_404(id)
    rem.is_sent = True
    db.session.commit()
    flash('Reminder marked as sent.', 'success')
    return redirect(url_for('reminders.index'))

@reminders_bp.route('/<int:id>/delete', methods=['POST'])
@staff_required
def delete(id):
    rem = ServiceReminder.query.get_or_404(id)
    db.session.delete(rem)
    db.session.commit()
    flash('Reminder deleted.', 'success')
    return redirect(url_for('reminders.index'))
