import os, logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from models.database import db, User
from routes.auth import auth_bp
from routes.detect import detect_bp
from routes.history import history_bp

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(name)s  %(message)s"
)


def create_app():
    app = Flask(__name__)

    # =========================
    # SECRET KEY
    # =========================
    app.config["SECRET_KEY"] = os.environ.get(
        "FLASK_SECRET_KEY",
        "dev-secret"
    )

    # =========================
    # POSTGRESQL DATABASE
    # =========================
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL belum dikonfigurasi")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # =========================
    # FILE UPLOAD
    # =========================
    app.config["MAX_CONTENT_LENGTH"] = (
        int(os.environ.get("MAX_CONTENT_LENGTH_MB", 10))
        * 1024
        * 1024
    )

    # =========================
    # SESSION COOKIE
    # =========================
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # =========================
    # CORS
    # =========================
    frontend_url = os.environ.get("FRONTEND_URL")

    if not frontend_url:
        raise RuntimeError("FRONTEND_URL belum dikonfigurasi")

    CORS(
        app,
        origins=[frontend_url],
        supports_credentials=True
    )

    # =========================
    # DATABASE
    # =========================
    db.init_app(app)
    Migrate(app, db)

    # =========================
    # LOGIN MANAGER
    # =========================
    login_manager = LoginManager(app)
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({
            "error": "Authentication required"
        }), 401

    # =========================
    # BLUEPRINTS
    # =========================
    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(
        detect_bp,
        url_prefix="/api"
    )

    app.register_blueprint(
        history_bp,
        url_prefix="/api/history"
    )

    # =========================
    # HEALTH CHECK
    # =========================
    @app.route("/api/health")
    def health():
        from utils.model import _load_model

        model = _load_model()

        if model is None:
            return jsonify({
                "status": "error",
                "version": "1.0.0",
                "model": "unavailable"
            }), 500

        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "model": "live"
        })

    # =========================
    # ERROR HANDLERS
    # =========================
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            "error": "Not found"
        }), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({
            "error": "File too large"
        }), 413

    # =========================
    # CREATE DATABASE TABLES
    # =========================
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5001)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )