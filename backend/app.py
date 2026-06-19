"""
WALLET-TRUST Backend Application Entry Point

Production-grade Flask application with comprehensive security hardening.

Implements:
- JWT-based authentication
- Rate limiting
- CORS configuration
- Security headers
- Input validation
- Comprehensive error handling
- Modular architecture

Author: Security Team
Date: February 28 2026
Version: 2.0.0
"""

import os
import logging
import sys
from pathlib import Path

# Load environment variables from .env file FIRST, before any other imports
from dotenv import load_dotenv
backend_dir = Path(__file__).parent
env_file = backend_dir / '.env'
if env_file.exists():
    load_dotenv(env_file)

# Add backend directory to path
sys.path.insert(0, str(backend_dir))

from app_factory import create_app
from config import config

# Create logs directory if it doesn't exist
logs_dir = backend_dir / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logs_dir / 'app.log', mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Create Flask application
try:
    app = create_app()
    logger.info("✅ Flask application created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Flask application: {e}", exc_info=True)
    sys.exit(1)

# Shell context processor for flask shell
@app.shell_context_processor
def make_shell_context():
    """Add app context for interactive shell."""
    return {'app': app}

if __name__ == '__main__':
    try:
        # Validate configuration
        config.validate()
        logger.info(f"✅ Using {type(config).__name__} configuration")
        
        # Log server startup
        logger.info("=" * 60)
        logger.info("🚀 WALLET-TRUST Backend Server Starting")
        logger.info("=" * 60)
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        logger.info(f"Debug Mode: {config.DEBUG}")
        logger.info(f"Server: http://0.0.0.0:5000")
        logger.info("=" * 60)
        
        # Run development server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=config.DEBUG,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("⚠️ Server shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}", exc_info=True)
        sys.exit(1)

