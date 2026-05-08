from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models import User, Product, Offer, Transaction
from app import db
from datetime import datetime

buyer_bp = Blueprint('buyer', __name__)

@buyer_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, role='buyer').first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = 'buyer'
            return redirect(url_for('buyer.dashboard'))
        else:
            flash('Invalid Buyer credentials')
            
    return render_template('buyer/login.html')

@buyer_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'buyer': return redirect(url_for('buyer.login'))
    
    buyer_id = session['user_id']
    
    # Calculate Metrics
    transactions = Transaction.query.filter_by(buyer_id=buyer_id).all()
    total_spent = sum(t.total_amount for t in transactions)
    order_count = len(transactions)
    
    pending_offers = Offer.query.filter_by(buyer_id=buyer_id, status='Pending').count()
    
    recent_transactions = Transaction.query.filter_by(buyer_id=buyer_id).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    return render_template('buyer/dashboard.html', 
                         total_spent=total_spent,
                         order_count=order_count,
                         pending_offers=pending_offers,
                         recent_transactions=recent_transactions)

@buyer_bp.route('/offers')
def offers():
    if session.get('role') != 'buyer': return redirect(url_for('buyer.login'))
    
    my_offers = Offer.query.filter_by(buyer_id=session['user_id']).order_by(Offer.id.desc()).all()
    return render_template('buyer/offers.html', offers=my_offers)

@buyer_bp.route('/history')
def history():
    if session.get('role') != 'buyer': return redirect(url_for('buyer.login'))
    
    transactions = Transaction.query.filter_by(buyer_id=session['user_id']).order_by(Transaction.timestamp.desc()).all()
    return render_template('buyer/history.html', transactions=transactions)


@buyer_bp.route('/analytics')
def analytics():
    if session.get('role') != 'buyer': return redirect(url_for('buyer.login'))
    
    all_transactions = Transaction.query.filter_by(buyer_id=session['user_id']).order_by(Transaction.timestamp).all()
    
    # 1. Extract Options
    years = sorted(list(set(t.timestamp.year for t in all_transactions)), reverse=True)
    current_year = datetime.now().year
    
    crops = sorted(list(set(t.product.name if t.product else "Deleted Product" for t in all_transactions)))
    
    # 2. Get Filters
    sel_year = request.args.get('year', str(years[0]) if years else str(current_year))
    sel_month = request.args.get('month', 'all')
    sel_crop = request.args.get('crop', 'all')
    
    # 3. Apply Filters
    filtered = all_transactions
    if sel_year != 'all':
        filtered = [t for t in filtered if str(t.timestamp.year) == sel_year]
    if sel_month != 'all':
        filtered = [t for t in filtered if t.timestamp.strftime('%m') == sel_month]
    if sel_crop != 'all':
        filtered = [t for t in filtered if (t.product.name if t.product else "Deleted Product") == sel_crop]
        
    # 4. Aggregate & Chart Type
    chart_data = {}
    total_expense = 0
    chart_type = 'doughnut' # Default for comparison
    
    for t in filtered:
        total_expense += t.total_amount
        
    if sel_crop != 'all':
        # Trend Line for Specific Crop
        chart_type = 'line'
        for t in filtered:
            date_key = t.timestamp.strftime('%Y-%m-%d')
            chart_data[date_key] = chart_data.get(date_key, 0) + t.total_amount
    else:
        # Comparison Pie/Doughnut for All Crops
        chart_type = 'doughnut'
        for t in filtered:
            pkg = t.product.name if t.product else "Deleted Product"
            chart_data[pkg] = chart_data.get(pkg, 0) + t.total_amount
            
    return render_template('buyer/analytics.html', 
                         total_expense=total_expense,
                         purchase_data=chart_data,
                         chart_type=chart_type,
                         years=years,
                         crops=crops,
                         sel_year=sel_year,
                         sel_month=sel_month,
                         sel_crop=sel_crop)

@buyer_bp.route('/marketplace')
def marketplace():
    if session.get('role') != 'buyer': return redirect(url_for('buyer.login'))
    
    products = Product.query.join(User).filter(User.is_verified == True).all()
    return render_template('buyer/marketplace.html', products=products)

@buyer_bp.route('/make_offer/<int:product_id>', methods=['POST'])
def make_offer(product_id):
    if session.get('role') != 'buyer': return jsonify({'message': 'Login required'}), 401
    
    amount = float(request.form['offer_amount'])
    offer = Offer(product_id=product_id, buyer_id=session['user_id'], offer_price=amount, status='Pending')
    db.session.add(offer)
    db.session.commit()
    return jsonify({'status': 'Pending', 'message': 'Offer sent'})

@buyer_bp.route('/buy_now/<int:product_id>', methods=['POST'])
def buy_now(product_id):
    if session.get('role') != 'buyer': return "Unauthorized", 403
    
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 0))
    
    # 1. Enforce Minimum Order Quantity (30kg)
    if quantity < 30:
        flash("Minimum order quantity is 30kg!")
        return redirect(url_for('buyer.marketplace'))
        
    # 2. Check Stock
    if quantity > product.quantity:
        flash(f"Insufficient stock! Only {product.quantity}kg available.")
        return redirect(url_for('buyer.marketplace'))
    
    flash(f"Purchase initiated! Please confirm your order.")
    return render_template('buyer/confirm_order.html', 
                         product=product,
                         farmer=product.farmer,
                         quantity=quantity,
                         price=product.price,
                         total_amount=quantity * product.price)

@buyer_bp.route('/buy_offer/<int:offer_id>', methods=['POST'])
def buy_offer(offer_id):
    if session.get('role') != 'buyer': return "Unauthorized", 403
    
    offer = Offer.query.get_or_404(offer_id)
    if offer.status != 'Accepted': return "Offer not accepted", 400
    
    product = Product.query.get(offer.product_id)
    quantity = int(request.form.get('quantity', 0))
    
    # 1. Enforce Minimum Order Quantity (30kg)
    if quantity < 30:
        flash("Minimum order quantity is 30kg!")
        return redirect(url_for('buyer.dashboard'))
        
    # 2. Check Stock
    if quantity > product.quantity:
        flash(f"Insufficient stock! Only {product.quantity}kg available.")
        return redirect(url_for('buyer.dashboard'))
        
    flash(f"Deal closed! Please confirm your order.")
    return render_template('buyer/confirm_order.html', 
                         product=product,
                         farmer=product.farmer,
                         quantity=quantity,
                         price=offer.offer_price,
                         total_amount=quantity * offer.offer_price,
                         offer_id=offer.id)

@buyer_bp.route('/process_payment', methods=['POST'])
def process_payment():
    if session.get('role') != 'buyer': return "Unauthorized", 403
    
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    total_amount = float(request.form['total_amount'])
    offer_id = request.form.get('offer_id')
    
    product = Product.query.get_or_404(product_id)
    
    return render_template('buyer/payment.html', 
                         product=product,
                         farmer=product.farmer,
                         quantity=quantity,
                         price=price,
                         total_amount=total_amount,
                         offer_id=offer_id)
@buyer_bp.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    if session.get('role') != 'buyer': return "Unauthorized", 403
    
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    offer_id = request.form.get('offer_id')
    
    product = Product.query.get_or_404(product_id)
    
    # Create Verified Transaction
    trans = Transaction(product_id=product.id, buyer_id=session['user_id'], farmer_id=product.farmer_id,
                       quantity=quantity, price_per_unit=price,
                       total_amount=quantity * price)
    
    # Update Stock
    product.quantity -= quantity
    
    db.session.add(trans)
    db.session.commit()
    
    flash(f"Payment confirmed! Purchase of {quantity}kg {product.name} successful.")
    return redirect(url_for('buyer.payment_success', transaction_id=trans.id))

@buyer_bp.route('/payment_success/<int:transaction_id>')
def payment_success(transaction_id):
    if session.get('role') != 'buyer': return "Unauthorized", 403
    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.buyer_id != session['user_id']: return "Unauthorized", 403
    return render_template('buyer/payment_success.html', transaction=transaction)

@buyer_bp.route('/download_bill/<int:transaction_id>')
def download_bill(transaction_id):
    if session.get('role') != 'buyer': return "Unauthorized", 403
    
    t = Transaction.query.get_or_404(transaction_id)
    if t.buyer_id != session['user_id']: return "Unauthorized", 403
    
    return render_template('buyer/bill.html', t=t)
