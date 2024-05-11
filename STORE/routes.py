from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_user, logout_user, current_user, login_required
from . import app, db
from .forms import LoginForm, RegistrationForm, ProductForm
from .models import User, Product

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('initial'))

@app.route('/')
def initial():
    if current_user.is_authenticated:
        return redirect(url_for('login'))  # Redirect authenticated users to the login page
    return render_template('initial.html')


@app.route('/index')
@login_required
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            code=form.code.data,
            item=form.item.data,
            type_material=form.type_material.data,
            size=form.size.data,
            color=form.color.data,
            description=form.description.data,
            price=form.price.data,
            quantity=form.quantity.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_product.html', form=form)

@app.route('/update_product/<int:id>', methods=['GET', 'POST'])
@login_required
def update_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.code = form.code.data
        product.item = form.item.data
        product.type_material = form.type_material.data
        product.size = form.size.data
        product.color = form.color.data
        product.description = form.description.data
        product.price = form.price.data
        product.quantity = form.quantity.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('update_product.html', form=form, product=product)

@app.route('/delete_product/<int:id>', methods=['POST'])
@login_required
def delete_product_by_id(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/fetch_products')
def fetch_products():
    products = Product.query.all()
    products_data = [{'id': product.id, 'code': product.code, 'item': product.item, 'type_material': product.type_material, 'size': product.size, 'color': product.color, 'description': product.description, 'price': product.price, 'quantity': product.quantity} for product in products]
    return jsonify({'products': products_data})

@app.route('/filter_products', methods=['POST'])
@login_required
def filter_products():
    search_term = request.form.get('search_term', '').lower()
    filtered_products = []

    if search_term:
        # Filter products based on the search term
        filtered_products = [{'id': product.id, 'code': product.code, 'item': product.item, 'type_material': product.type_material, 'size': product.size, 'color': product.color, 'description': product.description, 'price': product.price, 'quantity': product.quantity} for product in Product.query.filter(Product.description.ilike(f'%{search_term}%'))]

    return jsonify({'products': filtered_products})
