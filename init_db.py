# pyre-ignore-all-errors[21, 16]
import os
from app import create_app
from models import (db, User, Customer, Vehicle, Service, Inventory, JobCard, 
                    JobService, JobPart, Invoice, Appointment, GarageSettings,
                    Notification, ServiceReminder, VehicleInspection, 
                    ExpenseRecord, MechanicAttendance)
import bcrypt
from datetime import datetime, timedelta
import random
import uuid

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    
    now = datetime.utcnow()

    # 1. Garage Settings
    gs = GarageSettings(
        garage_name="Vehicle Service Management System",
        tagline="Smart Service. Seamless Management.",
        address="Plot No. 42, Industrial Area, Nagpur, Maharashtra 440001",
        gst_number="27AABCU9603R1ZX",
        phone="9876543210",
        email="vsms.garage@email.com",
        total_bays=6
    )
    db.session.add(gs)

    # 2. Users (5 total)
    users_data = [
        {'username': 'admin', 'password': 'Admin@123', 'role': 'Admin', 'email': 'admin@vsms.com', 'sq': "What is your pet's name?", 'sa': 'tommy'},
        {'username': 'mechanic1', 'password': 'Mech@123', 'role': 'Mechanic', 'email': 'ravi@vsms.com', 'sq': "What is your mother's maiden name?", 'sa': 'sharma'},
        {'username': 'mechanic2', 'password': 'Mech2@123', 'role': 'Mechanic', 'email': 'suresh@vsms.com', 'sq': "What city were you born in?", 'sa': 'nagpur'},
        {'username': 'receptionist1', 'password': 'Recep@123', 'role': 'Receptionist', 'email': 'priya@vsms.com', 'sq': "What was your first school name?", 'sa': 'dav'},
        {'username': 'manager1', 'password': 'Mgr@123', 'role': 'Admin', 'email': 'amit@vsms.com', 'sq': "What is your favorite color?", 'sa': 'blue'}
    ]
    user_objs = {}
    for u in users_data:
        user = User(
            username=u['username'],
            email=u['email'],
            password_hash=hash_password(u['password']),
            role=u['role'],
            security_question=u['sq'],
            security_answer_hash=hash_password(u['sa'])
        )
        db.session.add(user)
        user_objs[u['username']] = user
    db.session.commit()

    # 3. Customers (12 total)
    customers_data = [
        ("Rajesh Kumar", "9876543210", "rajesh.kumar@gmail.com", "12 Gandhi Nagar, Nagpur"),
        ("Priya Sharma", "9988776655", "priya.sharma@gmail.com", "45 Wardha Road, Nagpur"),
        ("Amit Patel", "9123456789", "amit.patel@gmail.com", "78 Civil Lines, Nagpur"),
        ("Sunita Verma", "9234567890", "sunita.v@gmail.com", "23 Sadar, Nagpur"),
        ("Vikram Singh", "9345678901", "vikram.s@gmail.com", "56 Dharampeth, Nagpur"),
        ("Meera Joshi", "9456789012", "meera.j@gmail.com", "34 Sitabuldi, Nagpur"),
        ("Arjun Nair", "9567890123", "arjun.n@gmail.com", "89 Ramdaspeth, Nagpur"),
        ("Kavita Reddy", "9678901234", "kavita.r@gmail.com", "12 Bajaj Nagar, Nagpur"),
        ("Suresh Mehta", "9789012345", "suresh.m@gmail.com", "67 Pratap Nagar, Nagpur"),
        ("Anita Gupta", "9890123456", "anita.g@gmail.com", "45 Manish Nagar, Nagpur"),
        ("Rohit Desai", "9012345678", "rohit.d@gmail.com", "23 Trimurti Nagar, Nagpur"),
        ("Pooja Iyer", "9111222333", "pooja.i@gmail.com", "78 Laxmi Nagar, Nagpur")
    ]
    cust_objs = []
    for c in customers_data:
        cust = Customer(name=c[0], phone=c[1], email=c[2], address=c[3], total_visits=random.randint(1,5))
        db.session.add(cust)
        cust_objs.append(cust)
    db.session.commit()

    # 4. Vehicles (16 total)
    vehicles_data = [
        (0, "Maruti", "Swift", 2019, "MH31AB1234", "White"),
        (0, "Honda", "Activa", 2021, "MH31AB5678", "Black"),
        (1, "Honda", "City", 2021, "MH31CD5678", "Silver"),
        (2, "Hyundai", "Creta", 2020, "MH31EF9012", "Red"),
        (3, "Toyota", "Fortuner", 2022, "MH31GH3456", "White"),
        (4, "Tata", "Nexon", 2021, "MH31IJ7890", "Blue"),
        (5, "Mahindra", "XUV700", 2022, "MH31KL2345", "Black"),
        (6, "Kia", "Seltos", 2020, "MH31MN6789", "Grey"),
        (7, "Maruti", "Baleno", 2019, "MH31OP1234", "Gold"),
        (8, "Hyundai", "i20", 2021, "MH31QR5678", "Orange"),
        (9, "Tata", "Tiago", 2020, "MH31ST9012", "Blue"),
        (10, "Volkswagen", "Polo", 2018, "MH31UV3456", "White"),
        (11, "Renault", "Duster", 2019, "MH31WX7890", "Brown"),
        (4, "Ford", "EcoSport", 2020, "MH31YZ2345", "Grey"),
        (8, "Maruti", "Ertiga", 2022, "MH31AA6789", "Silver"),
        (2, "Royal Enfield", "Classic", 2021, "MH31BB1234", "Black")
    ]
    veh_objs = []
    for v in vehicles_data:
        veh = Vehicle(customer_id=cust_objs[v[0]].id, make=v[1], model=v[2], year=v[3], license_plate=v[4], color=v[5], mileage=random.randint(10000, 80000))
        db.session.add(veh)
        veh_objs.append(veh)
    db.session.commit()

    # 5. Services (15 total)
    services_data = [
        ("Oil Change", 800, 1, "Routine"),
        ("Brake Service", 2500, 2, "Safety"),
        ("AC Service", 3500, 3, "Comfort"),
        ("Engine Tune-up", 5000, 4, "Engine"),
        ("Tire Rotation", 500, 0.5, "Routine"),
        ("Battery Replacement", 4000, 1, "Electrical"),
        ("Wheel Alignment", 800, 1, "Routine"),
        ("Suspension Check", 1500, 2, "Safety"),
        ("Full Service Package", 8000, 6, "Package"),
        ("Radiator Flush", 2000, 2, "Engine"),
        ("Clutch Repair", 6000, 5, "Transmission"),
        ("Denting & Painting", 15000, 8, "Body"),
        ("Windshield Repair", 3000, 2, "Body"),
        ("Engine Overhaul", 25000, 16, "Engine"),
        ("Transmission Service", 8000, 5, "Transmission")
    ]
    srv_objs = []
    for s in services_data:
        srv = Service(name=s[0], base_price=s[1], estimated_hours=s[2], category=s[3])
        db.session.add(srv)
        srv_objs.append(srv)
    db.session.commit()

    # 6. Inventory (20 items)
    inventory_data = [
        ("Engine Oil 5W-30", 50, 450, 10, "Castrol India"),
        ("Oil Filter", 30, 150, 5, "Bosch India"),
        ("Air Filter", 25, 350, 5, "K&N Filters"),
        ("Brake Pads Front", 20, 1200, 4, "Brembo India"),
        ("Brake Pads Rear", 20, 1000, 4, "Brembo India"),
        ("AC Refrigerant R134a", 15, 800, 3, "Honeywell"),
        ("Spark Plugs Set", 40, 600, 8, "NGK India"),
        ("Coolant 1L", 35, 250, 7, "Gulf Oil"),
        ("Wiper Blades", 25, 400, 5, "Bosch India"),
        ("Brake Fluid", 20, 300, 4, "Castrol India"),
        ("Power Steering Fluid", 15, 350, 3, "Gulf Oil"),
        ("Transmission Fluid", 12, 550, 3, "Castrol India"),
        ("Battery 12V 55Ah", 8, 3500, 2, "Exide India"),
        ("Fuel Filter", 18, 450, 4, "Bosch India"),
        ("Serpentine Belt", 10, 850, 2, "Gates India"),
        ("Timing Belt", 8, 1200, 2, "Gates India"),
        ("Radiator Cap", 15, 200, 3, "Tata AutoComp"),
        ("Thermostat", 10, 400, 2, "Tata AutoComp"),
        ("Clutch Plate", 6, 2800, 2, "LUK India"),
        ("Shock Absorber Front", 3, 3200, 2, "Monroe India")
    ]
    inv_objs = []
    for i, item in enumerate(inventory_data):
        inv = Inventory(part_name=item[0], part_number=f"PART-{i+100}", quantity=item[1], unit_price=item[2], reorder_level=item[3], supplier=item[4], category="General")
        db.session.add(inv)
        inv_objs.append(inv)
    db.session.commit()

    # 7. Job Cards (18 total)
    jc_statuses = ['Delivered']*5 + ['Ready']*3 + ['In Progress']*4 + ['Quality Check']*2 + ['Diagnosing']*2 + ['Received']*2
    job_cards = []
    mechanics = [user_objs['mechanic1'], user_objs['mechanic2']]
    
    for i, st in enumerate(jc_statuses):
        veh = veh_objs[i % len(veh_objs)]
        mech = random.choice(mechanics) if st not in ['Received'] else None
        dt = now - timedelta(days=random.randint(0, 30) if st == 'Delivered' else random.randint(0, 5))
        
        jc = JobCard(
            vehicle_id=veh.id,  # type: ignore
            customer_id=veh.customer_id,  # type: ignore
            mechanic_id=mech.id if mech else None,
            status=st,
            created_at=dt,
            completed_at=dt + timedelta(days=2) if st == 'Delivered' else None,
            qr_token=uuid.uuid4().hex,
            notes=f"Customer reported issues. Assigned for {st}."
        )
        db.session.add(jc)
        job_cards.append(jc)
    db.session.commit()

    # Job Services & Parts & Invoices
    for jc in job_cards:
        # Add 1-2 services
        js_list = []
        jp_list = []
        subtotal = 0
        for _ in range(random.randint(1, 2)):
            srv = random.choice(srv_objs)
            js = JobService(job_card_id=jc.id, service_id=srv.id, quantity=1, price=srv.base_price, status='Completed' if jc.status in ['Delivered', 'Ready'] else 'Pending')
            js_list.append(js)
            subtotal += srv.base_price
            
        for _ in range(random.randint(1, 2)):
            inv = random.choice(inv_objs)
            jp = JobPart(job_card_id=jc.id, inventory_id=inv.id, quantity_used=1, unit_price=inv.unit_price)
            jp_list.append(jp)
            subtotal += inv.unit_price
            
        db.session.add_all(js_list + jp_list)
        jc.total_amount = subtotal + (subtotal * 0.18)
        
        # Invoices for Delivered and Ready jobs
        if jc.status in ['Delivered', 'Ready']:
            inv_stat = 'Paid' if jc.status == 'Delivered' else 'Pending'
            inv_meth = random.choice(['Cash', 'UPI', 'Card']) if inv_stat == 'Paid' else None
            invoice = Invoice(
                job_card_id=jc.id,
                subtotal=subtotal,
                tax_percent=18.0,
                tax_amount=subtotal*0.18,
                total=jc.total_amount,
                payment_status=inv_stat,
                payment_method=inv_meth,
                created_at=jc.completed_at or now
            )
            db.session.add(invoice)
            
    db.session.commit()

    # 8. Appointments (12 total)
    appt_specs = [
        (3, 'Scheduled'), (4, 'Scheduled'), (5, 'Scheduled'), (6, 'Scheduled'), # upcoming
        (0, 'Scheduled'), (0, 'Scheduled'), (0, 'Scheduled'), # today
        (-5, 'Completed'), (-7, 'Completed'), (-8, 'Completed'), # completed
        (2, 'Cancelled'), (-2, 'Cancelled') # cancelled
    ]
    for d, st in appt_specs:
        v = random.choice(veh_objs)
        dt = now + timedelta(days=d)
        appt = Appointment(customer_id=v.customer_id, vehicle_id=v.id, scheduled_at=dt, service_type="General Checkup", status=st)  # type: ignore
        db.session.add(appt)
    db.session.commit()

    # 9. Expense Records (10 total)
    expenses = [
        ("Utilities", "Electricity Bill", 8500),
        ("Tools", "Tool Purchase (Torque Wrench)", 3200),
        ("Rent", "Shop Rent", 25000),
        ("Supplies", "Cleaning Supplies", 1200),
        ("Supplies", "Uniform Purchase", 4500),
        ("Utilities", "Internet Bill", 999),
        ("Utilities", "Water Bill", 650),
        ("Tools", "Safety Equipment", 8000),
        ("Office", "Printer Ink", 800),
        ("Supplies", "First Aid Kit", 1500)
    ]
    for e in expenses:
        exp = ExpenseRecord(category=e[0], description=e[1], amount=e[2], date=now - timedelta(days=random.randint(1,20)), added_by=user_objs['admin'].id)  # type: ignore
        db.session.add(exp)
    db.session.commit()

    # 10. Mechanic Attendance (30 days)
    for m in [user_objs['mechanic1'], user_objs['mechanic2']]:
        for i in range(30):
            dt_date = now.date() - timedelta(days=i)
            # Skip some Sundays
            if dt_date.weekday() == 6 and random.choice([True, False]):
                continue
            
            check_in = datetime.combine(dt_date, datetime.min.time()) + timedelta(hours=9, minutes=random.randint(0,30))
            check_out = check_in + timedelta(hours=8, minutes=random.randint(0,60))
            hours = (check_out - check_in).total_seconds() / 3600.0
            
            att = MechanicAttendance(mechanic_id=m.id, check_in=check_in, check_out=check_out, date=dt_date, hours_worked=hours)  # type: ignore
            db.session.add(att)
    db.session.commit()

    # 11. Notifications (8 sample)
    notifs = [
        ("Low stock: Shock Absorber Front (3 remaining)", "Low Stock", True),
        ("Job #15 marked as Ready for Pickup", "Job Update", False),
        ("New appointment booked for tomorrow", "Appointment", False),
        ("Invoice #8 payment received", "Payment", True),
        ("Battery 12V stock running low", "Low Stock", False),
        ("Customer Rajesh updated profile", "System", True),
        ("Mechanic 2 clocked in late", "Attendance", False),
        ("Daily revenue report generated", "Report", True)
    ]
    for n in notifs:
        db.session.add(Notification(user_id=user_objs['admin'].id, title=n[1], message=n[0], type=n[1], is_read=n[2], created_at=now - timedelta(hours=random.randint(1,48))))  # type: ignore
    db.session.commit()

    # 12. Service Reminders (5 sample)
    rems = [
        ("Rajesh's Swift", "Oil Change due in 2 weeks"),
        ("Priya's City", "Full Service due next month"),
        ("Amit's Creta", "Brake check overdue"),
        ("Sunita's Fortuner", "AC Service suggested"),
        ("Vikram's Nexon", "Tire Rotation due")
    ]
    for i, r in enumerate(rems):
        v = veh_objs[i]
        db.session.add(ServiceReminder(vehicle_id=v.id, customer_id=v.customer_id, reminder_type="Maintenance", notes=r[1], due_date=now + timedelta(days=random.randint(-10, 30))))  # type: ignore
    db.session.commit()

    print("✅ All data seeded explicitly as requested!")
