from flask import Blueprint, request, jsonify, session
from config import db
from models.post import Post
from models.category import Category
from models.user import User
from models.reaction import Reaction
from models.comment import Comment
from models.admin_response import AdminResponse
from functools import wraps

post_bp = Blueprint("post", __name__)

# Student login required decorator
def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "student":
            return jsonify({"error": "Only students can perform this action"}), 403
        return f(*args, **kwargs)
    return decorated

# Get all posts (for homepage)
@post_bp.route("/posts", methods=["GET"])
def get_posts():
    category_id = request.args.get("category_id", type=int)
    posts_query = Post.query.order_by(Post.id.desc())
    if category_id:
        posts_query = posts_query.filter_by(category_id=category_id)

    posts = posts_query.all()
    data = []
    for p in posts:
        reactions = Reaction.query.filter_by(post_id=p.id).all()
        likes = sum(1 for r in reactions if r.reaction_type == "like")
        dislikes = sum(1 for r in reactions if r.reaction_type == "dislike")
        comments_count = Comment.query.filter_by(post_id=p.id).count()
        admin_response = AdminResponse.query.filter_by(post_id=p.id).first()
        data.append({
            "id": p.id,
            "content": p.content,
            "category_id": p.category_id,
            "user_id": p.user_id,
            "created_at": p.created_at,
            "likes": likes,
            "dislikes": dislikes,
            "comments_count": comments_count,
            "admin_response": admin_response.content if admin_response else None
        })
    return jsonify(data), 200

# Get single post (details)
@post_bp.route("/posts/<int:id>", methods=["GET"])
def get_post(id):
    post = Post.query.get_or_404(id)

    # Reactions
    reactions = Reaction.query.filter_by(post_id=post.id).all()
    likes = sum(1 for r in reactions if r.reaction_type == "like")
    dislikes = sum(1 for r in reactions if r.reaction_type == "dislike")

    # User reaction
    user_reaction = None
    user_id = session.get("user_id")
    if user_id:
        user_react = Reaction.query.filter_by(post_id=post.id, user_id=user_id).first()
        if user_react:
            user_reaction = user_react.reaction_type

    # Comments
    comments = Comment.query.filter_by(post_id=post.id).all()
    comment_list = [{"id": c.id, "content": c.content, "user_id": c.user_id, "created_at": c.created_at} for c in comments]

    # Admin response
    admin_response = AdminResponse.query.filter_by(post_id=post.id).first()

    return jsonify({
        "id": post.id,
        "content": post.content,
        "category_id": post.category_id,
        "user_id": post.user_id,
        "created_at": post.created_at,
        "likes": likes,
        "dislikes": dislikes,
        "user_reaction": user_reaction,
        "comments": comment_list,
        "admin_response": {
            "content": admin_response.content if admin_response else None,
            "created_at": admin_response.created_at if admin_response else None
        }
    }), 200

# Create post (student only)
@post_bp.route("/posts", methods=["POST"])
@student_required
def create_post():
    data = request.get_json()
    content = data.get("content", "").strip()
    category_id = data.get("category_id")

    if not content:
        return jsonify({"error": "Content is required"}), 400
    if not category_id or not Category.query.get(category_id):
        return jsonify({"error": "Valid category is required"}), 400

    post = Post(content=content, user_id=session["user_id"], category_id=category_id)
    db.session.add(post)
    db.session.commit()

    return jsonify({
        "message": "Post created",
        "id": post.id,
        "content": post.content,
        "category_id": post.category_id,
        "user_id": post.user_id,
        "created_at": post.created_at,
        "likes": 0,
        "dislikes": 0,
        "comments_count": 0,
        "admin_response": None
    }), 201
