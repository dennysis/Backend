import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')  # Default if not set
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this in your code!
app.config["JWT_COOKIE_SAMESITE"]="Lax"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587  
app.config['MAIL_USERNAME'] = 'emungai906@gmail.com'  
app.config['MAIL_PASSWORD'] = 'wplz rpce ffvj bjoe'  
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


jwt = JWTManager(app)

# Initialize CORS with restricted origins
cors = CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}}, supports_credentials=True)
mail=Mail(app)
db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

api = Api(app)
migrate = Migrate(app, db)

from models import User  # Import after initializing db and login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

