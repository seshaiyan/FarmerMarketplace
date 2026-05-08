from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
    app.config['SECRET_KEY'] = 'secret_key_for_session'
    app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    
    from .models import User, Product, Offer, Transaction, Notification
    
    # Register Blueprints
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.farmer import farmer_bp
    from .routes.buyer import buyer_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(farmer_bp, url_prefix='/farmer')
    app.register_blueprint(buyer_bp, url_prefix='/buyer')
    
    with app.app_context():
        db.create_all()
        # Seed Admin
        if not User.query.filter_by(role='admin').first():
            admin = User(username='admin', password='admin123', role='admin', is_verified=True)
            db.session.add(admin)
            db.session.commit()
            
    return app
