# backend/app_factory.py
"""
Flask application factory for WALLET-TRUST backend.

Creates and configures Flask app with all security middleware and error handlers.
"""

import logging
import os
import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from flask import Flask

from config import config
from models import db
from api.middleware import (
    configure_cors,
    create_limiter,
    add_security_headers,
    setup_request_tracking,
    configure_error_handlers
)

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _ensure_mysql_database_exists(database_uri: str) -> None:
    """Create the MySQL database if missing (dev convenience).

    This is only called when AUTO_CREATE_DATABASE is enabled.
    """
    url = make_url(database_uri)
    if not url.drivername.startswith("mysql"):
        return

    db_name = url.database
    if not db_name:
        return

    if not re.fullmatch(r"[A-Za-z0-9_]+", db_name):
        raise RuntimeError("Invalid MYSQL_DB name; use only letters, numbers, underscore")

    server_url = url.set(database=None)
    engine = create_engine(server_url, future=True, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            conn.commit()
    finally:
        engine.dispose()


def create_app():
    """
    Application factory function.
    
    Creates and configures Flask app with:
    - CORS security
    - Rate limiting
    - Security headers
    - Error handlers
    - Request logging
    
    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__)
    
    # Apply configuration
    app.config.from_object(config)
    logger.info(f"Using {type(config).__name__} configuration")

    # Optional: auto-create MySQL schema/database
    if _truthy(os.getenv("AUTO_CREATE_DATABASE")):
        _ensure_mysql_database_exists(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    
    # Initialize database
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        logger.info("Database tables initialized")
    
    # Configure CORS
    configure_cors(app)
    
    # Create rate limiter
    limiter = create_limiter(app)
    app.limiter = limiter
    
    # Add security headers
    add_security_headers(app)
    
    # Setup request tracking
    setup_request_tracking(app)
    
    # Configure error handlers
    configure_error_handlers(app)
    
    # Register blueprints (modular routes)
    from api.routes import health_bp, auth_bp, users_bp, documents_bp, blockchain_bp, company_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    
    logger.info("Flask application initialized successfully")
    
    return app
