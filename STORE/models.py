from . import db
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

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
    code = db.Column(db.String(20), primary_key=True, unique=True, nullable=False, index=True)  # Index added to code column
    item = db.Column(db.String(100), nullable=False)
    type_material = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sales = relationship('Sale', backref='product', lazy=True)  # Relationship with Sale model

    def serialize(self):
        return {
            'code': self.code,
            'item': self.item,
            'type_material': self.type_material,
            'size': self.size,
            'color': self.color,
            'description': self.description,
            'price': self.price,
            'quantity': self.quantity
        }

    def __repr__(self):
        return f"Product('{self.code}', '{self.item}', '{self.type_material}', '{self.size}', '{self.color}', '{self.description}', '{self.price}', '{self.quantity}')"

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(20), db.ForeignKey('product.code'), nullable=False)  # ForeignKey to product code
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
