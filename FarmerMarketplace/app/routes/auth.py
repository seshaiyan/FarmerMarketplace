from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('auth.register'))
            
        new_user = User(username=username, password=password, role=role)
        new_user.contact_number = request.form.get('contact_number')
        
        if role == 'farmer':
            new_user.state = request.form.get('state')
            new_user.district = request.form.get('district')
            new_user.place = request.form.get('place')
            new_user.is_verified = False
        else:
            new_user.is_verified = True 
            
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        
        # Redirect to appropriate login based on role
        if role == 'admin': return redirect(url_for('admin.login'))
        if role == 'farmer': return redirect(url_for('farmer.login'))
        if role == 'buyer': return redirect(url_for('buyer.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.landing'))
