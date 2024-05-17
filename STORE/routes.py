from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_user, logout_user, current_user, login_required
from . import app, db
from .forms import LoginForm, RegistrationForm, ProductForm
from .models import User, Product, Sale
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime

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
            flash('Invalid username or password', 'warning')
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
        return redirect(url_for('login'))
    return render_template('initial.html')

@app.route('/index')
@login_required
def index():
    # Fetch all products and group them by all features besides code, description, and color
    products = db.session.query(
        Product.item,
        Product.type_material,
        Product.size,
        Product.price,
        func.sum(Product.quantity).label('total_quantity')
    ).group_by(
        Product.item,
        Product.type_material,
        Product.size,
        Product.price,
        
    ).all()

    # Calculate total quantity by summing up the quantities of all products
    total_quantity = sum(product.total_quantity for product in products)

    return render_template('index.html', products=products, total_quantity=total_quantity)

# @app.route('/expand_items/<string:item>', methods=['GET'])
# @login_required
# def expand_items(item):
#     # Query products with similar features
#     products = Product.query.filter_by(item=item).all()

#     # Prepare list of product data
#     product_data = []
#     for product in products:
#         product_data.append({
#             'code': product.code,
#             'description': product.description
#         })

#     # Print fetched data for debugging
#     print("Fetched data:", product_data)

#     # Return JSON response
#     return jsonify(product_data)
@app.route('/expand_items', methods=['POST'])
@login_required
def expand_items():
    data = request.get_json()
    item = data.get('item')
    type_material = data.get('type_material')
    size = data.get('size')
    price = data.get('price')

    if not all([item, type_material, size, price]):
        return jsonify({'error': 'Invalid parameters'}), 400

    products = Product.query.filter_by(
        item=item,
        type_material=type_material,
        size=size,
        price=price
    ).all()

    product_data = [
        {
            'code': product.code,
            'item': product.item,
            'type_material': product.type_material,
            'size': product.size,
            'color': product.color,
            'description': product.description,
            'price': product.price
        } 
        for product in products
    ]

    return jsonify(product_data)



@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        existing_product = Product.query.filter_by(code=form.code.data).first()
        if existing_product:
            flash('Product with this code already exists!', 'danger')
            return redirect(url_for('add_product'))
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
        try:
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            flash('An error occurred while adding the product!', 'danger')
            db.session.rollback()
            return redirect(url_for('add_product'))
    return render_template('add_product.html', form=form)

@app.route('/update_product/<string:code>', methods=['GET', 'POST'])
@login_required
def update_product(code):
    product = Product.query.filter_by(code=code).first_or_404()
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        form.populate_obj(product)
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('update_product.html', form=form, product=product)

@app.route('/delete_product/<string:code>', methods=['POST'])
@login_required
def delete_product(code):
    product = Product.query.filter_by(code=code).first_or_404()
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
        filtered_products = [{'id': product.id, 'code': product.code, 'item': product.item, 'type_material': product.type_material, 'size': product.size, 'color': product.color, 'description': product.description, 'price': product.price, 'quantity': product.quantity} for product in Product.query.filter(Product.description.ilike(f'%{search_term}%'))]

    return jsonify({'products': filtered_products})

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    sales_query = Sale.query.join(Product)

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    product_codes = request.args.getlist('product')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        sales_query = sales_query.filter(Sale.sale_date >= start_date)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        sales_query = sales_query.filter(Sale.sale_date <= end_date)

    if product_codes:
        product_filters = [Sale.product_code == code for code in product_codes]
        sales_query = sales_query.filter(or_(*product_filters))

    sales = sales_query.all()
    products = Product.query.all()
    total_sales_amount = sum(sale.quantity_sold * sale.product.price for sale in sales)

    return render_template('sales.html', sales=sales, total_sales_amount=total_sales_amount, products=products)

@app.route('/make_sale', methods=['GET', 'POST'])
@login_required
def make_sale():
    if request.method == 'POST':
        product_code = request.form.get('product_code')
        quantity = request.form.get('quantity')

        product = Product.query.filter_by(code=product_code).first_or_404()
        if product.quantity >= int(quantity):
            product.quantity -= int(quantity)
            sale = Sale(product_code=product_code, quantity_sold=int(quantity))
            db.session.add(sale)
            db.session.commit()
            flash('Sale recorded successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Not enough stock available for sale!', 'danger')

    return render_template('make_sales.html')
