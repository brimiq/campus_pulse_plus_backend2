from flask import Blueprint, request, jsonify, session
from config import db
from models.user import User
from werkzeug.security import check_password_hash
import re

auth_bp = Blueprint("auth", __name__)

# Helper to validate email format
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# -----------------------------
# Signup route
# -----------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    # Validation
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters"}), 400

    # Check if email exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    # Create user
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Save session
    session["user_id"] = user.id
    session["role"] = user.role

    return jsonify({"message": "Signup successful", "role": user.role}), 201

# -----------------------------
# Login route
# -----------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password_hash, data["password"]):
        session["user_id"] = user.id
        session["role"] = user.role
        session.permanent = True  # persist login across refresh
        return jsonify({"email": user.email, "role": user.role}), 200
    return jsonify({"error": "Invalid credentials"}), 401

# -----------------------------
# Logout route
# -----------------------------
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

# -----------------------------
# Get current user (optional)
# -----------------------------

@auth_bp.route("/current_user", methods=["GET"])
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(None), 200
    user = User.query.get(user_id)
    return jsonify({"email": user.email, "role": user.role}), 200