import os
from flask import Flask
from config import Config
from db import db
from flask_login import LoginManager
from seed import seed_database
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize DB
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    from models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Context Processor for datetime
    @app.context_processor
    def inject_now():
        return {'datetime': datetime}
        
    # Register blueprints
    from blueprints import (
        auth_bp, main_bp, sales_bp, customers_bp, 
        inventory_bp, finance_bp, employees_bp, ml_bp, reports_bp
    )
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(reports_bp)
    
    # Auto-seed database if db doesn't exist
    db_path = os.path.join(app.root_path, 'database', 'dashboard.db')
    if not os.path.exists(db_path):
        print("Database not found. Initializing and seeding...")
        seed_database(app)
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
