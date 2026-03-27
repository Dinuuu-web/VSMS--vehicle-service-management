# pyre-ignore-all-errors[21, 16]
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()

# 1. User
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Mechanic') # Admin/Mechanic/Receptionist
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_attempts = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.DateTime, nullable=True)
    security_question = db.Column(db.String(200))
    security_answer_hash = db.Column(db.String(200))
    profile_photo = db.Column(db.String(200), nullable=True)
    theme_preference = db.Column(db.String(20), default='dark')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

# 2. Customer
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_visits = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    vehicles = db.relationship('Vehicle', backref='customer', lazy=True)

# 3. Vehicle
class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    vin = db.Column(db.String(30), unique=True, nullable=True)
    color = db.Column(db.String(30), nullable=True)
    mileage = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    job_cards = db.relationship('JobCard', backref='vehicle', lazy=True)

# 4. Service 
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    base_price = db.Column(db.Float, nullable=False, default=0.0)
    estimated_hours = db.Column(db.Float, nullable=False, default=1.0)
    category = db.Column(db.String(50), nullable=True)

# 5. JobCard
class JobCard(db.Model):
    __tablename__ = 'job_cards'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    mechanic_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Received')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    ai_diagnosis = db.Column(db.Text, nullable=True)
    qr_token = db.Column(db.String(36), unique=True, nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    
    job_services = db.relationship('JobService', backref='job_card', lazy=True, cascade="all, delete-orphan")
    job_parts = db.relationship('JobPart', backref='job_card', lazy=True, cascade="all, delete-orphan")
    invoice = db.relationship('Invoice', backref='job_card', uselist=False, lazy=True)
    customer = db.relationship('Customer', foreign_keys=[customer_id], backref='job_card_records')
    mechanic = db.relationship('User', foreign_keys=[mechanic_id], backref='assigned_jobs')

    def generate_qr_token(self):
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex

# 6. JobService
class JobService(db.Model):
    __tablename__ = 'job_services'
    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(db.Integer, db.ForeignKey('job_cards.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    
    service = db.relationship('Service') # to access service details easily

# 7. JobPart
class JobPart(db.Model):
    __tablename__ = 'job_parts'
    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(db.Integer, db.ForeignKey('job_cards.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity_used = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    
    part = db.relationship('Inventory', backref='job_parts')

# 8. Inventory
class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    part_name = db.Column(db.String(100), nullable=False)
    part_number = db.Column(db.String(100), unique=True, nullable=True)
    quantity = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    reorder_level = db.Column(db.Integer, default=5)
    supplier = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(50), nullable=True)

# 9. Invoice
class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(db.Integer, db.ForeignKey('job_cards.id'), unique=True, nullable=False)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_percent = db.Column(db.Float, nullable=False, default=18.0)
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(db.String(20), default='Pending') # Pending/Partial/Paid
    payment_method = db.Column(db.String(20), nullable=True) # Cash/UPI/Card/Credit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def grand_total(self):
        return (self.subtotal or 0) + (self.tax_amount or 0) - (self.discount or 0)

# 10. Appointment
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    service_type = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='Scheduled')
    notes = db.Column(db.Text, nullable=True)
    
    customer = db.relationship('Customer')
    vehicle = db.relationship('Vehicle')

# 11. AuditLog
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(50), nullable=True)
    record_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    
    user = db.relationship('User')

# 12. GarageSettings
class GarageSettings(db.Model):
    __tablename__ = 'garage_settings'
    id = db.Column(db.Integer, primary_key=True)
    garage_name = db.Column(db.String(100), default='Vehicle Service Management System')
    tagline = db.Column(db.String(200), default='Smart Service. Seamless Management.')
    address = db.Column(db.Text)
    gst_number = db.Column(db.String(20))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    logo_path = db.Column(db.String(200))
    theme = db.Column(db.String(20), default='dark')
    accent_color = db.Column(db.String(20), default='gold')
    tax_percent = db.Column(db.Float, default=18.0)
    currency_symbol = db.Column(db.String(5), default='₹')
    working_hours = db.Column(db.String(50), default='9AM - 7PM')
    total_bays = db.Column(db.Integer, default=6)

# 13. Notification
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    type = db.Column(db.String(20))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(200), nullable=True)

# 14. ServiceReminder
class ServiceReminder(db.Model):
    __tablename__ = 'service_reminders'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    reminder_type = db.Column(db.String(50))
    due_date = db.Column(db.DateTime)
    mileage_due = db.Column(db.Integer, nullable=True)
    is_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    vehicle = db.relationship('Vehicle')
    customer = db.relationship('Customer')

# 15. VehicleInspection
class VehicleInspection(db.Model):
    __tablename__ = 'vehicle_inspections'
    id = db.Column(db.Integer, primary_key=True)
    job_card_id = db.Column(db.Integer, db.ForeignKey('job_cards.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    engine_condition = db.Column(db.String(20))
    brake_condition = db.Column(db.String(20))
    tire_condition = db.Column(db.String(20))
    battery_condition = db.Column(db.String(20))
    ac_condition = db.Column(db.String(20))
    lights_condition = db.Column(db.String(20))
    body_condition = db.Column(db.String(20))
    overall_score = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    job_card = db.relationship('JobCard')
    vehicle = db.relationship('Vehicle')
    inspector = db.relationship('User')

# 16. ExpenseRecord
class ExpenseRecord(db.Model):
    __tablename__ = 'expense_records'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    receipt_path = db.Column(db.String(200), nullable=True)
    
    user = db.relationship('User')

# 17. MechanicAttendance
class MechanicAttendance(db.Model):
    __tablename__ = 'mechanic_attendance'
    id = db.Column(db.Integer, primary_key=True)
    mechanic_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime, nullable=True)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    hours_worked = db.Column(db.Float, nullable=True)
    notes = db.Column(db.String(200), nullable=True)
    
    mechanic = db.relationship('User')
