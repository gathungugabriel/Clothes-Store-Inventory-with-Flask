from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from . import app, db
from .forms import LoginForm, RegistrationForm, ProductForm  # Import ProductForm
from .models import User, Product  # Import Product model

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        # Print form data
        print('Form data:', form.username.data, form.password.data)
        
        # Query the database for the user
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            # Check if the password matches
            if user.check_password(form.password.data):
                # Print a message to confirm successful authentication
                print('User authenticated:', user.username)
                
                # Log in the user
                login_user(user)
                
                # Redirect the user to the home page
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
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
    return redirect(url_for('index'))

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required  # Require login to add a product
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_product.html', form=form)

@app.route('/update_product/<int:id>', methods=['GET', 'POST'])
@login_required  # Require login to update a product
def update_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('update_product.html', form=form, product=product)

@app.route('/delete_product/<int:id>', methods=['POST'])
@login_required  # Require login to delete a product
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('index'))
