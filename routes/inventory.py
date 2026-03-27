from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Inventory, AuditLog
from auth import staff_required
import re

inventory_bp = Blueprint('inventory', __name__)

def check_edit_permission():
    if current_user.role not in ['Admin', 'Mechanic']:
        from flask import abort
        abort(403)

def sanitize_html(text):
    if not text: return text
    return re.sub(re.compile('<.*?>'), '', text)

@inventory_bp.route('/')
@staff_required
def list_inventory():
    category = request.args.get('category', '')
    query = Inventory.query
    if category:
        query = query.filter_by(category=category)
        
    items = query.order_by(Inventory.part_name.asc()).all()
    categories_list = db.session.query(Inventory.category).distinct().all()
    categories_list = [c[0] for c in categories_list if c[0]]
    
    return render_template('inventory/list.html', items=items, categories=categories_list, selected_category=category)

@inventory_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add():
    check_edit_permission()
    
    if request.method == 'POST':
        part_name = sanitize_html(request.form.get('part_name'))
        part_number = sanitize_html(request.form.get('part_number'))
        quantity = request.form.get('quantity', 0)
        unit_price = request.form.get('unit_price', 0.0)
        reorder_level = request.form.get('reorder_level', 5)
        supplier = sanitize_html(request.form.get('supplier'))
        category = sanitize_html(request.form.get('category'))
        
        if part_number and Inventory.query.filter_by(part_number=part_number).first():
            flash('Part number already exists.', 'error')
            return render_template('inventory/form.html', item=None)
            
        item = Inventory(
            part_name=part_name, part_number=part_number, quantity=quantity,
            unit_price=unit_price, reorder_level=reorder_level, supplier=supplier, category=category
        )
        db.session.add(item)
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='CREATE', table_name='inventory', record_id=item.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Part added to inventory successfully.', 'success')
        return redirect(url_for('inventory.list_inventory'))
        
    return render_template('inventory/form.html', item=None)

@inventory_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@staff_required
def edit(id):
    check_edit_permission()
    item = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        item.part_name = sanitize_html(request.form.get('part_name'))
        pn = sanitize_html(request.form.get('part_number'))
        
        if pn:
            existing = Inventory.query.filter_by(part_number=pn).first()
            if existing and existing.id != item.id:
                flash('Part number already exists.', 'error')
                return render_template('inventory/form.html', item=item)
            
        item.part_number = pn
        item.unit_price = request.form.get('unit_price')
        item.reorder_level = request.form.get('reorder_level')
        item.supplier = sanitize_html(request.form.get('supplier'))
        item.category = sanitize_html(request.form.get('category'))
        
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='UPDATE', table_name='inventory', record_id=item.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        flash('Inventory item updated successfully.', 'success')
        return redirect(url_for('inventory.list_inventory'))
        
    return render_template('inventory/form.html', item=item)

@inventory_bp.route('/<int:id>/restock', methods=['POST'])
@staff_required
def restock(id):
    check_edit_permission()
    item = Inventory.query.get_or_404(id)
    add_qty = int(request.form.get('quantity', 0))
    
    if add_qty > 0:
        item.quantity += add_qty
        db.session.commit()
        
        log = AuditLog(user_id=current_user.id, action='RESTOCK', table_name='inventory', record_id=item.id, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'new_quantity': item.quantity, 'message': f'Added {add_qty} units.'})
    
    return jsonify({'success': False, 'message': 'Invalid quantity.'})
