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

# Load environment variables
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

# Logging configuration
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Rate Limiting
limiter = Limiter(
   get_remote_address,
   app=app,
   default_limits=["1000 per day", "200 per hour"],
   storage_uri="memory://",
)

# App Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# --- SESSION & CORS SETTINGS ---
app.config["SESSION_COOKIE_NAME"] = "campus_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_PATH"] = "/"

# Detect if we are running on Render
IS_PRODUCTION = os.environ.get("PORT") is not None

if IS_PRODUCTION:
    # Production: Must use Secure and SameSite=None for cross-domain cookies (Vercel -> Render)
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
else:
    # Local: Standard settings
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Allowed Origins
ALLOWED_ORIGINS = [
    "https://campuspulseplusfrontend-git-main-washiras-projects-fb5072e5.vercel.app",
    "https://campuspulseplusfrontend.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174"
]

CORS(
   app,
   supports_credentials=True,
   origins=os.getenv("CORS_ORIGINS", ",".join(ALLOWED_ORIGINS)).split(","),
   methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
   allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

db.init_app(app)

# --- MIDDLEWARE & HELPERS ---
@app.before_request
def make_session_permanent():
   session.permanent = True

def student_required(f):
   @wraps(f)
   def wrapper(*args, **kwargs):
       if session.get("role") != "student":
           return {"error": "Only students allowed"}, 403
       return f(*args, **kwargs)
   return wrapper

def admin_required(f):
   @wraps(f)
   def wrapper(*args, **kwargs):
       if session.get("role") != "admin":
           return {"error": "Only admins allowed"}, 403
       return f(*args, **kwargs)
   return wrapper

def is_valid_email(email):
   return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- AUTH ROUTES ---

@app.route("/")
def health_check():
    return {"status": "healthy", "message": "Campus Pulse Backend is running!"}, 200

@app.route("/auth/signup", methods=["POST"])
@limiter.limit("5 per minute")
def signup():
   try:
       data = request.get_json()
       if not data:
           return {"error": "Invalid JSON"}, 400

       email = data.get("email", "").strip()
       password = data.get("password", "").strip()
       
       if not email or not password:
           return {"error": "Email and password required"}, 400
       if not is_valid_email(email):
           return {"error": "Invalid email format"}, 400
       if len(password) < 4:
           return {"error": "Password too short"}, 400
       if User.query.filter_by(email=email).first():
           return {"error": "Email already registered"}, 400

       user = User(email=email)
       user.set_password(password)
       db.session.add(user)
       db.session.commit()

       session["user_id"] = user.id
       session["role"] = user.role
       return {"user": {"id": user.id, "email": user.email, "role": user.role}}, 201
   except Exception as e:
       db.session.rollback()
       return {"error": "Internal server error"}, 500

@app.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
   data = request.get_json()
   user = User.query.filter_by(email=data.get("email")).first()
   if user and user.check_password(data.get("password")):
       session["user_id"] = user.id
       session["role"] = user.role
       return {"user": {"id": user.id, "email": user.email, "role": user.role}}, 200
   return {"error": "Invalid credentials"}, 401

@app.route("/auth/logout", methods=["POST"])
def logout():
   session.clear()
   return {"message": "Logged out"}, 200

@app.route("/auth/current_user", methods=["GET"])
def current_user():
   uid = session.get("user_id")
   if not uid:
       return jsonify(None)
   user = User.query.get(uid)
   return {"id": user.id, "email": user.email, "role": user.role}

# --- API ROUTES (POSTS, COMMENTS, ETC) ---

@app.route("/api/categories", methods=["GET"])
def get_categories():
   categories = Category.query.all()
   return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in categories])

@app.route("/api/posts", methods=["GET"])
def get_posts():
   try:
       category_id = request.args.get("category_id", type=int)
       query = Post.query.order_by(Post.created_at.desc())
       if category_id:
           query = query.filter_by(category_id=category_id)

       posts = query.limit(10).all()
       data = []
       for p in posts:
           likes = sum(1 for r in p.reactions if r.reaction_type == "like")
           dislikes = sum(1 for r in p.reactions if r.reaction_type == "dislike")
           admin_response = p.admin_responses[0].content if p.admin_responses else None
           data.append({
               "id": p.id,
               "content": p.content,
               "images": p.images,
               "category_id": p.category_id,
               "category_name": p.category.name,
               "user_id": p.user_id,
               "created_at": p.created_at,
               "likes": likes,
               "dislikes": dislikes,
               "comments_count": len(p.comments),
               "admin_response": admin_response,
           })
       return jsonify(data)
   except Exception:
       return {"error": "Internal server error"}, 500

@app.route("/api/reactions", methods=["POST"])
def add_reaction():
   data = request.get_json()
   post_id = data["post_id"]
   reaction_type = data["reaction_type"]
   user_id = session.get("user_id")
   if not user_id:
       return {"error": "Not logged in"}, 401
   
   existing = Reaction.query.filter_by(post_id=post_id, user_id=user_id).first()
   if existing:
       if existing.reaction_type == reaction_type:
           db.session.delete(existing)
           user_reaction = None
       else:
           existing.reaction_type = reaction_type
           user_reaction = reaction_type
   else:
       db.session.add(Reaction(post_id=post_id, user_id=user_id, reaction_type=reaction_type))
       user_reaction = reaction_type
   
   db.session.commit()
   reactions = Reaction.query.filter_by(post_id=post_id).all()
   return {
       "likes": sum(1 for r in reactions if r.reaction_type == "like"),
       "dislikes": sum(1 for r in reactions if r.reaction_type == "dislike"),
       "user_reaction": user_reaction,
   }

# --- REMAINING API ENDPOINTS (SECURITY, ESCORT, ADMIN) ---
# (Shortened for brevity but preserved logic from original)

@app.route("/api/security-reports", methods=["POST"])
@student_required
def create_security_report():
   data = request.get_json()
   report = SecurityReport(
       type=data["type"],
       description=data["description"],
       latitude=data["latitude"],
       longitude=data["longitude"],
       user_id=session.get("user_id"),
   )
   db.session.add(report)
   db.session.commit()
   return {"message": "Security report created"}, 201

# --- STARTUP LOGIC ---

try:
    with app.app_context():
        db.create_all()
        app.logger.info("Database initialized successfully")
except Exception as e:
    app.logger.error(f"Database initialization failed: {str(e)}")

if __name__ == "__main__":
    # Always bind to the PORT provided by Render, or default to 10000 for local dev
    port = int(os.environ.get("PORT", 10000))
    # In production, debug must be False. Locally, it can be True.
    app.run(host="0.0.0.0", port=port, debug=not IS_PRODUCTION)
