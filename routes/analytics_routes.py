from flask import Blueprint, jsonify
from config import db
from models.post import Post
from models.category import Category
from models.reaction import Reaction

analytics_bp = Blueprint("analytics", __name__)

# Category chart: number of posts per category
@analytics_bp.route("/analytics/categories", methods=["GET"])
def category_chart():
    categories = Category.query.all()
    data = []
    for c in categories:
        count = Post.query.filter_by(category_id=c.id).count()
        data.append({
            "name": c.name,
            "count": count
        })
    return jsonify(data), 200

# Votes chart: likes and dislikes per post
@analytics_bp.route("/analytics/votes", methods=["GET"])
def votes_chart():
    posts = Post.query.all()
    data = []
    for p in posts:
        reactions = Reaction.query.filter_by(post_id=p.id).all()
        likes = sum(1 for r in reactions if r.reaction_type == "like")
        dislikes = sum(1 for r in reactions if r.reaction_type == "dislike")
        data.append({
            "title": p.content[:20] + ("..." if len(p.content) > 20 else ""),
            "likes": likes,
            "dislikes": dislikes
        })
    return jsonify(data), 200
