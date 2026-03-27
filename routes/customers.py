from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Customer, AuditLog
from auth import staff_required
import re

customers_bp = Blueprint('customers', __name__)

def check_edit_permission():
    if current_user.role not in ['Admin', 'Receptionist']:
        from flask import abort
        abort(403)

def sanitize_html(text):
    if not text: return text
    return re.sub(re.compile('<.*?>'), '', text)

@customers_bp.route('/')
@staff_required
def list_customers():
    search = request.args.get('search', '')
    query = Customer.query.filter_by(is_active=True)
    if search:
        search_clean = sanitize_html(search)
        query = query.filter(
            (Customer.name.ilike(f'%{search_clean}%')) | 
            (Customer.phone.ilike(f'%{search_clean}%')) | 
            (Customer.email.ilike(f'%{search_clean}%'))
        )
    customers = query.order_by(Customer.created_at.desc()).all()
    return render_template('customers/list.html', customers=customers, search=search)

@customers_bp.route('/<int:id>')
@staff_required
def detail(id):
    customer = Customer.query.filter_by(id=id, is_active=True).first_or_404()
    return render_template('customers/detail.html', customer=customer)

@customers_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add():
    check_edit_permission()
    if request.method == 'POST':
        name = sanitize_html(request.form.get('name'))
        phone = sanitize_html(request.form.get('phone'))
        email = sanitize_html(request.form.get('email'))
        address = sanitize_html(request.form.get('address'))
        
        c = Customer(name=name, phone=phone, email=email, address=address)
        db.session.add(c)
        db.session.commit()
        
        # Log Audit
        log = AuditLog(user_id=current_user.id, action='CREATE', table_name='customers', record_id=c.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Customer added successfully.', 'success')
        return redirect(url_for('customers.detail', id=c.id))
        
    return render_template('customers/form.html', customer=None)

@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@staff_required
def edit(id):
    check_edit_permission()
    customer = Customer.query.filter_by(id=id, is_active=True).first_or_404()
    
    if request.method == 'POST':
        customer.name = sanitize_html(request.form.get('name'))
        customer.phone = sanitize_html(request.form.get('phone'))
        customer.email = sanitize_html(request.form.get('email'))
        customer.address = sanitize_html(request.form.get('address'))
        
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='UPDATE', table_name='customers', record_id=customer.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Customer updated successfully.', 'success')
        return redirect(url_for('customers.detail', id=customer.id))
        
    return render_template('customers/form.html', customer=customer)

@customers_bp.route('/<int:id>/delete', methods=['POST'])
@staff_required
def delete(id):
    check_edit_permission()
    customer = Customer.query.get_or_404(id)
    customer.is_active = False # Soft delete
    db.session.commit()
    
    log = AuditLog(user_id=current_user.id, action='SOFT_DELETE', table_name='customers', record_id=customer.id, ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    
    flash('Customer deleted successfully.', 'success')
    return redirect(url_for('customers.list_customers'))
