from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_user, logout_user, current_user, login_required
from . import app, db, mail
from .forms import LoginForm, RegistrationForm, ProductForm
from .models import User, Product, Sale, Invoice, InvoiceItem
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .utils import send_whatsapp_message
from flask_mail import Message
from weasyprint import HTML


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
        # Print form errors if validation fails
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
    # Query all products
    all_products = Product.query.all()

    # Query all sold product codes
    sold_product_codes = [sale.product_code for sale in Sale.query.all()]

    # Filter out sold products
    unsold_products = [product for product in all_products if product.code not in sold_product_codes]

    return render_template('index.html', products=unsold_products)

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

    # Query products with available quantities
    products = Product.query.filter_by(
        item=item,
        type_material=type_material,
        size=size,
        price=price
    ).filter(Product.quantity > 0).all()  # Filter only products with available quantities

    product_data = [
        {
            'code': product.code,
            'item': product.item,
            'type_material': product.type_material,
            'size': product.size,
            'color': product.color,
            'description': product.description,
            'price': product.price,
            'quantity': product.quantity  # Include quantity in product data
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
            price=form.price.data
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

import logging
from flask import current_app

@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    sales_query = Sale.query.join(Product)

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    product_codes = request.args.getlist('product')
    entered_product_code = request.args.get('product_code')

    current_app.logger.info(f"start_date: {start_date}, end_date: {end_date}, product_codes: {product_codes}, entered_product_code: {entered_product_code}")

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

    current_app.logger.info(f"Total sales found: {len(sales)}")
    current_app.logger.info(f"Total sales amount: {total_sales_amount}")

    if sales:
        flash_message = 'Sales filtered successfully!'
    else:
        flash_message = 'No sales found matching the criteria.'

    # Ensure flash is called once outside conditional
    flash(flash_message, 'success')

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
            # Create a sale record for each product sold
            for product_code in product_codes:
                product = Product.query.filter_by(code=product_code).first_or_404()
                if product.quantity <= 0:
                    flash(f'Product {product.item} is out of stock.', 'danger')
                    return redirect(url_for('make_sale'))
                sale = Sale(product_code=product_code, quantity_sold=1, sale_date=datetime.now())
                db.session.add(sale)
                total_sale_amount += product.price

            # Create an invoice for the sale
            invoice = Invoice(
                customer_name=customer_name,
                customer_email=customer_email,
                total_amount=total_sale_amount,
                date_created=datetime.now()  # Ensure date is set correctly
            )
            db.session.add(invoice)
            db.session.commit()  # Commit to get the invoice ID

            # Record the sale in the invoice items
            for product_code in product_codes:
                invoice_item = InvoiceItem(product_code=product_code, quantity=1, invoice_id=invoice.id)
                db.session.add(invoice_item)

                # Deduct sold products from the Product table
                product = Product.query.filter_by(code=product_code).first_or_404()
                product.quantity -= 1

            db.session.commit()
            flash('Sale and invoice recorded successfully!', 'success')

            # Generate PDF
            pdf = generate_invoice_pdf(invoice)

            # Send Email
            send_invoice_email(customer_email, pdf)

            # Send WhatsApp notification
            send_whatsapp_message(invoice.id, customer_name, total_sale_amount)
            flash('WhatsApp notification sent!', 'success')

            return redirect(url_for('print_invoice', invoice_id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while processing the sale: {str(e)}', 'danger')

    return render_template('make_sales.html')

def generate_invoice_pdf(invoice):
    rendered = render_template('invoice_template.html', invoice=invoice)
    pdf = HTML(string=rendered).write_pdf()
    return pdf

def send_invoice_email(email, pdf):
    msg = Message('Invoice', recipients=[email])
    msg.body = 'Please find the attached invoice.'
    msg.attach('invoice.pdf', 'application/pdf', pdf)
    mail.send(msg)




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

# Route to fetch and display all invoices
@app.route('/invoices')
@login_required
def invoices():
    # Get search parameters from request
    search_term = request.args.get('search_term')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    invoice_id = request.args.get('invoice_id')

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

    if not all_invoices:
        flash('No invoices found matching the criteria.', 'info')
    else:
        flash('Invoices filtered successfully!', 'success')

    return render_template('all_invoices.html', invoices=all_invoices)


@app.route('/generate_invoice', methods=['GET', 'POST'])
def generate_invoice():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        total_amount = request.form['total_amount']
        new_invoice = Invoice(customer_name=customer_name, total_amount=total_amount)
        db.session.add(new_invoice)
        db.session.commit()

        # Send WhatsApp message
        send_whatsapp_message(new_invoice.id, customer_name, total_amount)

        flash('Invoice generated and WhatsApp notification sent!', 'success')
        return redirect(url_for('index'))

    # Handle GET requests
    return render_template('make_sales.html')

def send_invoice_email(email, invoice):
    msg = Message('Invoice', recipients=[email])
    msg.body = render_template('emails/invoice_email_template.txt', invoice=invoice)
    msg.html = render_template('emails/invoice_email_template.html', invoice=invoice)
    mail.send(msg)