import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from backend.config.config import Config
from backend.database.db import db_session, init_db, close_db_session
from backend.models.token_blocklist import TokenBlocklist
from backend.routes.auth import auth_bp
from backend.routes.upload import upload_bp
from backend.routes.flashcards import flashcards_bp
from backend.routes.quiz import quiz_bp
from backend.routes.analytics import analytics_bp

def create_app(config_class=Config):
    """Application factory method to configure and return Flask instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure uploads target directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize JWT Manager
    jwt = JWTManager(app)

    # Register JWT Blocklist Loader
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = db_session.query(TokenBlocklist).filter_by(jti=jti).first()
        return token is not None

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(analytics_bp)

    # Register Database Session Teardown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        close_db_session(exception)

    # Initialize database tables on startup
    with app.app_context():
        init_db()

    return app

if __name__ == '__main__':
    app = create_app()
    # Runs the backend API server on port 5000 by default
    app.run(host='0.0.0.0', port=5000, debug=True)
