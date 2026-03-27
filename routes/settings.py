from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, GarageSettings, User
from auth import staff_required
import bcrypt
import os
from werkzeug.utils import secure_filename

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    garage = GarageSettings.query.first()
    if not garage:
        garage = GarageSettings()
        db.session.add(garage)
        db.session.commit()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'garage_profile' and current_user.role == 'Admin':
            garage.garage_name = request.form.get('garage_name')
            garage.tagline = request.form.get('tagline')
            garage.address = request.form.get('address')
            garage.gst_number = request.form.get('gst_number')
            garage.phone = request.form.get('phone')
            garage.email = request.form.get('email')
            garage.working_hours = request.form.get('working_hours')
            try:
                garage.total_bays = int(request.form.get('total_bays'))
            except:
                pass
            garage.currency_symbol = request.form.get('currency_symbol')
            
            logo = request.files.get('logo')
            if logo and logo.filename:
                filename = secure_filename(logo.filename)
                upload_dir = os.path.join('static', 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                logo.save(os.path.join(upload_dir, filename))
                garage.logo_path = f'/static/uploads/{filename}'
            db.session.commit()
            flash('Garage profile updated.', 'success')
            
        elif action == 'account':
            user = User.query.get(current_user.id)
            if request.form.get('email'):
                user.email = request.form.get('email')
            if request.form.get('password'):
                user.password_hash = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if request.form.get('security_question'):
                user.security_question = request.form.get('security_question')
                user.security_answer_hash = bcrypt.hashpw(request.form.get('security_answer').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.session.commit()
            flash('Account settings updated.', 'success')
            
    return render_template('settings/index.html', garage=garage)
