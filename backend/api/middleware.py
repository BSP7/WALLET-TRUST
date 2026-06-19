# backend/api/middleware.py
"""
Middleware components for WALLET-TRUST API.

Includes rate limiting, security headers, CORS configuration, and error handling.
"""

import logging
import json
from datetime import datetime
from flask import request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException

from config import config

logger = logging.getLogger(__name__)


# ============================================================
# RATE LIMITING
# ============================================================

def create_limiter(app):
    """
    Create and configure rate limiter.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Limiter instance
    """
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[config.RATELIMIT_DEFAULT],
        storage_uri=config.RATELIMIT_STORAGE_URL,
        strategy=config.RATELIMIT_STRATEGY
    )
    
    logger.info("Rate limiter configured")
    return limiter


# ============================================================
# CORS CONFIGURATION
# ============================================================

def configure_cors(app):
    """
    Configure CORS with secure settings.
    
    Args:
        app: Flask application instance
    """
    cors_config = {
        "origins": config.CORS_ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-Requested-With"
        ],
        "expose_headers": ["X-Total-Count", "X-Processing-Time"],
        "supports_credentials": True,
        "max_age": 3600
    }
    
    if not config.CORS_ALLOWED_ORIGINS:
        logger.warning("CORS_ALLOWED_ORIGINS is empty - using restrictive default")
        cors_config["origins"] = []
    
    CORS(app, resources={r"/api/*": cors_config})
    logger.info(f"CORS configured for origins: {config.CORS_ALLOWED_ORIGINS}")


# ============================================================
# SECURITY HEADERS
# ============================================================

def add_security_headers(app):
    """
    Add security headers to all responses.
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://sepolia.etherscan.io; "
            "frame-ancestors 'none'"
        )
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy
        response.headers['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "accelerometer=(), "
            "gyroscope=()"
        )
        
        # HSTS (only on HTTPS)
        if request.is_secure or config.ENVIRONMENT == 'production':
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        return response
    
    logger.info("Security headers configured")


# ============================================================
# REQUEST TRACKING & LOGGING
# ============================================================

def setup_request_tracking(app):
    """
    Setup request tracking and logging middleware.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        """Track request start time and generate request ID."""
        g.start_time = datetime.utcnow()
        g.request_id = get_remote_address().replace(':', '_')  # Simple request ID
        
        # Log request
        logger.info(
            f"[{g.request_id}] {request.method} {request.path} "
            f"from {get_remote_address()}"
        )
    
    @app.after_request
    def after_request(response):
        """Log response with timing information."""
        if hasattr(g, 'start_time'):
            elapsed_time = (datetime.utcnow() - g.start_time).total_seconds()
            response.headers['X-Processing-Time'] = str(elapsed_time)
            
            logger.info(
                f"[{g.request_id}] {request.method} {request.path} "
                f"returned {response.status_code} in {elapsed_time:.3f}s"
            )
        
        return response
    
    logger.info("Request tracking configured")


# ============================================================
# ERROR HANDLING
# ============================================================

def configure_error_handlers(app):
    """
    Configure global error handlers.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'error': 'Bad request',
            'error_code': 'BAD_REQUEST',
            'details': str(error),
            'timestamp': datetime.utcnow().timestamp()
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            'error': 'Unauthorized',
            'error_code': 'UNAUTHORIZED',
            'timestamp': datetime.utcnow().timestamp()
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            'error': 'Forbidden',
            'error_code': 'FORBIDDEN',
            'timestamp': datetime.utcnow().timestamp()
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'error': 'Not found',
            'error_code': 'NOT_FOUND',
            'timestamp': datetime.utcnow().timestamp()
        }), 404
    
    @app.errorhandler(413)
    def payload_too_large(error):
        """Handle 413 Payload Too Large errors."""
        return jsonify({
            'error': 'File too large. Maximum 10MB allowed.',
            'error_code': 'PAYLOAD_TOO_LARGE',
            'timestamp': datetime.utcnow().timestamp()
        }), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors."""
        return jsonify({
            'error': 'Rate limit exceeded. Please try again later.',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'timestamp': datetime.utcnow().timestamp()
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal server error',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'timestamp': datetime.utcnow().timestamp()
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle all unhandled exceptions."""
        if isinstance(error, HTTPException):
            # Return HTTP exception as-is
            return error
        
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        
        return jsonify({
            'error': 'Internal server error',
            'error_code': 'INTERNAL_SERVER_ERROR',
            'timestamp': datetime.utcnow().timestamp()
        }), 500
    
    logger.info("Error handlers configured")
