# pyre-ignore-all-errors[21, 16]
from dotenv import load_dotenv  # type: ignore
load_dotenv()
import os

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting VSMS application...")

from flask import Flask, request, g, render_template
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from models import db, User
import jwt

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"]
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        f'sqlite:///{os.path.join(BASE_DIR, "garage.db")}'
    )
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key-2024')
    app.config['JWT_SECRET'] = os.getenv('JWT_SECRET', 'fallback-jwt-secret-2024')
    app.config['SESSION_TYPE'] = 'null' # Use flask default session

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        db.create_all()
        from auth import auth_bp, login_manager
        login_manager.init_app(app)

        # Register Blueprints gracefully
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        # Register blueprints gracefully
        blueprints = [
            ('routes.dashboard', 'dashboard_bp', '/dashboard'),
            ('routes.customers', 'customers_bp', '/customers'),
            ('routes.vehicles', 'vehicles_bp', '/vehicles'),
            ('routes.inventory', 'inventory_bp', '/inventory'),
            ('routes.appointments', 'appointments_bp', '/appointments'),
            ('routes.jobs', 'jobs_bp', '/jobs'),
            ('routes.public', 'public_bp', ''),
            ('routes.ai_assistant', 'ai_bp', '/api/ai'),
            ('routes.billing', 'billing_bp', '/billing'),
            ('routes.reports', 'reports_bp', '/reports'),
            ('routes.users', 'users_bp', '/users'),
            ('routes.settings', 'settings_bp', '/settings'),
            ('routes.inspections', 'inspections_bp', '/inspections'),
            ('routes.expenses', 'expenses_bp', '/expenses'),
            ('routes.attendance', 'attendance_bp', '/attendance'),
            ('routes.reminders', 'reminders_bp', '/reminders')
        ]
        
        for mod_name, bp_name, prefix in blueprints:
            try:
                mod = __import__(mod_name, fromlist=[bp_name])
                bp = getattr(mod, bp_name)
                app.register_blueprint(bp, url_prefix=prefix)
            except Exception as e:
                print(f"Import error: {e}")
                raise

        # JWT Middleware
        @app.before_request
        def check_jwt():
            # Log IP implicitly via access logs, could explicitly add to custom log
            g.user = None
            token = request.cookies.get('jwt_token')
            if token:
                try:
                    data = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
                    u = User.query.get(data['user_id'])
                    if u and u.is_active:
                        g.user = u
                except Exception:
                    pass

        from flask import jsonify  # type: ignore
        @app.route('/api/search')
        def search_api():
            from models import Customer, Vehicle, JobCard, Inventory  # type: ignore
            q = request.args.get('q', '')
            if not q: return jsonify({'customers': [], 'vehicles': [], 'jobs': [], 'inventory': []})
            
            term = f"%{q}%"
            c = Customer.query.filter(Customer.name.ilike(term) | Customer.phone.ilike(term)).limit(5).all()
            v = Vehicle.query.filter(Vehicle.license_plate.ilike(term) | Vehicle.make.ilike(term)).limit(5).all()
            j = JobCard.query.filter(JobCard.status.ilike(term)).limit(5).all()
            i = Inventory.query.filter(Inventory.part_name.ilike(term)).limit(5).all()
            
            return jsonify({
                'customers': [{'id': x.id, 'name': x.name, 'phone': x.phone} for x in c],
                'vehicles': [{'id': x.id, 'plate': x.license_plate, 'make': x.make} for x in v],
                'jobs': [{'id': x.id, 'status': x.status} for x in j],
                'inventory': [{'id': x.id, 'name': x.part_name, 'qty': x.quantity} for x in i]
            })

        @app.route('/api/notifications')
        def notifications_api():
            from models import Notification  # type: ignore
            if not getattr(g, 'user', None):
                return jsonify({'unread_count': 0, 'notifications': []})
                
            notifs = Notification.query.filter_by(user_id=g.user.id).order_by(Notification.created_at.desc()).limit(10).all()
            unread = sum(1 for n in notifs if not n.is_read)
            return jsonify({
                'unread_count': unread,
                'notifications': [{'id': n.id, 'title': n.title, 'message': n.message, 'type': n.type, 'is_read': n.is_read, 'time': n.created_at.strftime('%Y-%m-%d %H:%M')} for n in notifs]
            })

        @app.route('/api/notifications/<int:id>/read', methods=['POST'])
        def mark_notification_read(id):
            from models import Notification  # type: ignore
            n = Notification.query.get(id)
            if n:
                n.is_read = True
                db.session.commit()
            return jsonify({'success': True})

        @app.route('/api/notifications/read_all', methods=['POST'])
        def mark_all_notifications_read():
            from models import Notification  # type: ignore
            if getattr(g, 'user', None):
                Notification.query.filter_by(user_id=g.user.id, is_read=False).update({'is_read': True})
                db.session.commit()
            return jsonify({'success': True})

        @app.route('/api/notifications/clear_all', methods=['POST'])
        def clear_all_notifications():
            from models import Notification  # type: ignore
            if getattr(g, 'user', None):
                Notification.query.filter_by(user_id=g.user.id).delete()
                db.session.commit()
            return jsonify({'success': True})

        # Error Handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('404.html'), 404

        @app.errorhandler(403)
        def forbidden_error(error):
            return render_template('403.html'), 403

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            return render_template('500.html'), 500

        @app.route('/favicon.ico')
        def favicon():
            return '', 204

        @app.route('/')
        def index():
            from flask import redirect, url_for  # type: ignore
            return redirect(url_for('auth.login'))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
