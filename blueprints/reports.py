from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from db import db
from models import SalesOrder, Customer, Product, Finance, ActivityLog
import pandas as pd
import io
import os

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports.html')

@reports_bp.route('/export/<string:module>/<string:format>')
@login_required
def export_data(module, format):
    # Fetch data based on module
    data_list = []
    filename = f"{module}_export"
    
    if module == 'sales':
        records = SalesOrder.query.all()
        for r in records:
            data_list.append({
                'OrderCode': r.order_code,
                'Customer': r.customer.name,
                'OrderDate': r.order_date.strftime('%Y-%m-%d'),
                'Status': r.status,
                'TotalAmount': r.total_amount
            })
    elif module == 'customers':
        records = Customer.query.all()
        for r in records:
            data_list.append({
                'CustomerCode': r.customer_code,
                'Name': r.name,
                'Email': r.email,
                'Phone': r.phone,
                'Region': r.region,
                'Status': r.status,
                'JoinDate': r.join_date.strftime('%Y-%m-%d')
            })
    elif module == 'inventory':
        records = Product.query.all()
        for r in records:
            data_list.append({
                'SKU': r.sku,
                'Name': r.name,
                'Category': r.category,
                'StockLevel': r.stock_level,
                'ReorderPoint': r.reorder_point,
                'UnitPrice': r.unit_price,
                'CostPrice': r.cost_price,
                'Supplier': r.supplier.name if r.supplier else 'N/A'
            })
    elif module == 'finance':
        records = Finance.query.all()
        for r in records:
            data_list.append({
                'TransactionCode': r.transaction_code,
                'Date': r.date.strftime('%Y-%m-%d'),
                'Category': r.category,
                'Type': r.type,
                'Amount': r.amount,
                'Description': r.description
            })
    else:
        flash("Invalid export module selected.", "danger")
        return redirect(url_for('reports.index'))

    if not data_list:
        flash("No data available to export.", "warning")
        return redirect(url_for('reports.index'))
        
    df = pd.DataFrame(data_list)
    
    # Export formats
    if format == 'csv':
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{filename}.csv"
        )
    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=module.capitalize())
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{filename}.xlsx"
        )
    else:
        flash("Invalid export format selected.", "danger")
        return redirect(url_for('reports.index'))

@reports_bp.route('/import/<string:module>', methods=['POST'])
@login_required
def import_data(module):
    if 'file' not in request.files:
        flash("No file uploaded", "danger")
        return redirect(url_for('reports.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('reports.index'))
        
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
                
            imported_count = 0
            
            # Module-specific imports
            if module == 'customers':
                required = ['Name', 'Email', 'Phone', 'Region', 'Status']
                for col in required:
                    if col not in df.columns:
                        flash(f"Missing column '{col}' in imported file.", "danger")
                        return redirect(url_for('reports.index'))
                for _, row in df.iterrows():
                    cust_count = Customer.query.count()
                    c = Customer(
                        customer_code=f"C{cust_count + 1:03d}",
                        name=row['Name'],
                        email=row['Email'],
                        phone=str(row['Phone']),
                        region=row['Region'],
                        status=row['Status']
                    )
                    db.session.add(c)
                    imported_count += 1
                    
            elif module == 'inventory':
                required = ['SKU', 'Name', 'Category', 'StockLevel', 'ReorderPoint', 'UnitPrice', 'CostPrice']
                for col in required:
                    if col not in df.columns:
                        flash(f"Missing column '{col}' in imported file.", "danger")
                        return redirect(url_for('reports.index'))
                for _, row in df.iterrows():
                    p_count = Product.query.count()
                    p = Product(
                        product_code=f"P{p_count + 1:03d}",
                        sku=row['SKU'],
                        name=row['Name'],
                        category=row['Category'],
                        stock_level=int(row['StockLevel']),
                        reorder_point=int(row['ReorderPoint']),
                        unit_price=float(row['UnitPrice']),
                        cost_price=float(row['CostPrice'])
                    )
                    db.session.add(p)
                    imported_count += 1
            else:
                flash("Module import is not supported yet.", "warning")
                return redirect(url_for('reports.index'))
                
            db.session.commit()
            
            # Log
            log = ActivityLog(user_id=current_user.id, action="Import Data", details=f"Imported {imported_count} records to {module} via file upload.")
            db.session.add(log)
            db.session.commit()
            
            flash(f"Successfully imported {imported_count} records to {module}!", "success")
        except Exception as e:
            flash(f"Error during import: {str(e)}", "danger")
            
        return redirect(url_for('reports.index'))
        
    flash("Unsupported file type. Use CSV or Excel.", "danger")
    return redirect(url_for('reports.index'))
