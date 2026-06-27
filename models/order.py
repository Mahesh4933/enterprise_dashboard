from db import db
from datetime import datetime

class SalesOrder(db.Model):
    __tablename__ = 'sales_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), nullable=False, default='Completed')  # Completed, Pending, Cancelled
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    
    # Relationships
    customer = db.relationship('Customer', back_populates='sales_orders')
    items = db.relationship('SalesItem', back_populates='sales_order', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<SalesOrder {self.order_code}>"


class SalesItem(db.Model):
    __tablename__ = 'sales_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    
    # Relationships
    sales_order = db.relationship('SalesOrder', back_populates='items')
    product = db.relationship('Product', back_populates='sales_items')


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    po_code = db.Column(db.String(20), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, Received, Cancelled
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    
    # Relationships
    supplier = db.relationship('Supplier', back_populates='purchase_orders')
    items = db.relationship('PurchaseItem', back_populates='purchase_order', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<PurchaseOrder {self.po_code}>"


class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    cost_price = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    
    # Relationships
    purchase_order = db.relationship('PurchaseOrder', back_populates='items')
    product = db.relationship('Product', back_populates='purchase_items')
