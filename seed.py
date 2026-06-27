import os
import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash
from db import db
from models import User, Employee, Customer, Supplier, Product, SalesOrder, SalesItem, Finance, Notification, ActivityLog

def seed_database(app):
    with app.app_context():
        # Ensure database directory exists
        db_dir = os.path.join(app.root_path, 'database')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        db.create_all()
        
        # 1. Seed Admin User if not exists
        if User.query.count() == 0:
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('adminpassword', method='scrypt'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            
            # Seed default employee profile for admin
            admin_emp = Employee(
                user_id=admin_user.id,
                first_name='System',
                last_name='Administrator',
                email='admin@enterprise.com',
                phone='+1-555-0000',
                department='IT & Administration',
                salary=120000.0,
                hire_date=datetime.utcnow().date(),
                status='Active'
            )
            db.session.add(admin_emp)
            
            # Seed a regular employee and manager too
            manager_user = User(
                username='manager',
                password_hash=generate_password_hash('managerpassword', method='scrypt'),
                role='manager'
            )
            db.session.add(manager_user)
            db.session.commit()
            
            manager_emp = Employee(
                user_id=manager_user.id,
                first_name='Jane',
                last_name='Doe',
                email='jane.doe@enterprise.com',
                phone='+1-555-0011',
                department='Sales & Marketing',
                salary=85000.0,
                hire_date=datetime.utcnow().date(),
                status='Active'
            )
            db.session.add(manager_emp)
            
            # Save logs
            db.session.add(ActivityLog(user_id=admin_user.id, action="Database Seed", details="Initialized users and default profiles."))
            db.session.commit()
            print("Users and employee profiles seeded.")
            
        # 2. Seed Suppliers
        if Supplier.query.count() == 0:
            suppliers_list = [
                Supplier(supplier_code='SUP001', name='Apex Electronics Inc', email='sales@apexelectronics.com', phone='+1-555-9001', address='123 Tech Blvd, Silicon Valley'),
                Supplier(supplier_code='SUP002', name='Accessories Corp Ltd', email='orders@accesscorp.com', phone='+1-555-9002', address='456 Logistics Way, Chicago'),
                Supplier(supplier_code='SUP003', name='Global Cable Distributor', email='info@globalcables.net', phone='+1-555-9003', address='789 Connection Dr, Boston')
            ]
            db.session.bulk_save_objects(suppliers_list)
            db.session.commit()
            print("Suppliers seeded.")

        # 3. Seed Products from inventory.csv
        if Product.query.count() == 0:
            csv_path = os.path.join(app.root_path, 'data', 'inventory.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    sup = Supplier.query.filter_by(supplier_code=row['SupplierID']).first()
                    p = Product(
                        product_code=row['ProductID'],
                        sku=row['SKU'],
                        name=row['Name'],
                        category=row['Category'],
                        stock_level=int(row['StockLevel']),
                        reorder_point=int(row['ReorderPoint']),
                        unit_price=float(row['UnitPrice']),
                        cost_price=float(row['CostPrice']),
                        supplier_id=sup.id if sup else None
                    )
                    db.session.add(p)
                db.session.commit()
                print("Products seeded from inventory.csv.")

        # 4. Seed Customers from customers.csv
        if Customer.query.count() == 0:
            csv_path = os.path.join(app.root_path, 'data', 'customers.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    c = Customer(
                        customer_code=row['CustomerID'],
                        name=row['Name'],
                        email=row['Email'],
                        phone=row['Phone'],
                        region=row['Region'],
                        status=row['Status'],
                        join_date=datetime.strptime(row['JoinDate'], '%Y-%m-%d').date()
                    )
                    db.session.add(c)
                db.session.commit()
                print("Customers seeded from customers.csv.")

        # 5. Seed Sales Orders from sales.csv
        if SalesOrder.query.count() == 0:
            csv_path = os.path.join(app.root_path, 'data', 'sales.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                # Group by SaleID (order_code)
                for order_code, group in df.groupby('SaleID'):
                    first_row = group.iloc[0]
                    cust = Customer.query.filter_by(customer_code=first_row['CustomerID']).first()
                    if not cust:
                        continue
                    
                    order_date = datetime.strptime(first_row['Date'], '%Y-%m-%d').date()
                    so = SalesOrder(
                        order_code=order_code,
                        customer_id=cust.id,
                        order_date=order_date,
                        status=first_row['Status'],
                        total_amount=float(group['TotalAmount'].sum())
                    )
                    db.session.add(so)
                    db.session.flush() # get ID
                    
                    for _, row in group.iterrows():
                        prod = Product.query.filter_by(product_code=row['ProductID']).first()
                        if not prod:
                            continue
                        item = SalesItem(
                            sales_order_id=so.id,
                            product_id=prod.id,
                            quantity=int(row['Quantity']),
                            unit_price=float(row['UnitPrice']),
                            total_price=float(row['Quantity']) * float(row['UnitPrice'])
                        )
                        db.session.add(item)
                db.session.commit()
                print("Sales Orders and Sales Items seeded from sales.csv.")

        # 6. Seed Finance records from finance.csv
        if Finance.query.count() == 0:
            csv_path = os.path.join(app.root_path, 'data', 'finance.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    f = Finance(
                        transaction_code=row['TransactionID'],
                        date=datetime.strptime(row['Date'], '%Y-%m-%d').date(),
                        category=row['Category'],
                        type=row['Type'],
                        amount=float(row['Amount']),
                        description=row['Description']
                    )
                    db.session.add(f)
                db.session.commit()
                print("Finance records seeded from finance.csv.")

        # 7. Seed Initial Notifications
        if Notification.query.count() == 0:
            notifs = [
                Notification(title="Low Stock Alert", description="Product SKU-MON-003 is below reorder point (8 items remaining).", role="manager"),
                Notification(title="New Customer Joined", description="Prime Enterprises has registered as an active customer.", role="employee"),
                Notification(title="System Update Completed", description="Database has been successfully configured and initialized with template datasets.", role="admin")
            ]
            db.session.bulk_save_objects(notifs)
            db.session.commit()
            print("Initial notifications seeded.")
