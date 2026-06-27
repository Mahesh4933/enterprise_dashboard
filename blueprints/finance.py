from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import db
from models import Finance, ActivityLog
from datetime import datetime

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

def log_activity(action, details):
    log = ActivityLog(user_id=current_user.id, action=action, details=details)
    db.session.add(log)
    db.session.commit()

@finance_bp.route('/')
@login_required
def index():
    records = Finance.query.order_by(Finance.date.desc()).all()
    # Calculate aggregates
    total_rev = sum(r.amount for r in records if r.type == 'Revenue')
    total_exp = sum(r.amount for r in records if r.type == 'Expense')
    net_profit = total_rev - total_exp
    
    return render_template(
        'finance.html', 
        records=records, 
        total_revenue=total_rev, 
        total_expense=total_exp, 
        net_profit=net_profit
    )

@finance_bp.route('/add', methods=['POST'])
@login_required
def add():
    date_str = request.form.get('date')
    category = request.form.get('category')
    type = request.form.get('type')
    amount = float(request.form.get('amount', 0.0))
    description = request.form.get('description')
    
    if not category or not type or amount <= 0:
        flash("Category, Type, and a positive Amount are required.", "danger")
        return redirect(url_for('finance.index'))
        
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    
    fin_count = Finance.query.count()
    transaction_code = f"T{fin_count + 1:03d}"
    
    record = Finance(
        transaction_code=transaction_code,
        date=date,
        category=category,
        type=type,
        amount=amount,
        description=description
    )
    db.session.add(record)
    db.session.commit()
    
    log_activity("Add Finance Record", f"Added financial transaction {transaction_code} of type {type} for ${amount:.2f}")
    flash(f"Finance transaction {transaction_code} added successfully!", "success")
    return redirect(url_for('finance.index'))

@finance_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    record = Finance.query.get_or_404(id)
    code = record.transaction_code
    db.session.delete(record)
    db.session.commit()
    
    log_activity("Delete Finance Record", f"Deleted financial transaction {code}")
    flash(f"Finance transaction {code} has been deleted.", "success")
    return redirect(url_for('finance.index'))
