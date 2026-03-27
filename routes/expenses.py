from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, ExpenseRecord
from auth import admin_required
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/')
@admin_required
def index():
    expenses = ExpenseRecord.query.order_by(ExpenseRecord.date.desc()).all()
    return render_template('expenses/index.html', expenses=expenses)

@expenses_bp.route('/add', methods=['POST'])
@admin_required
def add():
    category = request.form.get('category')
    description = request.form.get('description')
    amount = float(request.form.get('amount', 0))
    date_str = request.form.get('date')
    
    dt = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
    
    rec = ExpenseRecord(category=category, description=description, amount=amount, date=dt, added_by=current_user.id)
    db.session.add(rec)
    db.session.commit()
    flash('Expense recorded.', 'success')
    return redirect(url_for('expenses.index'))
