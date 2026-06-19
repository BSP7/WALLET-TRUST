# backend/api/routes/auth.py
"""
Authentication routes for WALLET-TRUST.

Handles user registration, login, token refresh, and logout.
"""

import logging
import time
from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError
from datetime import datetime

from api.schemas import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    ErrorResponse
)
from auth.jwt_handler import JWTHandler, require_auth
from core.crypto import CryptoManager
from config import config
from db_service import UserService

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Lazy-initialize crypto manager (key is loaded from environment)
_crypto_manager = None

def get_crypto_manager():
    """Get or initialize the crypto manager."""
    global _crypto_manager
    if _crypto_manager is None:
        if not config.ENCRYPTION_KEY:
            raise RuntimeError("ENCRYPTION_KEY not configured")
        _crypto_manager = CryptoManager(config.ENCRYPTION_KEY)
    return _crypto_manager


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Request body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "phone": "+1-555-0100",
        "dob": "1990-01-15"
    }
    
    Returns:
        - 201:Successfully created user with tokens
        - 400: Validation error
        - 409: User already exists
        - 500: Server error
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body required',
                'error_code': 'INVALID_REQUEST'
            }), 400
        
        try:
            req = UserRegistrationRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'error_code': 'VALIDATION_ERROR',
                'details': {field: str(err) for field, err in e.errors()}
            }), 400
        
        # Check if user exists in database
        existing_user = UserService.get_user_by_email(req.email)
        if existing_user:
            return jsonify({
                'error': 'User already exists',
                'error_code': 'USER_EXISTS'
            }), 409
        
        # Hash password
        crypto_mgr = get_crypto_manager()
        password_salt = crypto_mgr.generate_salt()
        password_hash = crypto_mgr.hash_password_with_salt(req.password, password_salt)
        
        # Create user ID
        user_id = f"user_{int(time.time())}_{crypto_mgr.generate_salt()[:8]}"
        
        # Save user to database
        try:
            user = UserService.create_user(
                user_id=user_id,
                name=req.name,
                email=req.email,
                password_hash=password_hash,
                password_salt=password_salt,
                phone=req.phone,
                dob=req.dob
            )
        except Exception as e:
            logger.error(f"Database error creating user: {e}", exc_info=True)
            return jsonify({
                'error': 'Failed to create user',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        # Generate tokens
        access_token = JWTHandler.create_access_token({
            'user_id': user.id,
            'email': user.email
        })
        
        refresh_token = JWTHandler.create_refresh_token({
            'user_id': user.id,
            'email': user.email
        })
        
        logger.info(f"User registered successfully: {user.id}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'user_id': user.id,
                'name': user.name,
                'email': user.email
            },
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': config.JWT_EXPIRATION_HOURS * 3600
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({
            'error': 'Registration failed',
            'error_code': 'REGISTRATION_ERROR'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and return authentication tokens.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    
    Returns:
        - 200: Successfully logged in with tokens
        - 400: Validation error
        - 401: Invalid credentials
        - 500: Server error
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body required',
                'error_code': 'INVALID_REQUEST'
            }), 400
        
        try:
            req = UserLoginRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'error_code': 'VALIDATION_ERROR'
            }), 400
        
        # Fetch user from database
        user = UserService.get_user_by_email(req.email)
        
        if not user:
            return jsonify({
                'error': 'Invalid credentials',
                'error_code': 'INVALID_CREDENTIALS'
            }), 401
        
        # Verify password
        crypto_mgr = get_crypto_manager()
        if not crypto_mgr.verify_password_with_salt(req.password, user.password_hash, user.password_salt):
            return jsonify({
                'error': 'Invalid credentials',
                'error_code': 'INVALID_CREDENTIALS'
            }), 401
        
        # Generate tokens
        access_token = JWTHandler.create_access_token({
            'user_id': user.id,
            'email': user.email
        })
        
        refresh_token = JWTHandler.create_refresh_token({
            'user_id': user.id,
            'email': user.email
        })
        
        logger.info(f"User logged in: {user.id}")
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'user_id': user.id,
                'email': user.email
            },
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': config.JWT_EXPIRATION_HOURS * 3600
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({
            'error': 'Login failed',
            'error_code': 'LOGIN_ERROR'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token.
    
    Request body:
    {
        "refresh_token": "eyJhbGc..."
    }
    
    Returns:
        - 200: New access token
        - 400: Validation error
        - 401: Invalid refresh token
        - 500: Server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Request body required',
                'error_code': 'INVALID_REQUEST'
            }), 400
        
        try:
            req = TokenRefreshRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'error_code': 'VALIDATION_ERROR'
            }), 400
        
        # Verify refresh token
        try:
            payload = JWTHandler.verify_token(req.refresh_token)
            
            if payload.get('type') != 'refresh':
                return jsonify({
                    'error': 'Invalid token type',
                    'error_code': 'INVALID_TOKEN'
                }), 401
            
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            return jsonify({
                'error': 'Invalid or expired refresh token',
                'error_code': 'INVALID_TOKEN'
            }), 401
        
        # Create new access token
        new_access_token = JWTHandler.create_access_token({
            'user_id': payload['user_id'],
            'email': payload.get('email')
        })
        
        logger.info(f"Token refreshed for user: {payload['user_id']}")
        
        return jsonify({
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': config.JWT_EXPIRATION_HOURS * 3600
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'error': 'Token refresh failed',
            'error_code': 'REFRESH_ERROR'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user (invalidate tokens).
    
    Requires: Authorization header with valid JWT
    
    Returns:
        - 200: Successfully logged out
        - 401: Unauthorized
        - 500: Server error
    """
    try:
        user_id = g.user_id
        
        logger.info(f"User logged out: {user_id}")
        
        return jsonify({
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'error': 'Logout failed',
            'error_code': 'LOGOUT_ERROR'
        }), 500


@auth_bp.route('/validate', methods=['POST'])
@require_auth
def validate_token():
    """
    Validate current access token.
    
    Requires: Authorization header with valid JWT
    
    Returns:
        - 200: Token is valid with user info
        - 401: Unauthorized
    """
    try:
        return jsonify({
            'valid': True,
            'user_id': g.user_id,
            'email': g.user_email
        }), 200
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return jsonify({
            'valid': False,
            'error': 'Token validation failed'
        }), 401
