import jwt
import bcrypt
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, session, render_template, redirect, url_for, flash, make_response, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, AuditLog

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt(user):
    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')

def log_audit(user_id, action, table_name=None, record_id=None):
    ip_address = request.remote_addr if request else '127.0.0.1'
    log = AuditLog(user_id=user_id, action=action, table_name=table_name, record_id=record_id, ip_address=ip_address)
    db.session.add(log)
    db.session.commit()

def sanitize_html(text):
    if not text:
        return text
    # Strip HTML tags
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# Decorators
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'Admin':
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def mechanic_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['Admin', 'Mechanic']:
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role not in ['Admin', 'Mechanic', 'Receptionist']:
            from flask import abort
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        try:
            username = sanitize_html(request.form.get('username'))
            password = request.form.get('password') # We don't sanitize pass
            
            user = User.query.filter_by(username=username).first()
            
            if user:
                # Check lockout
                if user.lockout_until and user.lockout_until > datetime.utcnow():
                    flash('Account locked out. Try again later.', 'error')
                    return render_template('auth/login.html')
                    
                if check_password(password, user.password_hash):
                    login_user(user)
                    user.failed_attempts = 0
                    user.lockout_until = None
                    user.last_login = datetime.utcnow()
                    log_audit(user.id, 'LOGIN', 'users', user.id)
                    db.session.commit()
                    
                    token = generate_jwt(user)
                    resp = make_response(redirect('/dashboard'))
                    resp.set_cookie('jwt_token', token, httponly=True, secure=False, samesite='Lax') # Secure=False for dev
                    flash('Login successful.', 'success')
                    return resp
                else:
                    user.failed_attempts += 1
                    if user.failed_attempts >= 5:
                        user.lockout_until = datetime.utcnow() + timedelta(minutes=15)
                        flash('Account locked for 15 minutes due to too many failed attempts.', 'error')
                    else:
                        flash('Invalid username or password', 'error')
                    db.session.commit()
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            return f"Error: {str(e)}", 500
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(current_user.id, 'LOGOUT', 'users', current_user.id)
    logout_user()
    resp = make_response(redirect(url_for('auth.login')))
    resp.set_cookie('jwt_token', '', expires=0)
    flash('Logged out successfully.', 'success')
    return resp

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = sanitize_html(request.form.get('username'))
        email = sanitize_html(request.form.get('email'))
        password = request.form.get('password')
        role = request.form.get('role', 'Mechanic')
        sq = request.form.get('security_question')
        sa = request.form.get('security_answer')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))
            
        hashed = hash_password(password)
        sa_hashed = hash_password(sa) if sa else None
        
        user = User(username=username, email=email, role=role, password_hash=hashed, security_question=sq, security_answer_hash=sa_hashed)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user and user.security_question:
            session['reset_user_id'] = user.id
            return render_template('auth/forgot_password_step2.html', question=user.security_question)
        flash('User not found or no security question set.', 'error')
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    user_id = session.get('reset_user_id')
    if not user_id:
        return redirect(url_for('auth.forgot_password'))
    user = User.query.get(user_id)
    
    answer = request.form.get('security_answer')
    if answer:
        if check_password(answer, user.security_answer_hash):
            session['reset_verified'] = True
            return render_template('auth/reset_password.html')
        flash('Incorrect answer.', 'error')
        return render_template('auth/forgot_password_step2.html', question=user.security_question)
        
    if session.get('reset_verified'):
        new_pass = request.form.get('password')
        user.password_hash = hash_password(new_pass)
        db.session.commit()
        session.pop('reset_user_id', None)
        session.pop('reset_verified', None)
        flash('Password reset successfully.', 'success')
        return redirect(url_for('auth.login'))
        
    return redirect(url_for('auth.forgot_password'))
