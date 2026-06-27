from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from models.user import User
from models.activity import ActivityLog
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def log_activity(user_id, action, details=None):
    log = ActivityLog(user_id=user_id, action=action, details=details)
    db.session.add(log)
    db.session.commit()

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        log_activity(user.id, "Login", f"User {user.username} logged in successfully.")
        return redirect(url_for('main.dashboard'))
        
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Only allow registration if no users exist, or if an admin registers a new user
    user_count = User.query.count()
    is_first_user = (user_count == 0)
    
    if not is_first_user and (not current_user.is_authenticated or current_user.role != 'admin'):
        flash('Only Admin users can register new accounts.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'employee')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists.', 'danger')
            return redirect(url_for('auth.register'))
            
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password, method='scrypt'),
            role='admin' if is_first_user else role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        creator = current_user.username if current_user.is_authenticated else "System"
        log_activity(
            current_user.id if current_user.is_authenticated else new_user.id, 
            "User Registration", 
            f"User {username} ({new_user.role}) created by {creator}."
        )
        
        if is_first_user:
            flash('First administrator registered. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(f'User {username} registered successfully as {role}.', 'success')
            return redirect(url_for('main.settings'))
            
    return render_template('auth/register.html', is_first_user=is_first_user)

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, "Logout", f"User {current_user.username} logged out.")
    logout_user()
    return redirect(url_for('auth.login'))
