from db import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    
    # Relationships
    products = db.relationship('Product', back_populates='supplier')
    purchase_orders = db.relationship('PurchaseOrder', back_populates='supplier')

    def __repr__(self):
        return f"<Supplier {self.name}>"
