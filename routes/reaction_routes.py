from flask import Blueprint, request, jsonify, session
from config import db
from models.reaction import Reaction
from functools import wraps

reaction_bp = Blueprint("reaction", __name__)

# Student login required decorator
def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "student":
            return jsonify({"error": "Only students can react"}), 403
        return f(*args, **kwargs)
    return decorated

# Add or update a reaction
@reaction_bp.route("/reactions", methods=["POST"])
@student_required
def add_reaction():
    data = request.get_json()
    post_id = data.get("post_id")
    reaction_type = data.get("reaction_type")  # "like" or "dislike"
    user_id = session.get("user_id")

    if not post_id or reaction_type not in ["like", "dislike"]:
        return jsonify({"error": "Invalid data"}), 400

    # Check if user already reacted
    existing = Reaction.query.filter_by(post_id=post_id, user_id=user_id).first()
    if existing:
        existing.reaction_type = reaction_type  # Update existing reaction
    else:
        new_reaction = Reaction(post_id=post_id, user_id=user_id, reaction_type=reaction_type)
        db.session.add(new_reaction)

    db.session.commit()

    # Return updated counts
    reactions = Reaction.query.filter_by(post_id=post_id).all()
    likes = sum(1 for r in reactions if r.reaction_type == "like")
    dislikes = sum(1 for r in reactions if r.reaction_type == "dislike")

    return jsonify({
        "likes": likes,
        "dislikes": dislikes,
        "user_reaction": reaction_type
    }), 201
