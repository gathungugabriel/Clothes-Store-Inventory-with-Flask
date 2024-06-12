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
# from weasyprint import HTML


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
        # Add your logic for adding the product here
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
    all_products = Product.query.all()
    sold_product_codes = [sale.product_code for sale in Sale.query.all()]
    unsold_products = [product for product in all_products if product.code not in sold_product_codes]
    return render_template('index.html', products=unsold_products)

# Product management routes
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
    ).filter(Product.quantity > 0).all()

    product_data = [
        {
            'code': product.code,
            'item': product.item,
            'type_material': product.type_material,
            'size': product.size,
            'color': product.color,
            'description': product.description,
            'price': product.price,
            'quantity': product.quantity
        } 
        for product in products
    ]

    return jsonify(product_data)

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

    filtered_products_data = [
        {
            'item': product.item,
            'type_material': product.type_material,
            'size': product.size,
            'price': product.price
        } 
        for product in filtered_products
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

    if product_codes and product_codes != ['']:
        sales_query = sales_query.filter(Sale.product_code.in_(product_codes))

    if entered_product_code:
        sales_query = sales_query.filter(Sale.product_code == entered_product_code)

    sales = sales_query.all()
    products = Product.query.all()
    total_sales_amount = sum(sale.quantity_sold * sale.product.price for sale in sales)

    if filtering_criteria_present:
        if sales:
            flash('Sales filtered successfully!', 'success')
        else:
            flash('No sales found matching the criteria.', 'warning')

    return render_template('sales.html', sales=sales, total_sales_amount=total_sales_amount, products=products)

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

def generate_invoice_pdf(invoice):
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Invoice</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
            }}
            .title {{
                text-align: center;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .customer-details, .total-amount {{
                margin-bottom: 10px;
                font-size: 14px;
            }}
            .invoice-items {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            .invoice-items th, .invoice-items td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .invoice-items th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <div class="title">Invoice</div>
        <div class="customer-details">Customer: {invoice.customer_name}</div>
        <div class="customer-details">Email: {invoice.customer_email}</div>
        <div class="total-amount">Total Amount: ${invoice.total_amount}</div>
        
        <table class="invoice-items">
            <thead>
                <tr>
                    <th>Product Code</th>
                    <th>Quantity</th>
                    <th>Price</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'<tr><td>{item.product_code}</td><td>{item.quantity}</td><td>{item.product.price}</td></tr>' for item in invoice.items])}
            </tbody>
        </table>
    </body>
    </html>
    '''

    pdf_file_path = f"invoice_{invoice.id}.pdf"
    HTML(string=html_content).write_pdf(pdf_file_path)
    return pdf_file_path

@app.route('/invoice/<int:invoice_id>/print', methods=['GET'])
@login_required
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('print_invoice.html', invoice=invoice)

@app.route('/get_product_details/<code>', methods=['GET'])
def get_product_details(code):
    product = Product.query.filter_by(code=code).first()
    if product:
        return jsonify(product.serialize())
    else:
        return jsonify({'error': 'Product not found'}), 404

@app.route('/invoices', methods=['GET'])
@login_required
def invoices():
    # Get search parameters from request
    search_term = request.args.get('search_term')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    invoice_id = request.args.get('invoice_id')

    # Check if any filtering criteria are present
    filtering_criteria_present = search_term or start_date or end_date or invoice_id

    # Query invoices based on search parameters
    query = Invoice.query

    if search_term:
        query = query.filter(
            or_(
                Invoice.customer_name.ilike(f'%{search_term}%'),
                Invoice.customer_email.ilike(f'%{search_term}%')
            )
        )

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Invoice.date_created >= start_date)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Invoice.date_created <= end_date)

    if invoice_id:
        query = query.filter(Invoice.id == invoice_id)

    all_invoices = query.all()

    # Only flash messages if filtering criteria are present
    if filtering_criteria_present:
        if all_invoices:
            flash('Invoices filtered successfully!', 'success')
        else:
            flash('No invoices found matching the criteria.', 'warning')

    return render_template('all_invoices.html', invoices=all_invoices)


@app.route('/generate_invoice', methods=['GET', 'POST'])
def generate_invoice():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        total_amount = request.form['total_amount']
        new_invoice = Invoice(customer_name=customer_name, total_amount=total_amount)
        db.session.add(new_invoice)
        db.session.commit()

        flash('Invoice generated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('make_sales.html')
