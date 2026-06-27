from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from db import db
from models import SalesOrder, SalesItem, Customer, Product, Finance, ActivityLog
from datetime import datetime

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

def log_activity(action, details):
    log = ActivityLog(user_id=current_user.id, action=action, details=details)
    db.session.add(log)
    db.session.commit()

@sales_bp.route('/')
@login_required
def index():
    orders = SalesOrder.query.order_by(SalesOrder.order_date.desc()).all()
    customers = Customer.query.filter_by(status='Active').all()
    products = Product.query.all()
    return render_template('sales.html', orders=orders, customers=customers, products=products)

@sales_bp.route('/add', methods=['POST'])
@login_required
def add():
    customer_id = request.form.get('customer_id')
    order_date_str = request.form.get('order_date')
    status = request.form.get('status', 'Completed')
    
    # Selected products and quantities
    product_ids = request.form.getlist('products[]')
    quantities = request.form.getlist('quantities[]')
    
    if not customer_id or not product_ids:
        flash("Customer and at least one product must be selected.", "danger")
        return redirect(url_for('sales.index'))
        
    order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date() if order_date_str else datetime.utcnow().date()
    
    # Generate unique order code
    order_count = SalesOrder.query.count()
    order_code = f"SO{order_count + 1:03d}"
    
    # Create order
    so = SalesOrder(
        order_code=order_code,
        customer_id=customer_id,
        order_date=order_date,
        status=status,
        total_amount=0.0
    )
    db.session.add(so)
    db.session.flush() # flush to get so.id
    
    total_amount = 0.0
    for pid, qty in zip(product_ids, quantities):
        if not pid or not qty or int(qty) <= 0:
            continue
        
        prod = Product.query.get(pid)
        if not prod:
            continue
            
        qty = int(qty)
        # Deduct inventory if completed
        if status == 'Completed':
            prod.stock_level = max(0, prod.stock_level - qty)
            
        unit_price = prod.unit_price
        total_price = qty * unit_price
        total_amount += total_price
        
        item = SalesItem(
            sales_order_id=so.id,
            product_id=prod.id,
            quantity=qty,
            unit_price=unit_price,
            total_price=total_price
        )
        db.session.add(item)
        
    so.total_amount = total_amount
    
    # If completed, add to finance logs as revenue
    if status == 'Completed' and total_amount > 0:
        fin_count = Finance.query.count()
        finance_log = Finance(
            transaction_code=f"T{fin_count + 1:03d}",
            date=order_date,
            category="Sales Revenue",
            type="Revenue",
            amount=total_amount,
            description=f"Revenue generated from invoice {order_code}"
        )
        db.session.add(finance_log)
        
    db.session.commit()
    log_activity("Create Sales Order", f"Created order {order_code} with total amount ${total_amount:.2f}")
    
    flash(f"Sales Order {order_code} created successfully!", "success")
    return redirect(url_for('sales.index'))

@sales_bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit(id):
    so = SalesOrder.query.get_or_4_4_or_cancel = SalesOrder.query.get_or_404(id)
    old_status = so.status
    new_status = request.form.get('status')
    
    so.status = new_status
    
    # If moving to Completed, check and adjust stock if not adjusted before
    if old_status != 'Completed' and new_status == 'Completed':
        for item in so.items:
            item.product.stock_level = max(0, item.product.stock_level - item.quantity)
            
        # Add to finance logs
        fin_count = Finance.query.count()
        finance_log = Finance(
            transaction_code=f"T{fin_count + 1:03d}",
            date=datetime.utcnow().date(),
            category="Sales Revenue",
            type="Revenue",
            amount=so.total_amount,
            description=f"Revenue generated from completed invoice {so.order_code}"
        )
        db.session.add(finance_log)
        
    db.session.commit()
    log_activity("Edit Sales Order", f"Updated status of order {so.order_code} from {old_status} to {new_status}")
    flash(f"Sales Order {so.order_code} updated successfully!", "success")
    return redirect(url_for('sales.index'))

@sales_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    so = SalesOrder.query.get_or_404(id)
    order_code = so.order_code
    
    # Return stock if it was completed
    if so.status == 'Completed':
        for item in so.items:
            item.product.stock_level += item.quantity
            
    db.session.delete(so)
    db.session.commit()
    log_activity("Delete Sales Order", f"Deleted sales order {order_code}")
    
    flash(f"Sales Order {order_code} has been deleted.", "success")
    return redirect(url_for('sales.index'))

@sales_bp.route('/api/order-details/<int:id>')
@login_required
def details(id):
    so = SalesOrder.query.get_or_404(id)
    items = []
    for item in so.items:
        items.append({
            'product_name': item.product.name,
            'sku': item.product.sku,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.total_price
        })
    return jsonify({
        'order_code': so.order_code,
        'customer_name': so.customer.name,
        'order_date': so.order_date.strftime('%Y-%m-%d'),
        'status': so.status,
        'total_amount': so.total_amount,
        'items': items
    })
