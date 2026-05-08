from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User, Product, Offer, Transaction, MarketPrice, Notification
from app import db
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from app.prediction_service import forecast_and_advise

farmer_bp = Blueprint('farmer', __name__)

@farmer_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='farmer').first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = 'farmer'
            return redirect(url_for('farmer.dashboard'))
        else:
            flash('Invalid Farmer credentials')
            
    return render_template('farmer/login.html')

@farmer_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    # Mock Data for Weather (could be replaced with real API later)
    weather = {
        'temp': '28°C',
        'condition': 'Sunny',
        'humidity': '65%',
        'wind_speed': '12 km/h',
        'precipitation': '10%',
        'location': 'Local Region'
    }
    
    user = User.query.get(session['user_id'])
    products = Product.query.filter_by(farmer_id=user.id).all()
    listed_crops = list(set(p.name for p in products))
    
    # 2. Dynamic Chart Data (Last 6 Months)
    from app.prediction_service import seed_historical_data
    from sqlalchemy import func
    
    # Calculate last 6 months labels
    months_labels = []
    datasets = []
    colors = ['#2ecc71', '#f1c40f', '#e74c3c', '#3498db', '#9b59b6', '#1abc9c']
    
    # We'll use the last 6 months including current
    for i in range(5, -1, -1):
        m_date = datetime.now() - timedelta(days=i*30)
        months_labels.append(m_date.strftime('%b'))
    
    for idx, crop in enumerate(listed_crops):
        seed_historical_data(crop) # Ensure data exists
        crop_data = []
        
        for i in range(5, -1, -1):
            start_date = datetime.now() - timedelta(days=(i+1)*30)
            end_date = datetime.now() - timedelta(days=i*30)
            
            avg_price = db.session.query(func.avg(MarketPrice.price)).filter(
                MarketPrice.crop_name == crop,
                MarketPrice.date >= start_date,
                MarketPrice.date <= end_date
            ).scalar()
            
            crop_data.append(round(avg_price, 2) if avg_price else 0)
        
        datasets.append({
            'label': f'{crop} (₹/kg)',
            'data': crop_data,
            'borderColor': colors[idx % len(colors)],
            'backgroundColor': f"{colors[idx % len(colors)]}1A", # 1A is ~10% opacity in hex
            'fill': True,
            'tension': 0.4
        })
    
    # If no crops, show a generic placeholder or empty chart
    if not datasets:
        chart_data = {'labels': months_labels, 'datasets': []}
    else:
        chart_data = {'labels': months_labels, 'datasets': datasets}
    
    schemes = [
        {'name': 'PM-KISAN', 'desc': 'Financial benefit of ₹6,000 per year.', 'link': 'https://pmkisan.gov.in/'},
        {'name': 'Pradhan Mantri Fasal Bima Yojana', 'desc': 'Crop insurance scheme.', 'link': 'https://pmfby.gov.in/'},
        {'name': 'Soil Health Card', 'desc': 'Nutrient management for soil.', 'link': 'https://soilhealth.dac.gov.in/'},
        {'name': 'e-NAM', 'desc': 'National Agriculture Market.', 'link': 'https://enam.gov.in/'},
        {'name': 'Kisan Credit Card (KCC)', 'desc': 'Affordable credit access.', 'link': 'https://pib.gov.in/PressReleasePage.aspx?PRID=1601614'}
    ]
    
    # Dynamic Stats
    now = datetime.now()
    transactions = Transaction.query.filter_by(farmer_id=user.id).all()
    earnings_month = sum(t.total_amount for t in transactions if t.timestamp.month == now.month and t.timestamp.year == now.year)
    
    active_listings = len(products)
    categories_count = len(listed_crops)
    
    # Fetch Notifications
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.timestamp.desc()).limit(10).all()
    
    return render_template('farmer/dashboard.html', 
                         weather=weather, 
                         prices=chart_data, 
                         schemes=schemes,
                         current_user_upi=user.upi_id,
                         earnings_month=earnings_month,
                         active_listings=active_listings,
                         categories_count=categories_count,
                         notifications=notifications)

@farmer_bp.route('/my_products')
def my_products():
    user = User.query.get(session['user_id'])
    my_products = Product.query.filter_by(farmer_id=user.id).all()
    return render_template('farmer/products.html', products=my_products, current_user_upi=user.upi_id)

@farmer_bp.route('/detect_disease', methods=['GET', 'POST'])
def detect_disease():
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    result = None
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file: # In a real app, verify allowed extensions here
            # Improved Mock AI Prediction Logic
            import random
            import time
            
            # Simulate processing time
            time.sleep(1.5)
            
            mock_outcomes = [
                {
                    'status': 'Healthy',
                    'disease': 'None',
                    'confidence': f'{random.randint(95, 99)}%',
                    'remedy': 'Great job! Your crop is healthy. Continue regular irrigation and monitoring.',
                    'color': '#27ae60'
                },
                {
                    'status': 'Infected',
                    'disease': 'Wheat Rust',
                    'confidence': f'{random.randint(85, 95)}%',
                    'remedy': 'Fungal infection detected. Apply fungicides like Propiconazole. Ensure proper spacing between plants to reduce humidity.',
                    'color': '#e74c3c'
                },
                {
                    'status': 'Infected',
                    'disease': 'Leaf Blight',
                    'confidence': f'{random.randint(88, 94)}%',
                    'remedy': 'Bacterial blight detected. Use copper-based bactericides. Avoid overhead irrigation to prevent spread.',
                    'color': '#c0392b'
                },
                {
                    'status': 'Infected',
                    'disease': 'Powdery Mildew',
                    'confidence': f'{random.randint(80, 90)}%',
                    'remedy': 'White powdery spots detected. Use sulfur-based fungicides and improve air circulation.',
                    'color': '#f39c12'
                }
            ]
            
            # Randomly pick an outcome (Weighted slightly towards healthy/common issues)
            result = random.choice(mock_outcomes)
            
    return render_template('farmer/disease_detection.html', result=result)

@farmer_bp.route('/offers')
def offers():
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    my_products = Product.query.filter_by(farmer_id=session['user_id']).all()
    product_ids = [p.id for p in my_products]
    offers_received = Offer.query.filter(Offer.product_id.in_(product_ids)).order_by(Offer.id.desc()).all()
    return render_template('farmer/offers.html', offers=offers_received)


@farmer_bp.route('/history')
def history():
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    transactions = Transaction.query.filter_by(farmer_id=session['user_id']).order_by(Transaction.timestamp.desc()).all()
    return render_template('farmer/history.html', transactions=transactions)


@farmer_bp.route('/analytics')
def analytics():
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    # Fetch all transactions to extract filter options and data
    all_transactions = Transaction.query.filter_by(farmer_id=session['user_id']).order_by(Transaction.timestamp).all()
    
    # 1. Extract Filter Options
    years = sorted(list(set(t.timestamp.year for t in all_transactions)), reverse=True)
    current_year = datetime.now().year
    
    # Unique Crops
    crops = sorted(list(set(t.product.name if t.product else "Deleted Product" for t in all_transactions)))
    
    # 2. Get Selected Filters
    sel_year = request.args.get('year', str(years[0]) if years else str(current_year))
    sel_month = request.args.get('month', 'all')
    sel_crop = request.args.get('crop', 'all')
    
    # 3. Apply Filters
    filtered_transactions = all_transactions
    
    if sel_year != 'all':
        filtered_transactions = [t for t in filtered_transactions if str(t.timestamp.year) == sel_year]
        
    if sel_month != 'all':
        filtered_transactions = [t for t in filtered_transactions if t.timestamp.strftime('%m') == sel_month]
        
    if sel_crop != 'all':
        filtered_transactions = [t for t in filtered_transactions if (t.product.name if t.product else "Deleted Product") == sel_crop]
        
    # 4. Aggregate Data & Determine Chart Type
    chart_data = {}
    chart_type = 'bar'
    total_income = 0
    
    for t in filtered_transactions:
        total_income += t.total_amount
        
    if sel_crop != 'all':
        # Specific Crop Selected -> Line Chart (Trend by Date)
        chart_type = 'line'
        for t in filtered_transactions:
            date_key = t.timestamp.strftime('%Y-%m-%d')
            chart_data[date_key] = chart_data.get(date_key, 0) + t.total_amount
    else:
        # All Crops -> Bar Chart (Comparison by Crop)
        chart_type = 'bar'
        for t in filtered_transactions:
            pkg = t.product.name if t.product else "Deleted Product"
            chart_data[pkg] = chart_data.get(pkg, 0) + t.total_amount
            
    return render_template('farmer/analytics.html', 
                         total_income=total_income,
                         sales_data=chart_data,
                         chart_type=chart_type,
                         years=years,
                         crops=crops,
                         sel_year=sel_year,
                         sel_month=sel_month,
                         sel_crop=sel_crop)

@farmer_bp.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    user = User.query.get(session['user_id'])
    if not user.is_verified: 
        flash("Your account is pending verification.")
        return redirect(url_for('farmer.dashboard'))

    if request.method == 'GET':
        return render_template('farmer/add_product.html', user=user)
    
    # POST Logic
    try:
        name = request.form['name']
        quantity = request.form['quantity']
        price = float(request.form['price'])
        condition = request.form['condition']
        state = request.form.get('state')
        district = request.form.get('district')
        place = request.form.get('place')
        image = request.files.get('image')

        if not all([state, district, place, image]):
            flash("All fields including location and image are mandatory")
            return redirect(url_for('farmer.add_product'))

        filename = secure_filename(image.filename)
        # Ensure upload dir exists
        upload_dir = os.path.join('app', 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        upload_path = os.path.join(upload_dir, filename)
        image.save(upload_path)
        image_url = url_for('static', filename='uploads/' + filename)
        
        new_product = Product(name=name, quantity=quantity, price=price, condition=condition,
                             location_state=state, location_district=district, location_place=place,
                             image_url=image_url, farmer_id=user.id)
        
        # Trigger Price Prediction & Advisory
        pred_price, advice = forecast_and_advise(name, price, farmer_id=user.id)
        new_product.predicted_price = pred_price
        new_product.advisory = advice
        
        # Update UPI if provided
        new_upi = request.form.get('upi_id')
        if new_upi:
            user.upi_id = new_upi
            
        db.session.add(new_product)
        db.session.commit()
        flash('Product listed successfully!')
        return redirect(url_for('farmer.my_products'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding product: {str(e)}')
        return redirect(url_for('farmer.add_product'))

@farmer_bp.route('/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if session.get('role') != 'farmer': return "Unauthorized", 403
    
    product = Product.query.get_or_404(product_id)
    if product.farmer_id != session['user_id']: return "Unauthorized", 403
    
    product.price = float(request.form['price'])
    product.quantity = int(request.form['quantity'])
    
    # Refresh Prediction on Price change
    pred_price, advice = forecast_and_advise(product.name, product.price, farmer_id=session['user_id'])
    product.predicted_price = pred_price
    product.advisory = advice
    
    # Update Farmer's UPI ID
    user = User.query.get(session['user_id'])
    new_upi = request.form.get('upi_id')
    if new_upi:
        user.upi_id = new_upi
    
    db.session.commit()
    flash('Product and UPI ID updated successfully!')
    return redirect(url_for('farmer.my_products'))

@farmer_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    product = Product.query.get_or_404(product_id)
    if product.farmer_id != session['user_id']: return "Unauthorized", 403
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting product. It may be linked to transaction history.')
        
    return redirect(url_for('farmer.my_products'))

@farmer_bp.route('/respond_offer/<int:offer_id>/<action>')
def respond_offer(offer_id, action):
    if session.get('role') != 'farmer': return "Unauthorized", 403
    
    offer = Offer.query.get_or_404(offer_id)
    if action == 'accept':
        offer.status = 'Accepted'
        # Transaction is NOT created here. Buyer must manually "Buy" the accepted offer.
        
    elif action == 'reject':
        offer.status = 'Rejected'
    
    db.session.commit()
    return redirect(url_for('farmer.dashboard'))

@farmer_bp.route('/update_upi', methods=['POST'])
def update_upi():
    if session.get('role') != 'farmer': return redirect(url_for('farmer.login'))
    
    upi_id = request.form.get('upi_id')
    user = User.query.get(session['user_id'])
    user.upi_id = upi_id
    db.session.commit()
    flash('UPI ID updated successfully!')
    return redirect(url_for('farmer.dashboard'))
