from flask import Flask, request, jsonify, session
from flask_cors import CORS
from functools import wraps
from datetime import timedelta
import re

from config import db
from models import User, Post, Comment, Reaction, Category, AdminResponse

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your_secret_key"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)



app.config["SESSION_COOKIE_NAME"] = "campus_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = False  # must be False on HTTP
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # safer for localhost

CORS(app, supports_credentials=True,
     origins=["http://localhost:5173", "http://127.0.0.1:5173"])

db.init_app(app)

@app.before_request
def make_session_permanent():
    session.permanent = True

# ---------------- DECORATORS ----------------
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

# ---------------- AUTH ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
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
    return {"user": {"email": user.email, "role": user.role}}, 201

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()
    if user and user.check_password(data.get("password")):
        session["user_id"] = user.id
        session["role"] = user.role
        return {"user": {"email": user.email, "role": user.role}}, 200
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
    return {"email": user.email, "role": user.role}

# ---------------- CATEGORIES ----------------
@app.route("/api/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in categories])

# ---------------- POSTS ----------------
@app.route("/api/posts", methods=["GET"])
def get_posts():
    category_id = request.args.get("category_id", type=int)
    query = Post.query.order_by(Post.created_at.desc())
    if category_id:
        query = query.filter_by(category_id=category_id)

    posts = query.all()
    data = []
    for p in posts:
        likes = sum(1 for r in p.reactions if r.reaction_type=="like")
        dislikes = sum(1 for r in p.reactions if r.reaction_type=="dislike")
        admin_response = p.admin_responses[0].content if p.admin_responses else None
        data.append({
            "id": p.id,
            "content": p.content,
            "category_id": p.category_id,
            "category_name": p.category.name,
            "user_id": p.user_id,
            "created_at": p.created_at,
            "likes": likes,
            "dislikes": dislikes,
            "comments_count": len(p.comments),
            "admin_response": admin_response
        })
    return jsonify(data)

@app.route("/api/posts/<int:id>", methods=["GET"])
def get_post(id):
    post = Post.query.get_or_404(id)
    likes = sum(1 for r in post.reactions if r.reaction_type=="like")
    dislikes = sum(1 for r in post.reactions if r.reaction_type=="dislike")
    user_reaction = None
    if session.get("user_id"):
        r = Reaction.query.filter_by(post_id=id, user_id=session["user_id"]).first()
        if r: user_reaction = r.reaction_type
    return {
        "id": post.id,
        "content": post.content,
        "category_id": post.category_id,
        "user_id": post.user_id,
        "created_at": post.created_at,
        "likes": likes,
        "dislikes": dislikes,
        "user_reaction": user_reaction,
        "comments": [{"id": c.id, "content": c.content, "user_id": c.user_id, "created_at": c.created_at} for c in post.comments],
        "admin_response": post.admin_responses[0].content if post.admin_responses else None
    }

@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    if not data.get("content"):
        return {"error": "Content required"}, 400
    post = Post(content=data["content"], user_id=session["user_id"], category_id=data["category_id"])
    db.session.add(post)
    db.session.commit()
    return {"id": post.id}, 201

# ---------------- COMMENTS ----------------
@app.route("/api/comments", methods=["POST"])
def add_comment():
    data = request.get_json()
    comment = Comment(
        content=data["content"],
        post_id=data["post_id"],
        user_id=session.get("user_id")  # None if anonymous
    )
    db.session.add(comment)
    db.session.commit()
    return {"id": comment.id}, 201

@app.route("/api/comments/<int:post_id>", methods=["GET"])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at).all()
    return jsonify([{"id": c.id,"content": c.content,"user_id": c.user_id,"created_at": c.created_at} for c in comments])

# ---------------- REACTIONS ----------------
@app.route("/api/reactions", methods=["POST"])
def add_reaction():
    data = request.get_json()
    post_id = data["post_id"]
    reaction_type = data["reaction_type"]
    existing = Reaction.query.filter_by(post_id=post_id,user_id=session["user_id"]).first()
    if existing:
        existing.reaction_type = reaction_type
    else:
        db.session.add(Reaction(post_id=post_id,user_id=session["user_id"],reaction_type=reaction_type))
    db.session.commit()
    reactions = Reaction.query.filter_by(post_id=post_id).all()
    return {
        "likes": sum(1 for r in reactions if r.reaction_type=="like"),
        "dislikes": sum(1 for r in reactions if r.reaction_type=="dislike"),
        "user_reaction": reaction_type
    }

# ---------------- ADMIN ----------------
@app.route("/api/admin/responses", methods=["POST"])
@admin_required
def respond_post():
    data = request.get_json()
    response = AdminResponse(post_id=data["post_id"], admin_id=session["user_id"], content=data["content"])
    db.session.add(response)
    db.session.commit()
    return {"message": "Admin response saved"}, 201

@app.route("/api/admin/posts/pending", methods=["GET"])
@admin_required
def pending_posts():
    posts = Post.query.all()
    return jsonify([{"id": p.id,"content": p.content,"created_at": p.created_at} for p in posts if not p.admin_responses])

# ---------------- ANALYTICS ----------------
@app.route("/api/analytics/categories")
def category_chart():
    return jsonify([{"name": c.name,"count": Post.query.filter_by(category_id=c.id).count()} for c in Category.query.all()])

@app.route("/api/analytics/votes")
def votes_chart():
    posts = Post.query.all()
    return jsonify([{"title": p.content[:20]+("..." if len(p.content)>20 else ""), "likes": sum(1 for r in p.reactions if r.reaction_type=="like"), "dislikes": sum(1 for r in p.reactions if r.reaction_type=="dislike")} for p in posts])

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
