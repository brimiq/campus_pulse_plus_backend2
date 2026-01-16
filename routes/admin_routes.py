from flask import Blueprint, request, jsonify, session
from config import db
from models.admin_response import AdminResponse
from models.post import Post
from functools import wraps

admin_bp = Blueprint("admin", __name__)

# Admin login required decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "admin":
            return jsonify({"error": "Only admins can perform this action"}), 403
        return f(*args, **kwargs)
    return decorated

# Add or update admin response
@admin_bp.route("/admin/responses", methods=["POST"])
@admin_required
def respond_post():
    data = request.get_json()
    post_id = data.get("post_id")
    content = data.get("content", "").strip()
    admin_id = session.get("user_id")

    if not post_id or not content:
        return jsonify({"error": "Post ID and content are required"}), 400

    post = Post.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # Check if admin response exists
    existing = AdminResponse.query.filter_by(post_id=post_id).first()
    if existing:
        existing.content = content
    else:
        new_response = AdminResponse(post_id=post_id, admin_id=admin_id, content=content)
        db.session.add(new_response)

    db.session.commit()

    response = AdminResponse.query.filter_by(post_id=post_id).first()

    return jsonify({
        "post_id": post_id,
        "content": response.content,
        "created_at": response.created_at
    }), 201

# Get all posts needing response
@admin_bp.route("/admin/posts/pending", methods=["GET"])
@admin_required
def get_pending_posts():
    posts = Post.query.all()
    pending = []
    for p in posts:
        existing = AdminResponse.query.filter_by(post_id=p.id).first()
        if not existing:
            pending.append({
                "id": p.id,
                "content": p.content,
                "category_id": p.category_id,
                "user_id": p.user_id,
                "created_at": p.created_at
            })
    return jsonify(pending), 200
