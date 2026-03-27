from flask import Blueprint, render_template, request, Response
from flask_login import current_user
from models import db, Invoice, JobCard, Customer, User, Inventory, JobPart
from auth import admin_required
import csv
from io import StringIO
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@admin_required
def dashboard():
    revenue = db.session.query(func.sum(Invoice.total)).filter(Invoice.payment_status == 'Paid').scalar() or 0
    
    # Completed jobs count
    completed_jobs = JobCard.query.filter_by(status='Delivered').count()
    
    # Mechanic Performance
    mechanics = db.session.query(
        User.username, 
        func.count(JobCard.id)
    ).join(JobCard, User.id == JobCard.mechanic_id)\
     .filter(JobCard.status == 'Delivered')\
     .group_by(User.id).all()
     
    # Top Customers by Revenue
    top_customers = db.session.query(
        Customer.name, 
        func.sum(Invoice.total)
    ).join(JobCard, Customer.id == JobCard.customer_id)\
     .join(Invoice, JobCard.id == Invoice.job_card_id)\
     .filter(Invoice.payment_status == 'Paid')\
     .group_by(Customer.id)\
     .order_by(func.sum(Invoice.total).desc())\
     .limit(5).all()
     
    return render_template('reports/dashboard.html', 
                           revenue=revenue, 
                           completed_jobs=completed_jobs,
                           mechanics=mechanics, 
                           top_customers=top_customers)

@reports_bp.route('/export/revenue')
@admin_required
def export_revenue():
    invoices = Invoice.query.filter_by(status='Paid').all()
    
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(['Invoice ID', 'Date', 'Customer', 'Subtotal', 'Tax', 'Grand Total'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        for inv in invoices:
            writer.writerow([
                f"INV-{inv.id:05d}", 
                inv.created_at.strftime('%Y-%m-%d'), 
                inv.job_card.customer.name, 
                f"{inv.subtotal:.2f}", 
                f"{inv.tax_amount:.2f}", 
                f"{inv.total:.2f}"
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
    return Response(generate(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=gms_revenue_report.csv'})
