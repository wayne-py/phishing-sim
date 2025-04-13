import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)
app.config['APP_CREATOR'] = "Wayne's Security Suite"
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Fix deprecated postgres URL scheme if needed
database_uri = os.environ.get("DATABASE_URL", "sqlite:///instance/phishing_sim.db")
if database_uri.startswith("postgres://"):
    database_uri = database_uri.replace("postgres://", "postgresql://", 1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set up email configuration
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() in ("true", "1", "t")
app.config["MAIL_USERNAME"] = os.environ.get("GMAIL_USER", "")
app.config["MAIL_PASSWORD"] = os.environ.get("GMAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("GMAIL_USER", "")

# Set up the application URL for tracking
app.config["APP_URL"] = os.environ.get("APP_URL", "http://localhost:5000")

# Initialize the database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add template context processor for date/time
@app.context_processor
def inject_now():
    import datetime
    return {'now': datetime.datetime.now()}

# Initialize the application context
with app.app_context():
    # Import models to ensure tables are created
    import models

    # Create tables only if they don't exist already
    db.create_all()

    # Import and register routes
    from routes import register_routes
    register_routes(app)
