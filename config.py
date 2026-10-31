import os
from urllib.parse import urlparse

class Config:
    """
    Configuration for both local development (port 3307)
    and production cloud deployment (Render, Railway, Heroku, Aiven).
    """
    # Cloud connection string support (Railway, Render, Clever Cloud, etc.)
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or os.environ.get('CLEARDB_DATABASE_URL')
    if db_url and (db_url.startswith('mysql://') or db_url.startswith('mysql+pymysql://')):
        parsed = urlparse(db_url)
        MYSQL_HOST = parsed.hostname or '127.0.0.1'
        MYSQL_PORT = parsed.port or 3306
        MYSQL_USER = parsed.username or 'root'
        MYSQL_PASSWORD = parsed.password or ''
        MYSQL_DB = parsed.path.lstrip('/') or 'farmer_alert_db'
    else:
        # Local development / standard environment variables
        MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
        MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3307))
        MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
        MYSQL_DB = os.environ.get('MYSQL_DB', 'farmer_alert_db')

    # Application Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'farmer-alert-registry-secret-key-2026')
    
    # Auto-disable debug in production cloud containers
    is_cloud = bool(os.environ.get('RENDER') or os.environ.get('RAILWAY_STATIC_URL') or os.environ.get('DYNO'))
    DEBUG = False if is_cloud else os.environ.get('DEBUG', 'True').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))
