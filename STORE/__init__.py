from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Create Flask app instance
app = Flask(__name__)

# Configure the secret key for encrypting session data
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Change the path as needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy database
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'  # Specify the login page
login_manager.init_app(app)

# Import the User model for Flask-Login
from .models import User

@login_manager.user_loader
def load_user(user_id):
    # Return the user object based on user_id
    return User.query.get(int(user_id))

# Import routes (views)
from . import routes
