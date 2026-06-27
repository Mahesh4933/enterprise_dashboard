from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from db import db
from models import Customer, ActivityLog
from datetime import datetime

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

def log_activity(action, details):
    log = ActivityLog(user_id=current_user.id, action=action, details=details)
    db.session.add(log)
    db.session.commit()

@customers_bp.route('/')
@login_required
def index():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers.html', customers=customers)

@customers_bp.route('/add', methods=['POST'])
@login_required
def add():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    region = request.form.get('region')
    status = request.form.get('status', 'Active')
    
    if not name or not email:
        flash("Name and Email are required.", "danger")
        return redirect(url_for('customers.index'))
        
    cust_count = Customer.query.count()
    customer_code = f"C{cust_count + 1:03d}"
    
    cust = Customer(
        customer_code=customer_code,
        name=name,
        email=email,
        phone=phone,
        region=region,
        status=status,
        join_date=datetime.utcnow().date()
    )
    db.session.add(cust)
    db.session.commit()
    
    log_activity("Add Customer", f"Added customer {name} ({customer_code})")
    flash(f"Customer {name} added successfully!", "success")
    return redirect(url_for('customers.index'))

@customers_bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit(id):
    cust = Customer.query.get_or_404(id)
    cust.name = request.form.get('name')
    cust.email = request.form.get('email')
    cust.phone = request.form.get('phone')
    cust.region = request.form.get('region')
    cust.status = request.form.get('status', 'Active')
    
    db.session.commit()
    log_activity("Edit Customer", f"Updated customer details for {cust.name} ({cust.customer_code})")
    flash(f"Customer {cust.name} updated successfully!", "success")
    return redirect(url_for('customers.index'))

@customers_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    cust = Customer.query.get_or_404(id)
    name = cust.name
    code = cust.customer_code
    
    db.session.delete(cust)
    db.session.commit()
    
    log_activity("Delete Customer", f"Deleted customer {name} ({code})")
    flash(f"Customer {name} has been deleted.", "success")
    return redirect(url_for('customers.index'))
