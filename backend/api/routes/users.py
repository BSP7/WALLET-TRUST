# backend/api/routes/users.py
"""
User management routes for WALLET-TRUST.
"""

import logging
from flask import Blueprint, jsonify, g, request
from pydantic import ValidationError

from api.schemas import UserProfileUpdateRequest
from auth.jwt_handler import require_auth
from db_service import UserService, TokenService, DocumentService

users_bp = Blueprint('users', __name__)
logger = logging.getLogger(__name__)


@users_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get authenticated user's profile.
    
    Returns:
        - 200: User profile data
        - 401: Unauthorized
        - 404: User not found
    """
    try:
        user_id = g.user_id
        
        # Fetch user profile from database
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


@users_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update authenticated user's profile.
    
    Returns:
        - 200: Profile updated
        - 400: Validation error
        - 401: Unauthorized
        - 500: Server error
    """
    try:
        user_id = g.user_id

        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        try:
            req = UserProfileUpdateRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.errors()
            }), 400

        update_fields = req.dict(exclude_unset=True)
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        if 'email' in update_fields and update_fields['email'] is not None:
            existing = UserService.get_user_by_email(update_fields['email'])
            if existing and existing.id != user_id:
                return jsonify({'error': 'Email already in use'}), 409

        user = UserService.update_user(user_id, **update_fields)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500


@users_bp.route('/tokens', methods=['GET'])
@require_auth
def get_tokens():
    """
    Get all tokens for authenticated user.
    
    Returns:
        - 200: List of user tokens
        - 401: Unauthorized
    """
    try:
        user_id = g.user_id
        
        # Fetch tokens from database
        tokens = TokenService.get_tokens_by_user(user_id)
        
        return jsonify({
            'tokens': [token.to_dict() for token in tokens]
        }), 200
        
    except Exception as e:
        logger.error(f"Tokens fetch error: {e}")
        return jsonify({'error': 'Failed to fetch tokens'}), 500


@users_bp.route('/documents', methods=['GET'])
@require_auth
def get_documents():
    """
    Get all documents for authenticated user.
    
    Returns:
        - 200: List of user documents
        - 401: Unauthorized
    """
    try:
        user_id = g.user_id
        
        # Fetch documents from database
        documents = DocumentService.get_documents_by_user(user_id)
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents]
        }), 200
        
    except Exception as e:
        logger.error(f"Documents fetch error: {e}")
        return jsonify({'error': 'Failed to fetch documents'}), 500
