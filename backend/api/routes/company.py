# backend/api/routes/company.py
"""
Company routes for WALLET-TRUST.

Handles company registration, login, and validation history.
"""

import logging
import time
from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, ValidationError

from auth.jwt_handler import JWTHandler, require_auth
from core.crypto import CryptoManager
from config import config
from db_service import CompanyService, ValidationService

company_bp = Blueprint('company', __name__)
logger = logging.getLogger(__name__)

_crypto_manager = None

def get_crypto_manager():
    global _crypto_manager
    if _crypto_manager is None:
        if not config.ENCRYPTION_KEY:
            raise RuntimeError("ENCRYPTION_KEY not configured")
        _crypto_manager = CryptoManager(config.ENCRYPTION_KEY)
    return _crypto_manager

class CompanyRegistrationRequest(BaseModel):
    company_name: str
    email: str
    password: str

class CompanyLoginRequest(BaseModel):
    email: str
    password: str

@company_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        try:
            req = CompanyRegistrationRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400
        
        existing = CompanyService.get_company_by_email(req.email)
        if existing:
            return jsonify({'error': 'Company already exists'}), 409
        
        crypto_mgr = get_crypto_manager()
        password_salt = crypto_mgr.generate_salt()
        password_hash = crypto_mgr.hash_password_with_salt(req.password, password_salt)
        
        company_id = f"comp_{int(time.time())}_{crypto_mgr.generate_salt()[:8]}"
        
        company = CompanyService.create_company(
            company_id=company_id,
            company_name=req.company_name,
            email=req.email,
            password_hash=password_hash,
            password_salt=password_salt
        )
        
        access_token = JWTHandler.create_access_token({
            'user_id': company.id,
            'email': company.email,
            'role': 'company'
        })
        
        return jsonify({
            'message': 'Company registered successfully',
            'company': {
                'id': company.id,
                'company_name': company.company_name,
                'email': company.email
            },
            'access_token': access_token,
            'token_type': 'Bearer'
        }), 201
    except Exception as e:
        logger.error(f"Company registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@company_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        try:
            req = CompanyLoginRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400
        
        company = CompanyService.get_company_by_email(req.email)
        if not company:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        crypto_mgr = get_crypto_manager()
        if not crypto_mgr.verify_password_with_salt(req.password, company.password_hash, company.password_salt):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        access_token = JWTHandler.create_access_token({
            'user_id': company.id,
            'email': company.email,
            'role': 'company'
        })
        
        return jsonify({
            'message': 'Login successful',
            'company': {
                'id': company.id,
                'company_name': company.company_name,
                'email': company.email
            },
            'access_token': access_token,
            'token_type': 'Bearer'
        }), 200
    except Exception as e:
        logger.error(f"Company login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@company_bp.route('/validations', methods=['GET'])
@require_auth
def get_validations():
    try:
        company_id = g.user_id
        validations = ValidationService.get_validations_by_company(company_id)
        
        return jsonify({
            'validations': [v.to_dict() for v in validations]
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch validations: {e}")
        return jsonify({'error': 'Failed to fetch validations'}), 500
