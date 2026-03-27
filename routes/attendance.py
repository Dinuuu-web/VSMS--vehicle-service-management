from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, MechanicAttendance, User
from auth import staff_required
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@staff_required
def index():
    today = datetime.utcnow().date()
    if current_user.role == 'Admin':
        records = MechanicAttendance.query.order_by(MechanicAttendance.date.desc()).all()
    else:
        records = MechanicAttendance.query.filter_by(mechanic_id=current_user.id).order_by(MechanicAttendance.date.desc()).all()
        
    today_record = MechanicAttendance.query.filter_by(mechanic_id=current_user.id, date=today).first()
    return render_template('attendance/index.html', records=records, today_record=today_record)

@attendance_bp.route('/check-in', methods=['POST'])
@staff_required
def check_in():
    today = datetime.utcnow().date()
    existing = MechanicAttendance.query.filter_by(mechanic_id=current_user.id, date=today).first()
    if not existing:
        record = MechanicAttendance(mechanic_id=current_user.id, check_in=datetime.utcnow(), date=today)
        db.session.add(record)
        db.session.commit()
        flash('Checked in successfully.', 'success')
    return redirect(url_for('attendance.index'))

@attendance_bp.route('/check-out', methods=['POST'])
@staff_required
def check_out():
    today = datetime.utcnow().date()
    record = MechanicAttendance.query.filter_by(mechanic_id=current_user.id, date=today).first()
    if record and not record.check_out:
        record.check_out = datetime.utcnow()
        diff = record.check_out - record.check_in
        record.hours_worked = diff.total_seconds() / 3600.0
        db.session.commit()
        flash('Checked out successfully.', 'success')
    return redirect(url_for('attendance.index'))
