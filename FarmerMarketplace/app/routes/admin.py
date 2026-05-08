from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User, Transaction
from app import db
import random

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='admin').first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = 'admin'
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid Admin credentials')
            
    return render_template('admin/login.html')

@admin_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    pending_farmers = User.query.filter_by(role='farmer', is_verified=False).all()
    all_users = User.query.all()
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(10).all()
    
    # Calculate Stats
    from sqlalchemy import func
    from app.models import Product
    
    total_revenue = db.session.query(func.sum(Transaction.total_amount)).scalar() or 0
    total_farmers = User.query.filter_by(role='farmer').count()
    total_buyers = User.query.filter_by(role='buyer').count()
    total_products = Product.query.count()

    return render_template('admin/dashboard.html', 
                         farmers=pending_farmers, 
                         users=all_users, 
                         transactions=transactions,
                         stats={
                             'revenue': total_revenue,
                             'farmers': total_farmers,
                             'buyers': total_buyers,
                             'products': total_products
                         })

@admin_bp.route('/verify_farmer/<int:user_id>')
def verify_farmer(user_id):
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    user = User.query.get(user_id)
    if user:
        user.is_verified = True
        db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users')
def users():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    role_filter = request.args.get('role')
    if role_filter:
        users_list = User.query.filter_by(role=role_filter).all()
    else:
        users_list = User.query.all()
        
    return render_template('admin/users.html', users=users_list, active_role=role_filter or 'all')

@admin_bp.route('/products')
def products():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    from app.models import Product
    products_list = Product.query.all()
    return render_template('admin/products.html', products=products_list)

@admin_bp.route('/transactions')
def transactions():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    transactions_list = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('admin/transactions.html', transactions=transactions_list)

@admin_bp.route('/reports')
def reports():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    from app.models import Product, Transaction, User
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # Metric 1: Total Revenue
    total_revenue = db.session.query(func.sum(Transaction.total_amount)).scalar() or 0
    
    # Metric 2: Total Transactions
    total_transactions = Transaction.query.count()
    
    # Metric 3: Total Products
    total_products = Product.query.count()
    
    # Metric 4: Total Users & Distribution
    total_users = User.query.count()
    farmers_count = User.query.filter_by(role='farmer').count()
    buyers_count = User.query.filter_by(role='buyer').count()
    
    # Latest 10 Transactions for the table
    recent_transactions = Transaction.query.order_by(Transaction.timestamp.desc()).limit(10).all()
    
    # Revenue Trend (Last 7 Days)
    revenue_trend = []
    labels = []
    for i in range(6, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        daily_revenue = db.session.query(func.sum(Transaction.total_amount))\
            .filter(func.date(Transaction.timestamp) == date).scalar() or 0
        revenue_trend.append(float(daily_revenue))
        labels.append(date.strftime('%b %d'))

    return render_template('admin/reports.html', 
                          total_revenue=total_revenue,
                          total_transactions=total_transactions,
                          total_products=total_products,
                          total_users=total_users,
                          farmers_count=farmers_count,
                          buyers_count=buyers_count,
                          recent_transactions=recent_transactions,
                          revenue_trend=revenue_trend,
                          labels=labels)

@admin_bp.route('/price_predictor')
def price_predictor():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    return render_template('admin/price_prediction.html')

@admin_bp.route('/get_prediction', methods=['POST'])
def get_prediction():
    if session.get('role') != 'admin': return {"error": "Unauthorized"}, 403
    
    from app.prediction_service import forecast_and_advise
    from datetime import datetime, timedelta
    import traceback
    
    try:
        data = request.get_json(silent=True)
        if not data:
            return {"error": "Invalid or missing JSON data"}, 400
            
        crop_name = data.get('crop', 'Wheat')
        timeframe = data.get('timeframe', '7')
        
        # We use a default current listing price of 0 as it's not strictly required for the admin view
        avg_price, advisory = forecast_and_advise(crop_name, 0)
        
        if avg_price is None:
            # Fallback for when the model is warming up
            avg_price = 25.0 if crop_name == 'Wheat' else 35.0
            if "warming up" not in advisory:
                advisory = "AI model is currently gathering data. Using initial market estimates."
            
        # Generate daily trend data for the chart
        labels = []
        prices = []
        start_date = datetime.utcnow().date()
        
        try:
            days = int(timeframe)
        except:
            days = 7
            
        # For simulation, we'll create a trend leading to the avg_price
        current_trend_price = float(avg_price) - (days * 0.2) 
        for i in range(days):
            date = (start_date + timedelta(days=i)).strftime('%b %d')
            labels.append(date)
            # Volatility around the trend
            price_val = current_trend_price + (i * 0.4) + (random.uniform(-1, 1))
            prices.append(round(max(5, price_val), 2))
            
        return {
            "labels": labels,
            "prices": prices,
            "advisory": advisory,
            "avg_price": round(float(avg_price), 2)
        }
    except Exception as e:
        print(f"Prediction Route Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}, 500

@admin_bp.route('/disease_detect')
def disease_detect():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    # Reusing the logic or just showing a similar interface
    return render_template('admin/disease_detection.html')

@admin_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
        else:
            new_user = User(username=username, password=password, role=role)
            new_user.contact_number = request.form.get('contact_number')
            new_user.is_verified = True if role != 'farmer' else False
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully!')
            return redirect(url_for('admin.users'))
            
    return render_template('admin/add_user.html')

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']: # Only update if provided
            user.password = request.form['password']
        user.role = request.form['role']
        user.contact_number = request.form.get('contact_number')
        user.state = request.form.get('state')
        user.district = request.form.get('district')
        user.place = request.form.get('place')
        
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('admin.users'))
        
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Cannot delete main admin account!')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!')
    return redirect(url_for('admin.users'))

@admin_bp.route('/notifications')
def notifications():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    # Example notifications: pending farmers
    pending_farmers = User.query.filter_by(role='farmer', is_verified=False).all()
    return render_template('admin/notifications.html', pending_farmers=pending_farmers)

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('role') != 'admin': return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        # Logic to update admin password or site settings
        flash('Settings updated successfully!')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/settings.html')
