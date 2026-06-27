from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import db
from models import Employee, User, ActivityLog
from blueprints.auth import role_required
from datetime import datetime

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')

def log_activity(action, details):
    log = ActivityLog(user_id=current_user.id, action=action, details=details)
    db.session.add(log)
    db.session.commit()

@employees_bp.route('/')
@login_required
@role_required(['admin', 'manager'])
def index():
    employees = Employee.query.all()
    # List users that do not have an employee profile yet
    users_without_profile = User.query.filter(~User.employee.has()).all()
    return render_template('employees.html', employees=employees, users_without_profile=users_without_profile)

@employees_bp.route('/add', methods=['POST'])
@login_required
@role_required(['admin'])
def add():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    department = request.form.get('department')
    salary = float(request.form.get('salary', 0.0))
    user_id = request.form.get('user_id')
    
    if not first_name or not last_name or not email or not department:
        flash("First Name, Last Name, Email, and Department are required.", "danger")
        return redirect(url_for('employees.index'))
        
    emp = Employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        department=department,
        salary=salary,
        user_id=int(user_id) if user_id else None,
        hire_date=datetime.utcnow().date(),
        status='Active'
    )
    db.session.add(emp)
    db.session.commit()
    
    log_activity("Add Employee", f"Added employee profile for {first_name} {last_name}")
    flash(f"Employee {first_name} {last_name} added successfully!", "success")
    return redirect(url_for('employees.index'))

@employees_bp.route('/edit/<int:id>', methods=['POST'])
@login_required
@role_required(['admin', 'manager'])
def edit(id):
    emp = Employee.query.get_or_404(id)
    emp.first_name = request.form.get('first_name')
    emp.last_name = request.form.get('last_name')
    emp.email = request.form.get('email')
    emp.phone = request.form.get('phone')
    emp.department = request.form.get('department')
    
    # Only Admin can update salary and status
    if current_user.role == 'admin':
        emp.salary = float(request.form.get('salary', 0.0))
        emp.status = request.form.get('status', 'Active')
        
    user_id = request.form.get('user_id')
    emp.user_id = int(user_id) if user_id else None
    
    db.session.commit()
    log_activity("Edit Employee", f"Updated employee profile for {emp.first_name} {emp.last_name}")
    flash(f"Employee {emp.first_name} {emp.last_name} updated successfully!", "success")
    return redirect(url_for('employees.index'))

@employees_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@role_required(['admin'])
def delete(id):
    emp = Employee.query.get_or_404(id)
    name = f"{emp.first_name} {emp.last_name}"
    db.session.delete(emp)
    db.session.commit()
    
    log_activity("Delete Employee", f"Deleted employee profile for {name}")
    flash(f"Employee {name} has been deleted.", "success")
    return redirect(url_for('employees.index'))
