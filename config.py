import os
from dotenv import load_dotenv
import pathlib

basedir = os.path.abspath(os.path.dirname(__file__))
# Fallback to .env if it exists
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'garage-super-secret-key-2024-xK9mP2nQ')
    JWT_SECRET = os.getenv('JWT_SECRET', 'garage-jwt-secret-2024-yR8nL3mW')
    
    # DB config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'garage.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session config
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_FILE_DIR = os.path.join(basedir, 'flask_session')
    
    # AI config
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    AI_RATE_LIMIT = os.environ.get('AI_RATE_LIMIT', '10/hour')
    AI_MODEL = os.environ.get('AI_MODEL', 'nvidia/nemotron-3-super-120b-a12b:free')
    # Directories
    QR_DIR = os.path.join(basedir, 'static', 'qrcodes')
    PDF_DIR = os.path.join(basedir, 'static', 'pdfs')
    
    @staticmethod
    def init_app(app):
        # Create required directories on startup
        pathlib.Path(Config.QR_DIR).mkdir(parents=True, exist_ok=True)
        pathlib.Path(Config.PDF_DIR).mkdir(parents=True, exist_ok=True)
        pathlib.Path(Config.SESSION_FILE_DIR).mkdir(parents=True, exist_ok=True)
