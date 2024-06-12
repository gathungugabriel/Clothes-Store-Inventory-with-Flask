from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, FloatField, IntegerField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, NumberRange, Email, EqualTo, Length

class ProductForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    item = StringField('Item', render_kw={'readonly': True})
    category = StringField('Category', render_kw={'readonly': True})
    type_material = StringField('Type/Material', validators=[DataRequired()])
    size = StringField('Size', validators=[DataRequired()])
    color = StringField('Color', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    buying_price = FloatField('Buying Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    profit = FloatField('Profit', validators=[DataRequired(), NumberRange(min=0)])
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
