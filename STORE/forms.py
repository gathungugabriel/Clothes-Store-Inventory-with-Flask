from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, FloatField, IntegerField, SubmitField, PasswordField
from wtforms.validators import DataRequired, NumberRange, Email, EqualTo, Length

class ProductForm(FlaskForm):
    barcode = StringField('Barcode', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Admin')

class ProductForm(FlaskForm):
    barcode = StringField('barcode')
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired()])