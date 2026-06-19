# backend/api/routes/health.py
"""
Health check and system status endpoints.

Provides endpoints to verify:
- API service status
- Database connectivity
- Blockchain connectivity
- Filebase storage connectivity
"""

import logging
from flask import Blueprint, jsonify, current_app
from datetime import datetime
from sqlalchemy import text
import os

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        JSON with service status
    """
    # Liveness check: should only fail if the process can't serve HTTP.
    # Do not include dependency checks here.
    return jsonify({
        'status': 'healthy',
        'service': 'WALLET-TRUST Backend',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with system component status.
    
    Returns:
        JSON with detailed component status
    """
    skip_db = _truthy(os.getenv('HEALTH_SKIP_DB'))
    skip_blockchain = _truthy(os.getenv('HEALTH_SKIP_BLOCKCHAIN'))
    skip_storage = _truthy(os.getenv('HEALTH_SKIP_STORAGE'))
    skip_redis = _truthy(os.getenv('HEALTH_SKIP_REDIS'))

    strict_ready = _truthy(os.getenv('HEALTH_STRICT_READY', 'true'))

    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'api': 'online',
            'database': 'skipped' if skip_db else 'checking',
            'blockchain': 'skipped' if skip_blockchain else 'checking',
            'storage': 'skipped' if skip_storage else 'checking',
            'redis': 'skipped' if skip_redis else 'checking',
        },
        'errors': {}
    }
    
    # Check database connection
    if not skip_db:
        try:
            from models import db
            db.session.execute(text('SELECT 1'))
            status['components']['database'] = 'online'
        except Exception as e:
            logger.error("Database health check failed", exc_info=True)
            status['components']['database'] = 'offline'
            status['errors']['database'] = str(e)
            status['status'] = 'degraded'
    
    # Check blockchain connection
    if not skip_blockchain:
        try:
            from config import config
            from core.blockchain import get_web3_manager

            w3_manager = get_web3_manager(config)
            if not w3_manager or not getattr(w3_manager, 'connected', False):
                raise RuntimeError('Web3Manager not connected')

            status['components']['blockchain'] = 'online'
        except Exception as e:
            logger.error("Blockchain health check failed", exc_info=True)
            status['components']['blockchain'] = 'offline'
            status['errors']['blockchain'] = str(e)
            status['status'] = 'degraded'
    
    # Check storage connection
    if not skip_storage:
        try:
            from core.storage import FilebaseStorage
            storage = FilebaseStorage(current_app.config)
            is_connected, message = storage.check_connectivity()

            if is_connected:
                status['components']['storage'] = 'online'
            else:
                status['components']['storage'] = 'offline'
                status['errors']['storage'] = message
                status['status'] = 'degraded'
        except Exception as e:
            logger.error("Storage health check failed", exc_info=True)
            status['components']['storage'] = 'offline'
            status['errors']['storage'] = str(e)
            status['status'] = 'degraded'

    # Check Redis connection (optional)
    if not skip_redis:
        try:
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                status['components']['redis'] = 'not_configured'
            else:
                import redis
                client = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
                client.ping()
                status['components']['redis'] = 'online'
        except Exception as e:
            logger.error("Redis health check failed", exc_info=True)
            status['components']['redis'] = 'offline'
            status['errors']['redis'] = str(e)
            status['status'] = 'degraded'
    
    # Readiness semantics:
    # - strict_ready=true: any offline dependency makes this endpoint 503
    # - strict_ready=false: always 200, but components show degraded/offline
    status_code = 200
    if strict_ready and status['status'] != 'healthy':
        status_code = 503
    
    return jsonify(status), status_code


@health_bp.route('/health/ready', methods=['GET'])
def readiness_alias():
    """Alias for /health/detailed (readiness)."""
    return detailed_health_check()


@health_bp.route('/health/live', methods=['GET'])
def liveness_alias():
    """Alias for /health (liveness)."""
    return health_check()


@health_bp.route('/version', methods=['GET'])
def get_version():
    """
    Get API version information.
    
    Returns:
        JSON with version info
    """
    return jsonify({
        'version': '2.0.0',
        'release_date': '2026-02-28',
        'status': 'production',
        'features': [
            'blockchain_tokens',
            'document_processing',
            'user_management',
            'rate_limiting',
            'encryption'
        ]
    }), 200


@health_bp.route('/health/storage', methods=['GET'])
def storage_health_check():
    """
    Check Filebase storage connectivity
    
    Returns:
        JSON with storage status and detailed information
    """
    status = {
        'service': 'Filebase Storage',
        'status': 'unknown',
        'timestamp': datetime.utcnow().isoformat(),
        'details': {}
    }
    
    try:
        from core.storage import FilebaseStorage
        
        storage = FilebaseStorage(current_app.config)
        
        # Check connectivity
        is_connected, message = storage.check_connectivity()
        
        if is_connected:
            status['status'] = 'healthy'
            status['details'] = {
                'endpoint': current_app.config.get('FILEBASE_ENDPOINT'),
                'bucket': current_app.config.get('FILEBASE_BUCKET'),
                'message': message,
                'connectivity': 'verified'
            }
            status_code = 200
        else:
            status['status'] = 'unhealthy'
            status['details'] = {
                'endpoint': current_app.config.get('FILEBASE_ENDPOINT'),
                'bucket': current_app.config.get('FILEBASE_BUCKET'),
                'error': message,
                'connectivity': 'failed'
            }
            status_code = 503
    
    except Exception as e:
        status['status'] = 'error'
        status['details'] = {
            'error': str(e),
            'message': 'Failed to check storage health'
        }
        status_code = 503
        logger.error(f"Storage health check failed: {str(e)}")
    
    return jsonify(status), status_code
