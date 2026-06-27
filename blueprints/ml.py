from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from db import db
from models import SalesOrder, SalesItem, Product, ActivityLog
import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score

ml_bp = Blueprint('ml', __name__, url_prefix='/predictions')

MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'ml_models')
ML_MODEL_PATH = os.path.join(MODEL_DIR, 'sales_model.pkl')
DL_MODEL_PATH = os.path.join(MODEL_DIR, 'neural_net.pkl')

def ensure_model_dir():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

def get_training_data():
    items = SalesItem.query.all()
    if len(items) < 5:
        return None, None
        
    data = []
    for item in items:
        data.append({
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'category': item.product.category,
            'month': item.sales_order.order_date.month,
            'day': item.sales_order.order_date.day,
            'total_price': item.total_price
        })
        
    df = pd.DataFrame(data)
    
    # Simple data prep: encode category
    df = pd.get_dummies(df, columns=['category'], drop_first=True)
    
    # Target: total_price
    y = df['total_price']
    X = df.drop(columns=['total_price'])
    
    return X, y

@ml_bp.route('/')
@login_required
def index():
    # Check if models exist
    ml_exists = os.path.exists(ML_MODEL_PATH)
    dl_exists = os.path.exists(DL_MODEL_PATH)
    
    # Load model info if they exist
    ml_metrics = None
    dl_metrics = None
    
    if ml_exists:
        try:
            with open(ML_MODEL_PATH, 'rb') as f:
                saved_data = pickle.load(f)
                ml_metrics = saved_data.get('metrics')
        except Exception:
            ml_exists = False
            
    if dl_exists:
        try:
            with open(DL_MODEL_PATH, 'rb') as f:
                saved_data = pickle.load(f)
                dl_metrics = saved_data.get('metrics')
        except Exception:
            dl_exists = False
            
    # Sample products for manual prediction form
    products = Product.query.all()
    
    return render_template(
        'predictions.html',
        ml_exists=ml_exists,
        dl_exists=dl_exists,
        ml_metrics=ml_metrics,
        dl_metrics=dl_metrics,
        products=products
    )

@ml_bp.route('/train', methods=['POST'])
@login_required
def train():
    ensure_model_dir()
    X, y = get_training_data()
    
    if X is None or len(X) < 5:
        flash("Not enough historical sales data to train models. Need at least 5 sale line items.", "warning")
        return redirect(url_for('ml.index'))
        
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 1. Train ML Model (Linear Regression)
    ml_model = LinearRegression()
    ml_model.fit(X_train, y_train)
    ml_preds = ml_model.predict(X_test)
    ml_mse = mean_squared_error(y_test, ml_preds)
    ml_r2 = r2_score(y_test, ml_preds)
    
    # 2. Train DL Model (MLP Neural Network)
    # Using small hidden layers for speed and light resource usage
    dl_model = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=500, random_state=42)
    dl_model.fit(X_train, y_train)
    dl_preds = dl_model.predict(X_test)
    dl_mse = mean_squared_error(y_test, dl_preds)
    dl_r2 = r2_score(y_test, dl_preds)
    
    # Save feature names
    feature_names = X.columns.tolist()
    
    # Save ML model
    with open(ML_MODEL_PATH, 'wb') as f:
        pickle.dump({
            'model': ml_model,
            'features': feature_names,
            'metrics': {'mse': float(ml_mse), 'r2': float(ml_r2)}
        }, f)
        
    # Save DL model
    with open(DL_MODEL_PATH, 'wb') as f:
        pickle.dump({
            'model': dl_model,
            'features': feature_names,
            'metrics': {'mse': float(dl_mse), 'r2': float(dl_r2)}
        }, f)
        
    # Log Activity
    log = ActivityLog(user_id=current_user.id, action="Model Training", details=f"Trained ML & Neural Net models. ML R2: {ml_r2:.2f}, DL R2: {dl_r2:.2f}")
    db.session.add(log)
    db.session.commit()
    
    flash("Machine Learning and Deep Learning models trained and saved successfully!", "success")
    return redirect(url_for('ml.index'))

@ml_bp.route('/predict', methods=['POST'])
@login_required
def predict():
    model_type = request.form.get('model_type', 'ml')  # ml or dl
    product_id = request.form.get('product_id')
    quantity = float(request.form.get('quantity', 1))
    month = int(request.form.get('month', datetime.utcnow().month))
    
    prod = Product.query.get(product_id)
    if not prod:
        return jsonify({'error': 'Product not found'}), 400
        
    model_path = ML_MODEL_PATH if model_type == 'ml' else DL_MODEL_PATH
    if not os.path.exists(model_path):
        return jsonify({'error': 'Model has not been trained yet.'}), 400
        
    with open(model_path, 'rb') as f:
        saved_data = pickle.load(f)
        model = saved_data['model']
        feature_names = saved_data['features']
        
    # Create input vector matching the trained features
    input_dict = {feat: 0.0 for feat in feature_names}
    input_dict['quantity'] = quantity
    input_dict['unit_price'] = prod.unit_price
    input_dict['month'] = month
    input_dict['day'] = 15 # default middle of month
    
    # Handle category one-hot encoding
    cat_feature = f"category_{prod.category}"
    if cat_feature in input_dict:
        input_dict[cat_feature] = 1.0
        
    # Convert to DataFrame with correct order
    input_df = pd.DataFrame([input_dict])[feature_names]
    
    # Predict
    pred_val = model.predict(input_df)[0]
    pred_val = max(0.0, float(pred_val))  # prevent negative predictions
    
    return jsonify({
        'product': prod.name,
        'quantity': quantity,
        'unit_price': prod.unit_price,
        'prediction': round(pred_val, 2),
        'model_used': 'Linear Regression' if model_type == 'ml' else 'Multi-Layer Perceptron (Neural Net)'
    })

@ml_bp.route('/upload-predict', methods=['POST'])
@login_required
def upload_predict():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(url_for('ml.index'))
        
    file = request.files['file']
    model_type = request.form.get('model_type', 'ml')
    
    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(url_for('ml.index'))
        
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        try:
            # Read CSV or Excel
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
                
            # Verify columns
            required_cols = ['quantity', 'unit_price', 'category', 'month']
            for col in required_cols:
                if col not in df.columns:
                    flash(f"Uploaded file is missing required column: '{col}'", "danger")
                    return redirect(url_for('ml.index'))
            
            # Load model
            model_path = ML_MODEL_PATH if model_type == 'ml' else DL_MODEL_PATH
            if not os.path.exists(model_path):
                flash("Model is not trained. Please train the model first.", "warning")
                return redirect(url_for('ml.index'))
                
            with open(model_path, 'rb') as f:
                saved_data = pickle.load(f)
                model = saved_data['model']
                feature_names = saved_data['features']
                
            # Clean and prepare uploaded data
            predictions = []
            for _, row in df.iterrows():
                input_dict = {feat: 0.0 for feat in feature_names}
                input_dict['quantity'] = float(row['quantity'])
                input_dict['unit_price'] = float(row['unit_price'])
                input_dict['month'] = int(row['month'])
                input_dict['day'] = 15
                
                cat_feature = f"category_{row['category']}"
                if cat_feature in input_dict:
                    input_dict[cat_feature] = 1.0
                    
                input_df = pd.DataFrame([input_dict])[feature_names]
                pred_val = model.predict(input_df)[0]
                predictions.append(round(max(0.0, float(pred_val)), 2))
                
            df['PredictedTotalAmount'] = predictions
            
            # Convert results to HTML table
            results_html = df.to_html(classes="table table-hover table-striped mb-0", index=False)
            
            flash("Batch predictions processed successfully!", "success")
            return render_template(
                'predictions.html',
                ml_exists=os.path.exists(ML_MODEL_PATH),
                dl_exists=os.path.exists(DL_MODEL_PATH),
                batch_results=results_html,
                products=Product.query.all()
            )
            
        except Exception as e:
            flash(f"Error processing file: {str(e)}", "danger")
            return redirect(url_for('ml.index'))
            
    flash("Invalid file format. Upload CSV or Excel.", "danger")
    return redirect(url_for('ml.index'))
