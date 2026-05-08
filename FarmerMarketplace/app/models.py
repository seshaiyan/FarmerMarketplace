from . import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) 
    role = db.Column(db.String(20), nullable=False) # 'admin', 'farmer', 'buyer'
    contact_number = db.Column(db.String(15))
    
    # Farmer specific fields
    state = db.Column(db.String(50))
    district = db.Column(db.String(50))
    place = db.Column(db.String(50))
    upi_id = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)

class MarketPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False) # Floor Price
    image_url = db.Column(db.String(200))
    
    # Detailed fields
    condition = db.Column(db.String(100)) # e.g., Fresh, Organic
    weight_unit = db.Column(db.String(20), default='kg')
    location_state = db.Column(db.String(50))
    location_district = db.Column(db.String(50))
    location_place = db.Column(db.String(50))
    
    # Prediction & Advisory
    predicted_price = db.Column(db.Float)
    advisory = db.Column(db.String(500))
    
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    farmer = db.relationship('User', backref=db.backref('products', lazy=True))

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    offer_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Accepted, Rejected

    buyer = db.relationship('User', foreign_keys=[buyer_id])
    product = db.relationship('Product', foreign_keys=[product_id])

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships for easy access
    product = db.relationship('Product')
    buyer = db.relationship('User', foreign_keys=[buyer_id])
    farmer = db.relationship('User', foreign_keys=[farmer_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 'price_alert', 'offer_update', 'system'
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
