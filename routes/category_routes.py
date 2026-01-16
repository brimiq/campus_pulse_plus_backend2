from flask import Blueprint, jsonify
from models.category import Category

category_bp = Blueprint("category", __name__)

@category_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in categories]), 200
