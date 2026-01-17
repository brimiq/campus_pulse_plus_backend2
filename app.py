from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import timedelta, datetime
import re
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import func, case


load_dotenv()


from config import db
from models import (
   User,
   Post,
   Comment,
   Reaction,
   Category,
   AdminResponse,
   SecurityReport,
   EscortRequest,
   UniversitySettings,
   ChatMessage,
)
app = Flask(__name__)




logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)




limiter = Limiter(
   get_remote_address,
   app=app,
   default_limits=["1000 per day", "200 per hour"],
   storage_uri="memory://",
)




app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)




app.config["SESSION_COOKIE_NAME"] = "campus_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False 
app.config["SESSION_COOKIE_SAMESITE"] = "Lax" 
app.config["SESSION_COOKIE_DOMAIN"] = None 
app.config["SESSION_COOKIE_PATH"] = "/"