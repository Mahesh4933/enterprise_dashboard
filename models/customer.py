from db import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    region = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default='Active')  # Active, Inactive
    join_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    
    # Relationships
    sales_orders = db.relationship('SalesOrder', back_populates='customer')

    def __repr__(self):
        return f"<Customer {self.name}>"
