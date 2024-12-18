from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import os
from app.auth import init_oauth
from flask_cors import CORS



# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def register_extensions(app): 
    """Register Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)  # Add Flask-Migrate
    login_manager.init_app(app)
    init_oauth(app)

def register_blueprints(app):
    from app.routes import main
    from app.clubs.routes import club_management
    
    app.register_blueprint(main)
    app.register_blueprint(club_management, url_prefix='/clubs') 

def configure_login_manager(app):
    """Configure the Flask-Login extension."""
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))


def create_app(config_class=Config):
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)
    
    # Configure the app
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception as e:
        print(f"Error creating instance path: {e}")
    
    # Initialize extensions and register blueprints
    register_extensions(app)
    register_blueprints(app)
    configure_login_manager(app)
    
    # Set up error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return "Page not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "Internal server error", 500
        
    return app

# Import models after db initialization to avoid circular imports
from app.models import User, Student, Report