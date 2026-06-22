# backend/api/routes/__init__.py
"""
API route blueprints for WALLET-TRUST.

Exports all route blueprints for registration in app factory.
"""

from .health import health_bp
from .auth import auth_bp
from .users import users_bp
from .documents import documents_bp
from .blockchain import blockchain_bp
from .company import company_bp

__all__ = [
    'health_bp',
    'auth_bp',
    'users_bp',
    'documents_bp',
    'blockchain_bp',
    'company_bp'
]
