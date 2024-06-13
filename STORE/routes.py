from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_user, logout_user, current_user, login_required
from . import app, db
from .forms import LoginForm, RegistrationForm, ProductForm
from .models import User, Product, Sale, Invoice, InvoiceItem
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .utils import generate_tag, prefixes
from add_data import add_products_from_csv

# Define routes and views
@app.route('/handle_barcode/<barcode>', methods=['GET'])
@login_required
def handle_barcode(barcode):
    product = Product.query.filter_by(code=barcode).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Determine action based on some condition
    action = request.args.get('action', 'filter')

    if action == 'add':
        # Handle product addition
        return jsonify({'action': 'add', 'product': product.serialize()})
    elif action == 'delete':
        # Handle product deletion
        db.session.delete(product)
        db.session.commit()
        return jsonify({'action': 'delete', 'product': product.serialize()})
    elif action == 'filter':
        # Handle product filtering
        return jsonify({'action': 'filter', 'product': product.serialize()})
    else:
        return jsonify({'error': 'Invalid action'}), 400

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
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
        username = form.username.data
        email = form.email.data
        password = form.password.data

        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists. Please choose a different one.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        print(form.errors)
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('initial'))

@app.route('/')
def initial():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('initial.html')

@app.route('/index')
@login_required
def index():
    unsold_products = Product.query.filter(Product.quantity > 0).all()
    
    # Example logic to group products by item and category
    grouped_products = {}
    for product in unsold_products:
        key = (product.item, product.category)
        if key not in grouped_products:
            grouped_products[key] = {
                'products': [],
                'total_quantity': 0,
                'total_buying_price': 0,
                'total_selling_price': 0,
                'total_profit': 0
            }
        grouped_products[key]['products'].append(product)
        grouped_products[key]['total_quantity'] += product.quantity
        grouped_products[key]['total_buying_price'] += product.buying_price * product.quantity
        grouped_products[key]['total_selling_price'] += product.selling_price * product.quantity
        grouped_products[key]['total_profit'] += product.profit * product.quantity
    
    grouped_products_display = {
        f"{k[1]} - {k[0]}": v for k, v in grouped_products.items()
    }
    
    return render_template('index.html', grouped_products=grouped_products_display)


@app.route('/expand_items', methods=['POST'])
@login_required
def expand_items():
    try:
        data = request.get_json()

        if not data or 'item' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        category_item = data['item']
        category, item = category_item.split('___')
        products = Product.query.filter_by(category=category, item=item).all()

        if not products:
            return jsonify({'error': 'No products found'}), 404

        products_data = [
            {
                'code': product.code,
                'size': product.size,
                'type_material': product.type_material,
                'color': product.color,
                'description': product.description,
                'buying_price': product.buying_price,
                'selling_price': product.selling_price,
                'profit': product.profit,
                'quantity': product.quantity
            }
            for product in products
        ]

        return jsonify({'products': products_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_items_by_code', methods=['POST'])
@login_required
def get_items_by_code():
    try:
        data = request.get_json()
        code = data.get('code')

        if not code:
            return jsonify({'error': 'No code provided'}), 400

        product = Product.query.filter_by(code=code).first()

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        product_data = {
            'code': product.code,
            'item': product.item,
            'category': product.category,
            'type_material': product.type_material,
            'size': product.size,
            'color': product.color,
            'description': product.description,
            'buying_price': product.buying_price,
            'selling_price': product.selling_price,
            'profit': product.profit,
            'quantity': product.quantity
        }

        return jsonify(product_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/grouped_products', methods=['GET'])
@login_required
def grouped_products():
    products = Product.query.filter(Product.quantity > 0).all()
    grouped_products = {}

    for product in products:
        category = product.category if product.category else 'Others'
        if category not in grouped_products:
            grouped_products[category] = []
        grouped_products[category].append(product)

    return jsonify(grouped_products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        # Extract the code prefix
        code_prefix = form.code.data.upper()

        # Initialize item and category
        item = None
        category = None

        # Determine the item and category from the code prefix
        for item_key, prefix_data in prefixes.items():
            if isinstance(prefix_data, dict):
                for subcategory_key, prefix in prefix_data.items():
                    if code_prefix.startswith(prefix):
                        item = item_key
                        category = subcategory_key
                        break
            else:
                if code_prefix.startswith(prefix_data):
                    item = item_key
                    category = ""  # No subcategory for this item
                    break

        if not item:
            # Handle invalid code prefix
            flash('Invalid code prefix!', 'danger')
            return redirect(url_for('add_product'))

        try:
            # Generate the tag
            subcategory = category  # For readability
            item_code = Product.query.filter_by(item=item, category=subcategory).count() + 1
            product_code = generate_tag(item, subcategory, item_code)

            product = Product(
                code=product_code,
                item=item,
                category=subcategory,
                type_material=form.type_material.data,
                size=form.size.data,
                color=form.color.data,
                description=form.description.data,
                buying_price=form.buying_price.data,
                selling_price=form.selling_price.data
            )

            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            flash('An error occurred while adding the product!', 'danger')
            db.session.rollback()
        except ValueError as e:
            flash(f'Error: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('add_product.html', form=form)

@app.route('/update_product/<string:code>', methods=['GET', 'POST'])
@login_required
def update_product(code):
    product = Product.query.filter_by(code=code).first_or_404()
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        form.populate_obj(product)
        product.profit = product.calculate_profit()
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

@app.route('/filter_products', methods=['POST'])
@login_required
def filter_products():
    data = request.get_json()
    search_term = data.get('search_term', '').lower()

    filtered_products = Product.query.filter(
        or_(
            Product.item.ilike(f'%{search_term}%'),
            Product.type_material.ilike(f'%{search_term}%'),
            Product.size.ilike(f'%{search_term}%'),
            Product.color.ilike(f'%{search_term}%'),
            Product.description.ilike(f'%{search_term}%')
        )
    ).all()

    grouped_products = {}
    for product in filtered_products:
        key = (product.item, product.category)
        if key not in grouped_products:
            grouped_products[key] = []
        grouped_products[key].append(product)
    
    filtered_products_data = [
        {
            'category': category,
            'item': item,
            'products': [
                {
                    'code': product.code,
                    'item': product.item,
                    'category': product.category,
                    'type_material': product.type_material,
                    'size': product.size,
                    'color': product.color,
                    'description': product.description,
                    'buying_price': product.buying_price,
                    'selling_price': product.selling_price,
                    'profit': product.profit,
                    'quantity': product.quantity
                } for product in products
            ]
        }
        for (item, category), products in grouped_products.items()
    ]

    return jsonify({'products': filtered_products_data})

@app.route('/add_data_to_db')
@login_required
def add_data_to_db():
    try:
        add_products_from_csv('products.csv')  # Assuming your CSV file is named products.csv
        return jsonify({'message': 'Data added to database successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sales routes
@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    sales_query = Sale.query.join(Product)

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    product_codes = request.args.getlist('product')
    entered_product_code = request.args.get('product_code')

    # Check if any filtering criteria are present
    filtering_criteria_present = start_date or end_date or product_codes or entered_product_code

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        sales_query = sales_query.filter(Sale.sale_date >= start_date)
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        sales_query = sales_query.filter(Sale.sale_date <= end_date)
    if product_codes:
        sales_query = sales_query.filter(Product.code.in_(product_codes))
    if entered_product_code:
        sales_query = sales_query.filter(Product.code == entered_product_code)

    sales = sales_query.all()

    return render_template('sales.html', sales=sales, filtering_criteria_present=filtering_criteria_present)

@app.route('/make_sale', methods=['GET', 'POST'])
@login_required
def make_sale():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email')
        product_codes = request.form.getlist('product_code[]')

        total_sale_amount = 0

        try:
            for product_code in product_codes:
                product = Product.query.filter_by(code=product_code).first_or_404()
                if product.quantity <= 0:
                    flash(f'Product {product.item} is out of stock.', 'danger')
                    return redirect(url_for('make_sale'))
                sale = Sale(product_code=product_code, quantity_sold=1, sale_date=datetime.now())
                db.session.add(sale)
                total_sale_amount += product.price

            invoice = Invoice(
                customer_name=customer_name,
                customer_email=customer_email,
                total_amount=total_sale_amount,
                date_created=datetime.now()
            )
            db.session.add(invoice)
            db.session.commit()

            for product_code in product_codes:
                invoice_item = InvoiceItem(product_code=product_code, quantity=1, invoice_id=invoice.id)
                db.session.add(invoice_item)

                product = Product.query.filter_by(code=product_code).first_or_404()
                product.quantity -= 1

            db.session.commit()
            flash('Sale and invoice recorded successfully!', 'success')

            pdf = generate_invoice_pdf(invoice)
            return redirect(url_for('print_invoice', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while processing the sale: {str(e)}', 'danger')

    return render_template('make_sales.html')

@app.route('/invoices', methods=['GET'])
@login_required
def invoices():
    invoices_query = Invoice.query.join(User)
    invoice_number = request.args.get('invoice_number')
    entered_product_code = request.args.get('product_code')

    # Check if any filtering criteria are present
    filtering_criteria_present = invoice_number or entered_product_code

    if invoice_number:
        invoices_query = invoices_query.filter(Invoice.invoice_number == invoice_number)
    if entered_product_code:
        invoices_query = invoices_query.join(InvoiceItem).join(Product).filter(Product.code == entered_product_code)

    invoices = invoices_query.all()

    return render_template('invoices.html', invoices=invoices, filtering_criteria_present=filtering_criteria_present)
