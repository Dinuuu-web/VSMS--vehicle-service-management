# pyre-ignore-all-errors[21, 16]
from flask import Blueprint, render_template, request, jsonify  # type: ignore
from flask_login import login_required  # type: ignore
from models import db, JobCard, Invoice, Vehicle, Inventory, Appointment, Customer  # type: ignore
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_  # type: ignore
from sqlalchemy.orm import joinedload  # type: ignore

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    today = datetime.utcnow().date()
    timeframe = request.args.get('timeframe', 'today')

    # Calculate date ranges
    # We will use >= start and < end for exact matching of datetimes
    if timeframe == 'monthly':
        start_date = today.replace(day=1)
        # Prev month range
        if start_date.month == 1:
            prev_start = start_date.replace(year=start_date.year-1, month=12)
        else:
            prev_start = start_date.replace(month=start_date.month-1)
        prev_end = start_date
        end_date = today + timedelta(days=1)
    elif timeframe == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date
        end_date = today + timedelta(days=1)
    else: # today
        start_date = today
        prev_start = today - timedelta(days=1)
        prev_end = today
        end_date = today + timedelta(days=1)

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.min.time())
    prev_start_dt = datetime.combine(prev_start, datetime.min.time())
    prev_end_dt = datetime.combine(prev_end, datetime.min.time())

    # Helper function for safe percentage change
    def calc_pct_change(current, previous):
        if previous == 0 and current == 0: return 0
        if previous == 0: return 100
        return round(((current - previous) / previous) * 100)

    # 1. Total (Pending) jobs 
    # Current
    pending_jobs = JobCard.query.filter(
        JobCard.status == 'Received',
        JobCard.created_at >= start_dt,
        JobCard.created_at < end_dt
    ).count()
    # Prev
    prev_pending_jobs = JobCard.query.filter(
        JobCard.status == 'Received',
        JobCard.created_at >= prev_start_dt,
        JobCard.created_at < prev_end_dt
    ).count()
    pending_pct = calc_pct_change(pending_jobs, prev_pending_jobs)
    
    # 2. Revenue (paid invoices)
    revenue_query = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.payment_status == 'Paid',
        Invoice.created_at >= start_dt,
        Invoice.created_at < end_dt
    ).scalar()
    current_revenue = revenue_query if revenue_query else 0.0

    prev_revenue_query = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.payment_status == 'Paid',
        Invoice.created_at >= prev_start_dt,
        Invoice.created_at < prev_end_dt
    ).scalar()
    prev_revenue = prev_revenue_query if prev_revenue_query else 0.0
    revenue_pct = calc_pct_change(current_revenue, prev_revenue)

    # 3. Vehicles in Bay (Status NOT Delivered) 
    vehicles_in_bay = JobCard.query.filter(JobCard.status != 'Delivered').count()

    # 4. Vehicles Serviced
    vehicles_serviced = JobCard.query.filter(
        JobCard.created_at >= start_dt,
        JobCard.created_at < end_dt
    ).count()
    prev_vehicles_serviced = JobCard.query.filter(
        JobCard.created_at >= prev_start_dt,
        JobCard.created_at < prev_end_dt
    ).count()
    vehicles_pct = calc_pct_change(vehicles_serviced, prev_vehicles_serviced)

    # Bay Occupancy (Assume total capacity is 20 for the gauge)
    capacity = 20
    bay_occupancy_pct = min(int((vehicles_in_bay / capacity) * 100), 100) if vehicles_in_bay > 0 else 0

    # 5. Recent 5 job cards
    recent_jobs = JobCard.query.options(
        joinedload(JobCard.customer),
        joinedload(JobCard.vehicle),
        joinedload(JobCard.mechanic)
    ).order_by(JobCard.created_at.desc()).limit(5).all()

    # 6. Low stock items
    low_stock_items = Inventory.query.filter(Inventory.quantity <= Inventory.reorder_level).all()

    # 7. Today's appointments
    today_str = today.strftime('%Y-%m-%d')
    today_appointments = Appointment.query.filter(Appointment.scheduled_at.like(f"{today_str}%")).all()

    # 8. Revenue last 7 days (Array for Chart.js)
    # Using tension 0.4 requires more data points to look good; we keep 7 days as requested but smooth it in UI
    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    revenue_data = []
    chart_labels = []
    
    for d in last_7_days:
        d_start = datetime.combine(d, datetime.min.time())
        d_end = d_start + timedelta(days=1)
        rev_q = db.session.query(func.sum(Invoice.total)).filter(
            Invoice.payment_status == 'Paid',
            Invoice.created_at >= d_start,
            Invoice.created_at < d_end
        ).scalar()
        revenue_data.append(rev_q if rev_q else 0.0)
        chart_labels.append(d.strftime('%a'))

    # Top 5 Customers by Revenue (Lifetime)
    top_customers = db.session.query(
        Customer, func.sum(Invoice.total).label('total_spent')
    ).join(JobCard, JobCard.customer_id == Customer.id)\
     .join(Invoice, Invoice.job_card_id == JobCard.id)\
     .filter(Invoice.payment_status == 'Paid')\
     .group_by(Customer.id)\
     .order_by(desc('total_spent'))\
     .limit(5).all()

    # Top 5 Vehicles by Service Frequency
    top_vehicles = db.session.query(
        Vehicle, func.count(JobCard.id).label('service_count')
    ).join(JobCard, JobCard.vehicle_id == Vehicle.id)\
     .group_by(Vehicle.id)\
     .order_by(desc('service_count'))\
     .limit(5).all()

    return render_template('dashboard.html',
                           timeframe=timeframe,
                           active_jobs=vehicles_in_bay,
                           
                           today_revenue=current_revenue,
                           revenue_pct=revenue_pct,
                           
                           month_vehicles=vehicles_serviced,
                           vehicles_pct=vehicles_pct,
                           
                           pending_jobs=pending_jobs,
                           pending_pct=pending_pct,
                           
                           recent_jobs=recent_jobs,
                           low_stock=low_stock_items,
                           appointments=today_appointments,
                           chart_labels=chart_labels,
                           revenue_data=revenue_data,
                           top_customers=top_customers,
                           top_vehicles=top_vehicles)
