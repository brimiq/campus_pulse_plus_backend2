from flask import Flask, session
from config import db
from routes.auth_routes import auth_bp
from routes.post_routes import post_bp
from routes.comment_routes import comment_bp
from routes.reaction_routes import reaction_bp
from routes.admin_routes import admin_bp
from routes.analytics_routes import analytics_bp
from routes.category_routes import category_bp

app = Flask(__name__)


    
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 7  # 7 days

db.init_app(app)

    # Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(post_bp, url_prefix="/api")
app.register_blueprint(comment_bp, url_prefix="/api")
app.register_blueprint(reaction_bp, url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api")
app.register_blueprint(analytics_bp, url_prefix="/api")
app.register_blueprint(category_bp, url_prefix="/api")

@app.before_request
def make_session_permanent():
    session.permanent = True

    return app

if __name__ == "__main__":
    app.run(debug=True)
