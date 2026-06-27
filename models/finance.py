from db import db
from datetime import datetime

class Finance(db.Model):
    __tablename__ = 'finance'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_code = db.Column(db.String(20), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    category = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # Revenue, Expense
    amount = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f"<Finance {self.transaction_code} - {self.type}: {self.amount}>"
