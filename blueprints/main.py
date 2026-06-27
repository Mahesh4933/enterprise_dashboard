from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from db import db
from models import SalesOrder, SalesItem, Customer, Product, Finance, Notification, ActivityLog, Employee, User
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Calculate KPIs
    sales_orders = SalesOrder.query.filter_by(status='Completed').all()
    total_sales = sum(o.total_amount for o in sales_orders)
    
    customers_count = Customer.query.filter_by(status='Active').count()
    products_count = Product.query.count()
    
    # Financials
    finances = Finance.query.all()
    total_revenue = sum(f.amount for f in finances if f.type == 'Revenue')
    total_expense = sum(f.amount for f in finances if f.type == 'Expense')
    total_profit = total_revenue - total_expense
    
    # Low stock count
    low_stock_products = Product.query.filter(Product.stock_level <= Product.reorder_point).all()
    low_stock_count = len(low_stock_products)
    
    # Average Sale value
    avg_sale = total_sales / len(sales_orders) if sales_orders else 0.0
    
    # Top Product (using pandas)
    items_list = []
    sales_items = SalesItem.query.all()
    for item in sales_items:
        items_list.append({
            'product_name': item.product.name,
            'quantity': item.quantity,
            'total_price': item.total_price
        })
    
    top_product_name = "N/A"
    if items_list:
        df_items = pd.DataFrame(items_list)
        top_product_df = df_items.groupby('product_name')['quantity'].sum().reset_index()
        if not top_product_df.empty:
            top_product_name = top_product_df.sort_values(by='quantity', ascending=False).iloc[0]['product_name']

    # Top Customer (using pandas)
    orders_list = []
    for o in sales_orders:
        orders_list.append({
            'customer_name': o.customer.name,
            'amount': o.total_amount
        })
    top_customer_name = "N/A"
    if orders_list:
        df_orders = pd.DataFrame(orders_list)
        top_cust_df = df_orders.groupby('customer_name')['amount'].sum().reset_index()
        if not top_cust_df.empty:
            top_customer_name = top_cust_df.sort_values(by='amount', ascending=False).iloc[0]['customer_name']

    # Recent Sales Table (limit 5)
    recent_sales = SalesOrder.query.order_by(SalesOrder.order_date.desc()).limit(5).all()
    
    # Live Notifications
    user_notifications = Notification.query.filter(
        (Notification.role == None) | (Notification.role == current_user.role)
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_sales=total_sales,
        customers_count=customers_count,
        products_count=products_count,
        total_profit=total_profit,
        total_revenue=total_revenue,
        total_expense=total_expense,
        low_stock_count=low_stock_count,
        avg_sale=avg_sale,
        top_product=top_product_name,
        top_customer=top_customer_name,
        recent_sales=recent_sales,
        notifications=user_notifications
    )

@main_bp.route('/api/dashboard/charts')
@login_required
def charts_data():
    # 1. Monthly Sales Chart Data (Line Chart)
    sales = SalesOrder.query.filter_by(status='Completed').all()
    sales_data = [{'date': s.order_date.strftime('%Y-%m'), 'amount': s.total_amount} for s in sales]
    
    months_labels = []
    monthly_totals = []
    
    if sales_data:
        df = pd.DataFrame(sales_data)
        df_monthly = df.groupby('date')['amount'].sum().reset_index().sort_values('date')
        months_labels = df_monthly['date'].tolist()
        monthly_totals = df_monthly['amount'].tolist()

    # 2. Product Sales Data (Bar Chart)
    items = SalesItem.query.all()
    items_data = [{'product': i.product.name, 'revenue': i.total_price} for i in items]
    prod_labels = []
    prod_revenues = []
    
    if items_data:
        df_items = pd.DataFrame(items_data)
        df_prod = df_items.groupby('product')['revenue'].sum().reset_index().sort_values('revenue', ascending=False).head(5)
        prod_labels = df_prod['product'].tolist()
        prod_revenues = df_prod['revenue'].tolist()

    # 3. Category Share (Pie/Doughnut Chart)
    prod_categories = [{'category': i.product.category, 'quantity': i.quantity} for i in items]
    cat_labels = []
    cat_quantities = []
    
    if prod_categories:
        df_cat = pd.DataFrame(prod_categories)
        df_group = df_cat.groupby('category')['quantity'].sum().reset_index()
        cat_labels = df_group['category'].tolist()
        cat_quantities = df_group['quantity'].tolist()

    # 4. Inventory Alert Levels (Radar or PolarArea Chart)
    products = Product.query.all()
    inv_labels = [p.name for p in products[:6]]
    inv_stock = [p.stock_level for p in products[:6]]
    inv_reorder = [p.reorder_point for p in products[:6]]

    return jsonify({
        'monthlySales': {'labels': months_labels, 'data': monthly_totals},
        'productSales': {'labels': prod_labels, 'data': prod_revenues},
        'categoryShare': {'labels': cat_labels, 'data': cat_quantities},
        'inventoryAlerts': {'labels': inv_labels, 'stock': inv_stock, 'reorder': inv_reorder}
    })

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    emp = Employee.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not emp:
            emp = Employee(user_id=current_user.id)
            db.session.add(emp)
            
        emp.first_name = first_name
        emp.last_name = last_name
        emp.email = email
        emp.phone = phone
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
        
    return render_template('profile.html', employee=emp)

@main_bp.route('/settings')
@login_required
def settings():
    users = User.query.all()
    activity_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(20).all()
    return render_template('settings.html', users=users, activity_logs=activity_logs)

@main_bp.route('/api/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    notifs = Notification.query.filter(
        (Notification.role == None) | (Notification.role == current_user.role),
        Notification.is_read == False
    ).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return jsonify({'status': 'success'})
