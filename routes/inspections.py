from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, VehicleInspection, JobCard, Vehicle
from auth import staff_required

inspections_bp = Blueprint('inspections', __name__)

@inspections_bp.route('/')
@staff_required
def index():
    inspections = VehicleInspection.query.order_by(VehicleInspection.created_at.desc()).all()
    return render_template('inspections/index.html', inspections=inspections)

@inspections_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add():
    job_id = request.args.get('job_id')
    job = JobCard.query.get(job_id) if job_id else None
    
    if request.method == 'POST':
        cats = ['engine', 'brake', 'tire', 'battery', 'ac', 'lights', 'body']
        score_map = {'Good': 3, 'Average': 2, 'Poor': 1}
        total = 0
        vals = {}
        for c in cats:
            v = request.form.get(f'{c}_condition')
            vals[c] = v if v else 'Poor'
            total += score_map.get(vals[c], 1)
            
        overall = int((total / (len(cats) * 3)) * 100)
        
        job_card_id = request.form.get('job_card_id')
        job_card_id = int(job_card_id) if job_card_id else None
        
        ins = VehicleInspection(
            job_card_id=job_card_id,
            vehicle_id=int(request.form.get('vehicle_id')),
            inspector_id=current_user.id,
            engine_condition=vals['engine'],
            brake_condition=vals['brake'],
            tire_condition=vals['tire'],
            battery_condition=vals['battery'],
            ac_condition=vals['ac'],
            lights_condition=vals['lights'],
            body_condition=vals['body'],
            overall_score=overall,
            notes=request.form.get('notes')
        )
        db.session.add(ins)
        db.session.commit()
        flash('Inspection report created.', 'success')
        return redirect(url_for('inspections.index'))
        
    vehicles = Vehicle.query.all()
    jobs = JobCard.query.all()
    return render_template('inspections/form.html', vehicles=vehicles, jobs=jobs, selected_job=job)
