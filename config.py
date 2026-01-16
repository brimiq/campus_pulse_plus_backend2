import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS
from flask_session import Session


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Session configuration
    app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE", "filesystem")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    CORS(
        app, 
        supports_credentials=True,
        resources={r"/*": {"origins": cors_origins}}
    )
    Session(app)
    db.init_app(app)

    return app
