from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import db


# ======================
# USER
# ======================
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default="student")  # student | admin

    posts = db.relationship(
        "Post", back_populates="user", cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )
    reactions = db.relationship(
        "Reaction", back_populates="user", cascade="all, delete-orphan"
    )
    admin_responses = db.relationship(
        "AdminResponse", back_populates="admin", cascade="all, delete-orphan"
    )

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


# ======================
# CATEGORY
# ======================
class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)

    posts = db.relationship("Post", back_populates="category")


# ======================
# POST
# ======================
class Post(db.Model):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    user = db.relationship("User", back_populates="posts")
    category = db.relationship("Category", back_populates="posts")

    comments = db.relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    reactions = db.relationship(
        "Reaction", back_populates="post", cascade="all, delete-orphan"
    )
    admin_responses = db.relationship(
        "AdminResponse", back_populates="post", cascade="all, delete-orphan"
    )


# ======================
# COMMENT
# ======================
class Comment(db.Model):
    __tablename__ = "comment"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))

    user = db.relationship("User", back_populates="comments")
    post = db.relationship("Post", back_populates="comments")


# ======================
# REACTION
# ======================
class Reaction(db.Model):
    __tablename__ = "reaction"

    id = db.Column(db.Integer, primary_key=True)
    reaction_type = db.Column(db.String(10), nullable=False)  # like | dislike
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))

    user = db.relationship("User", back_populates="reactions")
    post = db.relationship("Post", back_populates="reactions")


# ======================
# ADMIN RESPONSE
# ======================
class AdminResponse(db.Model):
    __tablename__ = "admin_response"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    post = db.relationship("Post", back_populates="admin_responses")
    admin = db.relationship("User", back_populates="admin_responses")
