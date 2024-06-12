from . import db
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    code = db.Column(db.String(20), primary_key=True, unique=True, nullable=False, index=False)
    item = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # Add category field
    type_material = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False, default=0)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    sales = relationship('Sale', backref='product', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profit = self.calculate_profit()

    def calculate_profit(self):
        return self.selling_price - self.buying_price

    def serialize(self):
        return {
            'code': self.code,
            'item': self.item,
            'category': self.category,  # Include category in serialization
            'type_material': self.type_material,
            'size': self.size,
            'color': self.color,
            'description': self.description,
            'buying_price': self.buying_price,
            'selling_price': self.selling_price,
            'profit': self.profit
        }

    def __repr__(self):
        return f"Product('{self.code}', '{self.item}', '{self.category}', '{self.type_material}', '{self.size}', '{self.color}', '{self.description}', '{self.buying_price}', '{self.selling_price}', '{self.profit}')"

    def set_prices(self, buying_price, selling_price):
        self.buying_price = buying_price
        self.selling_price = selling_price
        self.profit = self.calculate_profit()

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(20), db.ForeignKey('product.code'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(128), nullable=False)
    customer_email = db.Column(db.String(128), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True)

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(64), db.ForeignKey('product.code'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product = db.relationship('Product')
