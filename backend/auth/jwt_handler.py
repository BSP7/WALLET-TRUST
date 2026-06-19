# backend/auth/jwt_handler.py
"""
Production-grade JWT authentication handler for WALLET-TRUST.

Implements secure token generation, validation, and refresh mechanisms
without any fallback or bypass logic.
"""

import logging
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, g

from config import config

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handles JWT token generation, validation, and refresh."""
    
    ALGORITHM = config.JWT_ALGORITHM
    SECRET = config.JWT_SECRET
    ACCESS_EXPIRATION = config.JWT_EXPIRATION_HOURS
    REFRESH_EXPIRATION = config.JWT_REFRESH_EXPIRATION_DAYS
    
    @staticmethod
    def validate_secret():
        """Validate JWT secret is configured properly."""
        if not JWTHandler.SECRET:
            raise ValueError("JWT_SECRET environment variable not set")
        if len(JWTHandler.SECRET) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
    
    @classmethod
    def create_access_token(cls, user_data: Dict[str, Any]) -> str:
        """
        Create a short-lived access token.
        
        Args:
            user_data: Dictionary with at minimum 'user_id' key
            
        Returns:
            JWT access token
            
        Raises:
            ValueError: If user_data invalid
        """
        if not isinstance(user_data, dict) or 'user_id' not in user_data:
            raise ValueError("user_data must be dict with 'user_id' key")
        
        payload = {
            'user_id': user_data['user_id'],
            'email': user_data.get('email'),
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=cls.ACCESS_EXPIRATION)
        }
        
        try:
            token = jwt.encode(payload, cls.SECRET, algorithm=cls.ALGORITHM)
            logger.debug(f"Access token created for user: {user_data['user_id']}")
            return token
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise
    
    @classmethod
    def create_refresh_token(cls, user_data: Dict[str, Any]) -> str:
        """
        Create a long-lived refresh token.
        
        Args:
            user_data: Dictionary with at minimum 'user_id' key
            
        Returns:
            JWT refresh token
            
        Raises:
            ValueError: If user_data invalid
        """
        if not isinstance(user_data, dict) or 'user_id' not in user_data:
            raise ValueError("user_data must be dict with 'user_id' key")
        
        payload = {
            'user_id': user_data['user_id'],
            'email': user_data.get('email'),
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=cls.REFRESH_EXPIRATION)
        }
        
        try:
            token = jwt.encode(payload, cls.SECRET, algorithm=cls.ALGORITHM)
            logger.debug(f"Refresh token created for user: {user_data['user_id']}")
            return token
        except Exception as e:
            logger.error(f"Refresh token creation failed: {e}")
            raise
    
    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload
            
        Raises:
            jwt.InvalidTokenError: If token invalid or expired
            jwt.ExpiredSignatureError: If token expired
        """
        try:
            payload = jwt.decode(token, cls.SECRET, algorithms=[cls.ALGORITHM])
            logger.debug(f"Token verified for user: {payload.get('user_id')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise
    
    @classmethod
    def extract_token_from_header(cls, headers: Dict[str, str]) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            headers: HTTP headers dict
            
        Returns:
            Token string or None if not present/invalid format
        """
        auth_header = headers.get('Authorization', '')
        
        if not auth_header:
            return None
        
        try:
            scheme, token = auth_header.split(' ')
            if scheme.lower() != 'bearer':
                return None
            return token
        except ValueError:
            return None


def require_auth(f):
    """
    Decorator to require JWT authentication.
    
    Validates token and adds user_id to request context.
    Returns 401 if token missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = JWTHandler.extract_token_from_header(request.headers)
        
        if not token:
            logger.warning(f"Missing authorization token for {request.path}")
            return jsonify({'error': 'Authorization required'}), 401
        
        try:
            payload = JWTHandler.verify_token(token)
            
            # Verify token type
            if payload.get('type') != 'access':
                logger.warning(f"Invalid token type: {payload.get('type')}")
                return jsonify({'error': 'Invalid token type'}), 401
            
            # Store user_id in request context
            g.user_id = payload['user_id']
            g.user_email = payload.get('email')
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token presented")
            return jsonify({'error': 'Token expired. Please refresh.'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin privileges.
    
    Validates token and checks admin role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = JWTHandler.extract_token_from_header(request.headers)
        
        if not token:
            return jsonify({'error': 'Authorization required'}), 401
        
        try:
            payload = JWTHandler.verify_token(token)
            
            # Check admin role
            if payload.get('role') != 'admin':
                logger.warning(f"Unauthorized admin access attempt by user: {payload.get('user_id')}")
                return jsonify({'error': 'Admin privileges required'}), 403
            
            g.user_id = payload['user_id']
            g.is_admin = True
            
            return f(*args, **kwargs)
            
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Admin auth error: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    return decorated_function
