from db import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(20), unique=True, nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    stock_level = db.Column(db.Integer, nullable=False, default=0)
    reorder_point = db.Column(db.Integer, nullable=False, default=10)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    cost_price = db.Column(db.Float, nullable=False, default=0.0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    
    # Relationships
    supplier = db.relationship('Supplier', back_populates='products')
    sales_items = db.relationship('SalesItem', back_populates='product')
    purchase_items = db.relationship('PurchaseItem', back_populates='product')

    def __repr__(self):
        return f"<Product {self.name} - SKU: {self.sku}>"
