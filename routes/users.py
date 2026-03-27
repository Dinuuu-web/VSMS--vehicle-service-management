from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User, AuditLog
from auth import admin_required
import bcrypt
import re
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

users_bp = Blueprint('users', __name__)

def sanitize_html(text):
    if not text: return text
    return re.sub(re.compile('<.*?>'), '', text)

@users_bp.route('/')
@admin_required
def list_users():
    try:
        users = User.query.all()
    except SQLAlchemyError as e:
        flash("Database error retrieving users.", "error")
        users = []
    return render_template('users/list.html', users=users)

@users_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        username = sanitize_html(request.form.get('username'))
        email = sanitize_html(request.form.get('email'))
        role = request.form.get('role')
        password = request.form.get('password')
        security_question = sanitize_html(request.form.get('security_question'))
        security_answer = sanitize_html(request.form.get('security_answer'))
        
        try:
            if User.query.filter_by(username=username).first():
                flash('Operator identity already exists.', 'error')
                return redirect(url_for('users.add'))
                
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Additional models properties matching check
            sa_hashed = bcrypt.hashpw(security_answer.encode('utf-8'), bcrypt.gensalt()) if security_answer else None
            
            u = User(
                username=username, 
                email=email, 
                role=role, 
                password_hash=hashed.decode('utf-8'),
                security_question=security_question,
                security_answer_hash=sa_hashed.decode('utf-8') if sa_hashed else None
            )
            db.session.add(u)
            db.session.commit()
            
            flash('Operator activated in the mainframe.', 'success')
            return redirect(url_for('users.list_users'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Database error adding user.", "error")
            return redirect(url_for('users.add'))
            
    return render_template('users/form.html', user=None)

@users_bp.route('/audit')
@admin_required
def audit_logs():
    user_filter = request.args.get('user_id')
    action_filter = request.args.get('action')
    try:
        limit = int(request.args.get('limit', 150))
    except (ValueError, TypeError):
        limit = 150
        
    try:
        query = AuditLog.query
        
        if user_filter:
            query = query.filter(AuditLog.user_id == user_filter)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
            
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        # Get users and actions for the filter dropdowns
        users = User.query.all()
        actions = db.session.query(AuditLog.action).distinct().all()
        actions = [a[0] for a in actions if a[0]]
        
    except SQLAlchemyError as e:
        flash("Database error retrieving audit logs.", "error")
        logs = []
        users = []
        actions = []
        
    return render_template('users/audit.html', 
                           logs=logs,
                           users=users,
                           actions=actions,
                           user_filter=user_filter,
                           action_filter=action_filter,
                           limit_filter=limit)
