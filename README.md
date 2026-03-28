<div align="center">

# 🚗 VSMS: Vehicle Service Management System
### *Smart Service. Seamless Management.*

A production-ready Vehicle Service Management System featuring a custom
**Glassmorphism UI**, role-based access control, AI diagnostics, 
job card pipeline, automated PDF invoicing, and real-time analytics.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)

</div>

---

## 👨‍💻 Developed By

| Developer | Role |
|-----------|------|
| **Dinbandhu Choudhary** | Full Stack Developer |
| **Aditya Hardas** | Full Stack Developer |

> 🎓 College Mini Project | Bharat College of Engineering, Badlapur | 2026

---

## ✨ Features

- 🔐 **Secure Authentication** — bcrypt hashing, JWT tokens, RBAC (Admin/Mechanic/Receptionist)
- 📊 **Interactive Dashboard** — real-time stats, animated SVG gauges, Chart.js analytics
- 📋 **Job Card Pipeline** — Kanban-style workflow (Received → Diagnosing → In Progress → Ready → Delivered)
- 📱 **QR Status Tracking** — customers scan QR to track their vehicle live
- 👥 **Customer & Vehicle Management** — full service history, vehicle health score
- 📦 **Inventory Management** — stock tracking, low stock alerts, auto-deduction
- 📅 **Appointment Scheduling** — calendar view, conflict detection
- 💰 **Billing & Invoicing** — GST-compliant PDF invoices, multiple payment modes
- 🤖 **AI Assistant** — Gemini-powered diagnosis, service suggestions, chatbot
- 📊 **Reports & Analytics** — revenue, mechanic performance, CSV export
- 🔍 **Vehicle Inspections** — 7-point checklist with health score
- 💸 **Expense Tracker** — garage expense management with P&L view
- 👥 **Mechanic Attendance** — check-in/check-out, hours tracking
- 🔔 **Smart Reminders** — service due alerts for customers
- 🎨 **5 Themes** — Dark, Light, Blue, Purple, Green (saved to localStorage)
- ⚙️ **Settings Panel** — garage profile, theme, notifications, account

---

## 💻 Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.11, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-WTF |
| **Database** | SQLite, SQLAlchemy ORM |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Jinja2, Chart.js |
| **Security** | bcrypt, PyJWT, CSRF Protection, Rate Limiting |
| **AI** | Google Gemini API (gemini-1.5-flash) |
| **PDF/QR** | ReportLab, qrcode, Pillow |
| **UI Style** | Glassmorphism, Neumorphism, CSS Animations |

---

## 🔐 Default Login Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `Admin@123` | Admin |
| `mechanic1` | `Mech@123` | Mechanic |
| `mechanic2` | `Mech2@123` | Mechanic |
| `receptionist1` | `Recep@123` | Receptionist |
| `manager1` | `Mgr@123` | Admin |

---

## 🚀 Installation (Windows)

**1. Clone the repository:**
```bash
git clone https://github.com/Dinuuu-web/VSMS--vehicle-service-management.git
cd VSMS--vehicle-service-management
```

**2. Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Setup .env file:**
```env
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
DATABASE_URL=sqlite:///garage.db
GEMINI_API_KEY=your-gemini-api-key
FLASK_ENV=development
```

**5. Initialize database:**
```bash
python init_db.py
```

**6. Run the application:**
```bash
python app.py
```

Open browser → `http://localhost:5000`

---

## 📂 Project Structure
```
VSMS/
├── app.py                 # Application entry point
├── auth.py                # Authentication & RBAC
├── config.py              # Configuration
├── models.py              # SQLAlchemy models
├── init_db.py             # Database + seed data
├── routes/
│   ├── dashboard.py
│   ├── customers.py
│   ├── vehicles.py
│   ├── jobs.py
│   ├── inventory.py
│   ├── appointments.py
│   ├── billing.py
│   ├── reports.py
│   ├── ai_assistant.py
│   ├── inspections.py
│   ├── expenses.py
│   ├── attendance.py
│   ├── reminders.py
│   └── settings.py
├── static/
│   ├── css/
│   ├── js/
│   └── qrcodes/
└── templates/
    ├── base.html
    ├── auth/
    ├── dashboard.html
    └── [all module templates]
```

---

## 🌐 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User authentication |
| GET | `/dashboard` | Main dashboard |
| GET/POST | `/jobs` | Job card management |
| GET | `/status/<token>` | Public QR status page |
| POST | `/ai/diagnose` | AI vehicle diagnosis |
| POST | `/ai/chat` | AI chatbot |
| GET | `/billing/<id>/pdf` | Download invoice PDF |
| GET | `/jobs/<id>/pdf` | Download job card PDF |
| GET | `/reports/revenue` | Revenue report |
| GET | `/api/search` | Global search |
| GET | `/api/notifications` | Notifications |

---

## 🖼️ Screenshots

> *Coming soon — Dashboard, Job Cards, Invoice, QR Status Page*

---

## 📜 License

MIT License © 2026 — Dinbandhu Choudhary & Aditya Hardas

---

<div align="center">
  <b>© 2026 VSMS | Developed by Dinbandhu Choudhary & Aditya Hardas</b><br/>
  <i>Bharat College of Engineering, Badlapur</i>
</div>
