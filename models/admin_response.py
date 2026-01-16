from config import db
from datetime import datetime

class AdminResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    post = db.relationship("Post", back_populates="admin_responses")
    admin = db.relationship("User", back_populates="admin_responses")
