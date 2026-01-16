from flask import Blueprint, request, jsonify, session
from config import db
from models.comment import Comment
from functools import wraps

comment_bp = Blueprint("comment", __name__)

# Student login required decorator
def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "student":
            return jsonify({"error": "Only students can comment"}), 403
        return f(*args, **kwargs)
    return decorated

# Add a comment
@comment_bp.route("/comments", methods=["POST"])
@student_required
def add_comment():
    data = request.get_json()
    post_id = data.get("post_id")
    content = data.get("content", "").strip()
    user_id = session.get("user_id")

    if not content:
        return jsonify({"error": "Comment content is required"}), 400
    if not post_id:
        return jsonify({"error": "Post ID is required"}), 400

    comment = Comment(content=content, post_id=post_id, user_id=user_id)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "id": comment.id,
        "content": comment.content,
        "user_id": comment.user_id,
        "created_at": comment.created_at
    }), 201

# Get all comments for a post
@comment_bp.route("/comments/<int:post_id>", methods=["GET"])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    data = [{
        "id": c.id,
        "content": c.content,
        "user_id": c.user_id,
        "created_at": c.created_at
    } for c in comments]
    return jsonify(data), 200
