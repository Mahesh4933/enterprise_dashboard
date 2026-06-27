from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from db import db
from models import Product, Supplier, PurchaseOrder, PurchaseItem, Finance, ActivityLog, Notification
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

def log_activity(action, details):
    log = ActivityLog(user_id=current_user.id, action=action, details=details)
    db.session.add(log)
    db.session.commit()

@inventory_bp.route('/')
@login_required
def index():
    products = Product.query.order_by(Product.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    purchase_orders = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).all()
    return render_template(
        'inventory.html', 
        products=products, 
        suppliers=suppliers, 
        purchase_orders=purchase_orders
    )

# --- PRODUCTS CRUD ---
@inventory_bp.route('/product/add', methods=['POST'])
@login_required
def add_product():
    sku = request.form.get('sku')
    name = request.form.get('name')
    category = request.form.get('category')
    stock_level = int(request.form.get('stock_level', 0))
    reorder_point = int(request.form.get('reorder_point', 10))
    unit_price = float(request.form.get('unit_price', 0.0))
    cost_price = float(request.form.get('cost_price', 0.0))
    supplier_id = request.form.get('supplier_id')
    
    if not sku or not name:
        flash("SKU and Name are required.", "danger")
        return redirect(url_for('inventory.index'))
        
    # Generate unique product code
    p_count = Product.query.count()
    product_code = f"P{p_count + 1:03d}"
    
    p = Product(
        product_code=product_code,
        sku=sku,
        name=name,
        category=category,
        stock_level=stock_level,
        reorder_point=reorder_point,
        unit_price=unit_price,
        cost_price=cost_price,
        supplier_id=supplier_id if supplier_id else None
    )
    db.session.add(p)
    db.session.commit()
    
    log_activity("Add Product", f"Added product {name} ({sku})")
    flash(f"Product {name} added successfully!", "success")
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/product/edit/<int:id>', methods=['POST'])
@login_required
def edit_product(id):
    p = Product.query.get_or_404(id)
    p.sku = request.form.get('sku')
    p.name = request.form.get('name')
    p.category = request.form.get('category')
    p.stock_level = int(request.form.get('stock_level', 0))
    p.reorder_point = int(request.form.get('reorder_point', 10))
    p.unit_price = float(request.form.get('unit_price', 0.0))
    p.cost_price = float(request.form.get('cost_price', 0.0))
    supplier_id = request.form.get('supplier_id')
    p.supplier_id = supplier_id if supplier_id else None
    
    # Check for low stock notification
    if p.stock_level <= p.reorder_point:
        notif = Notification(
            title="Low Stock Alert",
            description=f"Product {p.name} ({p.sku}) is low on stock: {p.stock_level} remaining.",
            role="manager"
        )
        db.session.add(notif)
        
    db.session.commit()
    log_activity("Edit Product", f"Updated product details for {p.name} ({p.sku})")
    flash(f"Product {p.name} updated successfully!", "success")
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/product/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    p = Product.query.get_or_404(id)
    name = p.name
    sku = p.sku
    db.session.delete(p)
    db.session.commit()
    
    log_activity("Delete Product", f"Deleted product {name} ({sku})")
    flash(f"Product {name} has been deleted.", "success")
    return redirect(url_for('inventory.index'))

# --- SUPPLIERS CRUD ---
@inventory_bp.route('/supplier/add', methods=['POST'])
@login_required
def add_supplier():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    
    if not name or not email:
        flash("Supplier Name and Email are required.", "danger")
        return redirect(url_for('inventory.index'))
        
    sup_count = Supplier.query.count()
    supplier_code = f"SUP{sup_count + 1:03d}"
    
    s = Supplier(
        supplier_code=supplier_code,
        name=name,
        email=email,
        phone=phone,
        address=address
    )
    db.session.add(s)
    db.session.commit()
    
    log_activity("Add Supplier", f"Added supplier {name} ({supplier_code})")
    flash(f"Supplier {name} added successfully!", "success")
    return redirect(url_for('inventory.index'))

# --- PURCHASE ORDERS CRUD ---
@inventory_bp.route('/purchase/add', methods=['POST'])
@login_required
def add_purchase_order():
    supplier_id = request.form.get('supplier_id')
    product_ids = request.form.getlist('products[]')
    quantities = request.form.getlist('quantities[]')
    
    if not supplier_id or not product_ids:
        flash("Supplier and at least one product must be selected.", "danger")
        return redirect(url_for('inventory.index'))
        
    po_count = PurchaseOrder.query.count()
    po_code = f"PO{po_count + 1:03d}"
    
    po = PurchaseOrder(
        po_code=po_code,
        supplier_id=supplier_id,
        order_date=datetime.utcnow().date(),
        status='Pending',
        total_amount=0.0
    )
    db.session.add(po)
    db.session.flush()
    
    total_amount = 0.0
    for pid, qty in zip(product_ids, quantities):
        if not pid or not qty or int(qty) <= 0:
            continue
        prod = Product.query.get(pid)
        if not prod:
            continue
            
        qty = int(qty)
        cost_price = prod.cost_price
        item_total = qty * cost_price
        total_amount += item_total
        
        pi = PurchaseItem(
            purchase_order_id=po.id,
            product_id=prod.id,
            quantity=qty,
            cost_price=cost_price,
            total_price=item_total
        )
        db.session.add(pi)
        
    po.total_amount = total_amount
    db.session.commit()
    
    log_activity("Create Purchase Order", f"Created Purchase Order {po_code} with total cost ${total_amount:.2f}")
    flash(f"Purchase Order {po_code} created successfully!", "success")
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/purchase/receive/<int:id>', methods=['POST'])
@login_required
def receive_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    if po.status == 'Received':
        flash("Purchase Order is already marked as received.", "warning")
        return redirect(url_for('inventory.index'))
        
    po.status = 'Received'
    
    # Increase stock level for products
    for item in po.items:
        item.product.stock_level += item.quantity
        
    # Create finance expense entry
    fin_count = Finance.query.count()
    expense_log = Finance(
        transaction_code=f"T{fin_count + 1:03d}",
        date=datetime.utcnow().date(),
        category="Inventory Cost",
        type="Expense",
        amount=po.total_amount,
        description=f"Inventory procurement cost for PO {po.po_code}"
    )
    db.session.add(expense_log)
    
    db.session.commit()
    log_activity("Receive Purchase Order", f"Received inventory from PO {po.po_code}. Added ${po.total_amount:.2f} expense.")
    
    flash(f"Purchase Order {po.po_code} marked as Received. Inventory updated.", "success")
    return redirect(url_for('inventory.index'))
