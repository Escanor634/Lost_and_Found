"""Campus Lost & Found Flask Application Package.

Implements the application factory pattern and registers modular blueprints.
"""
import os
from datetime import datetime, timezone
import click
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_login import login_required

from sqlite3 import Connection as SQLite3Connection
from sqlalchemy import event
from sqlalchemy.engine import Engine

from config import Config, config_by_name
from app.extensions import db, migrate, login_manager, csrf
from app.auth import auth_bp
from app.items import items_bp
from app.claims import claims_bp
from app.notifications import notifications_bp
from app.admin import admin_bp
from app import models  # Ensure models are loaded into db.metadata


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite foreign key constraints on connection."""
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(config_name_or_class=None):
    """Application factory for Campus Lost & Found.

    Args:
        config_name_or_class: Configuration name string ('development', 'testing',
            'production') or a Config class. Defaults to FLASK_CONFIG env var or 'default'.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Resolve configuration
    if config_name_or_class is None:
        env_config = os.getenv("FLASK_CONFIG") or os.getenv("FLASK_ENV")
        if not env_config:
            env_config = "production" if os.getenv("RENDER") else "default"
        config_obj = config_by_name.get(env_config, Config)
        app.config.from_object(config_obj)
    elif isinstance(config_name_or_class, str):
        config_obj = config_by_name.get(config_name_or_class, Config)
        app.config.from_object(config_obj)
    else:
        app.config.from_object(config_name_or_class)

    # Ensure live environment SECRET_KEY is always respected
    if os.getenv("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Ensure instance and upload folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    if app.config.get("UPLOAD_FOLDER"):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        try:
            return db.session.get(models.User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Register modular blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)

    # Context processors
    @app.context_processor
    def inject_template_globals():
        return {
            "now_year": datetime.now(timezone.utc).year
        }

    # Core routes
    @app.route("/")
    def index():
        """Render application homepage."""
        return render_template("index.html")

    @app.route("/dashboard")
    @login_required
    def dashboard_redirect():
        """Convenience redirect to auth dashboard."""
        return redirect(url_for("auth.dashboard"))

    @app.route("/profile")
    @login_required
    def profile_redirect():
        """Convenience redirect to auth profile."""
        return redirect(url_for("auth.profile"))

    @app.route("/health", methods=["GET"])
    def health_check():
        """Return application health status."""
        return jsonify({
            "status": "healthy",
            "service": "campus-lost-and-found"
        }), 200

    # Database initialization CLI command
    @app.cli.command("init-db")
    def init_db_command():
        """CLI command to initialize the SQLite database tables."""
        init_db(app)
        click.echo("Initialized database tables successfully.")

    return app


def init_db(app=None):
    """Initialize database tables within application context."""
    if app is None:
        app = create_app()

    with app.app_context():
        db.create_all()
