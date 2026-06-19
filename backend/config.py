"""
Configuration management for WALLET-TRUST backend.

Environment-specific configuration with security-first defaults.
Supports Development, Staging, and Production environments.

CONFIGURATION HIERARCHY:
1. Environment variables (highest priority)
2. Environment-specific classes (DevelopmentConfig, StagingConfig, ProductionConfig)
3. Base Config class (lowest priority)

SECURITY REQUIREMENTS:
- Development: Secrets auto-generated, HTTPS disabled
- Staging: Requires all secrets in .env file
- Production: Strict validation of all required variables
"""

import os
from datetime import timedelta
import logging

from sqlalchemy.engine import URL

logger = logging.getLogger(__name__)


class Config:
    """
    Base configuration with secure defaults.
    
    All security-sensitive settings should be configured here.
    Environment-specific subclasses override as needed.
    """
    
    # ================================================================
    # APPLICATION SETTINGS
    # ================================================================
    APP_NAME = 'WALLET-TRUST'
    ENV = os.getenv('FLASK_ENV', 'development').lower()
    ENVIRONMENT = ENV
    DEBUG = False
    TESTING = False
    
    # ================================================================
    # SERVER SETTINGS
    # ================================================================
    UPLOAD_FOLDER = os.getenv(
        'UPLOAD_FOLDER',
        os.path.join(os.path.dirname(__file__), 'storage')
    )
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    # ================================================================
    # SECURITY: COOKIES & SESSIONS
    # ================================================================
    SESSION_COOKIE_SECURE = True  # Only transmit over HTTPS in production
    SESSION_COOKIE_HTTPONLY = True  # Prevents JavaScript access
    SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # ================================================================
    # SECURITY: SECRET KEYS (CRITICAL)
    # ================================================================
    # These MUST be set from environment variables in production
    # Never hardcode secrets in source code
    
    # JWT_SECRET: Used for signing JWT tokens
    # Requirements:
    # - Minimum 32 characters (64+ recommended)
    # - Random cryptographic bytes (hex-encoded)
    # - Different per environment
    # - Securely stored (never in git)
    JWT_SECRET = os.getenv('JWT_SECRET')
    
    # ENCRYPTION_KEY: Used for Fernet symmetric encryption
    # Requirements:
    # - Valid Fernet key (base64-encoded)
    # - Different per environment
    # - Consistent across restarts (stored in .env)
    # - Securely stored (never in git)
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    # For backward compatibility
    FERNET_KEY = ENCRYPTION_KEY
    
    # ================================================================
    # DATABASE CONFIGURATION (MySQL)
    # ================================================================
    # Primary config path:
    # - Set MYSQL_* vars (recommended) OR set DATABASE_URL explicitly.
    #
    # Examples:
    #   MYSQL_HOST=BSP179
    #   MYSQL_PORT=3306
    #   MYSQL_USER=root
    #   MYSQL_PASSWORD=...
    #   MYSQL_DB=walletid
    #
    # If DATABASE_URL is set, it wins.
    _database_url = os.getenv('DATABASE_URL')
    if _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        _mysql_url = URL.create(
            drivername='mysql+pymysql',
            username=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            database=os.getenv('MYSQL_DB', 'walletid'),
            query={'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4')},
        )
        SQLALCHEMY_DATABASE_URI = _mysql_url.render_as_string(hide_password=False)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # ================================================================
    # CORS CONFIGURATION
    # ================================================================
    CORS_ALLOWED_ORIGINS = []
    
    # ================================================================
    # RATE LIMITING
    # ================================================================
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    # For production with multiple workers:
    # RATELIMIT_STORAGE_URL=redis://localhost:6379/0
    RATELIMIT_STRATEGY = os.getenv('RATELIMIT_STRATEGY', 'fixed-window')
    
    # ================================================================
    # JWT CONFIGURATION
    # ================================================================
    JWT_ALGORITHM = 'HS256'  # HMAC with SHA-256
    JWT_EXPIRATION_HOURS = 24
    JWT_REFRESH_EXPIRATION_DAYS = 30
    
    # ================================================================
    # BLOCKCHAIN CONFIGURATION (ETHEREUM + SEPOLIA)
    # ================================================================
    # Blockchain RPC endpoint - for reading blockchain state and broadcasting transactions
    BLOCKCHAIN_RPC_URL = os.getenv(
        'BLOCKCHAIN_RPC_URL',
        os.getenv('SEPOLIA_RPC_URL')  # Backward compatibility
    )
    
    # Sepolia testnet chain ID
    BLOCKCHAIN_CHAIN_ID = int(os.getenv('BLOCKCHAIN_CHAIN_ID', '11155111'))
    
    # Deployed contract address on Sepolia
    BLOCKCHAIN_CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')
    
    # Private key for signing transactions (0x-prefixed hex string)
    BLOCKCHAIN_PRIVATE_KEY = os.getenv('PRIVATE_KEY')
    
    # Gas limit for contract interactions
    BLOCKCHAIN_GAS_LIMIT = 300000
    
    # ================================================================
    # FILE STORAGE CONFIGURATION (AWS S3 / Filebase)
    # ================================================================
    FILEBASE_ENDPOINT = os.getenv('ENDPOINT_URL', 'https://s3.filebase.com')
    FILEBASE_BUCKET = os.getenv('BUCKET_NAME', 'pii-authenticator')
    FILEBASE_ACCESS_KEY = os.getenv('FILEBASE_ACCESS_KEY')
    FILEBASE_SECRET_KEY = os.getenv('FILEBASE_SECRET_KEY')
    
    # ================================================================
    # LOGGING
    # ================================================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # ================================================================
    # PASSWORD HASHING (Argon2id)
    # ================================================================
    PASSWORD_HASH_ALGORITHM = 'argon2id'
    ARGON2_TIME_COST = 2  # Number of iterations
    ARGON2_MEMORY_COST = 65536  # 64 MB
    ARGON2_PARALLELISM = 4  # Number of parallel threads
    
    @classmethod
    def validate(cls):
        """
        Validate required environment variables.
        
        This method is called when the app starts to ensure all
        required configuration is present.
        
        Raises:
            RuntimeError: In production if required variables are missing
        """
        required_keys = ['JWT_SECRET', 'ENCRYPTION_KEY']
        
        missing = []
        for key in required_keys:
            value = getattr(cls, key, None)
            if not value or (isinstance(value, str) and len(value.strip()) == 0):
                missing.append(key)
        
        # Handle missing keys based on environment
        if missing:
            env = cls.ENV
            if env == 'production':
                # Production: FAIL LOUDLY
                error_msg = (
                    f"❌ PRODUCTION CONFIGURATION ERROR\n\n"
                    f"Missing required environment variables: {', '.join(missing)}\n"
                    f"Please set these in your .env file (or production secrets manager):\n"
                )
                for key in missing:
                    error_msg += f"\n  {key}\n"
                raise RuntimeError(error_msg)
            else:
                # Development/Staging: Generate or warn
                logger.warning(
                    f"⚠️  Missing configuration keys: {', '.join(missing)}\n"
                    f"   For development, auto-generating defaults.\n"
                    f"   For production, you MUST set these in .env"
                )
                
                # Auto-generate for development only
                if not cls.JWT_SECRET:
                    cls.JWT_SECRET = os.urandom(32).hex()
                    logger.warning(f"   🔐 Generated JWT_SECRET: {cls.JWT_SECRET}")
                
                if not cls.ENCRYPTION_KEY:
                    from cryptography.fernet import Fernet
                    cls.ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')
                    logger.warning(f"   🔐 Generated ENCRYPTION_KEY: {cls.ENCRYPTION_KEY}")
    
    @classmethod
    def validate_blockchain_config(cls):
        """
        Validate blockchain configuration.
        
        This is called separately so blockchain failures don't prevent
        app startup for routes that don't need blockchain.
        """
        if not cls.BLOCKCHAIN_RPC_URL:
            logger.warning(
                "⚠️  BLOCKCHAIN_RPC_URL not configured. "
                "Blockchain endpoints will not work."
            )
        
        if not cls.BLOCKCHAIN_CONTRACT_ADDRESS:
            logger.warning(
                "⚠️  BLOCKCHAIN_CONTRACT_ADDRESS not configured. "
                "Smart contract interaction will fail."
            )
        
        if not cls.BLOCKCHAIN_PRIVATE_KEY:
            logger.warning(
                "⚠️  BLOCKCHAIN_PRIVATE_KEY not configured. "
                "Transaction signing will fail."
            )


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    - DEBUG: Enabled (hot reload, detailed errors)
    - HTTPS: Disabled (insecure cookies)
    - Secrets: Auto-generated if not provided
    - CORS: All localhost origins allowed
    - Logging: DEBUG level
    
    USAGE:
        Set FLASK_ENV=development in .env
    """
    DEBUG = True
    ENV = 'development'
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    SESSION_COOKIE_SAMESITE = 'Lax'
    LOG_LEVEL = 'DEBUG'
    
    # Allow all localhost origins for frontend development
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',      # Vite default
        'http://localhost:3000',      # React default
        'http://localhost:8080',      # Common dev port
        'http://127.0.0.1:5173',      # Vite (127.0.0.1)
        'http://127.0.0.1:3000',      # React (127.0.0.1)
        'http://127.0.0.1:8080',      # Common (127.0.0.1)
    ]
    
    @classmethod
    def validate(cls):
        """Validate and auto-generate development defaults."""
        super().validate()
        # Development: auto-generate missing secrets
        if not cls.JWT_SECRET:
            cls.JWT_SECRET = os.urandom(32).hex()
            logger.info(f"✅ Generated development JWT_SECRET")
        if not cls.ENCRYPTION_KEY:
            from cryptography.fernet import Fernet
            cls.ENCRYPTION_KEY = Fernet.generate_key().decode('utf-8')
            logger.info(f"✅ Generated development ENCRYPTION_KEY")


class StagingConfig(Config):
    """
    Staging environment configuration.
    
    - DEBUG: Disabled
    - HTTPS: Required (secure cookies)
    - Secrets: MUST be set in environment
    - CORS: Staging domains only
    - Rate Limiting: Enabled with Redis (recommended)
    - Logging: INFO level
    
    USAGE:
        Set FLASK_ENV=staging in environment
        Ensure all secrets are in .env or secrets manager
    """
    DEBUG = False
    ENV = 'staging'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    LOG_LEVEL = 'INFO'
    
    # Staging frontend domains
    CORS_ALLOWED_ORIGINS = [
        os.getenv('STAGING_DOMAIN', 'https://staging.wallet-trust.com'),
        os.getenv('STAGING_FE_DOMAIN', 'https://staging-fe.wallet-trust.com')
    ]
    
    # For staging, use Redis for rate limiting (supports multiple workers)
    # RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/0')
    
    @classmethod
    def validate(cls):
        """Validate staging configuration."""
        super().validate()
        logger.info(f"✅ Using StagingConfig")
        logger.info(f"   CORS Origins: {cls.CORS_ALLOWED_ORIGINS}")


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    ⚠️  CRITICAL SECURITY REQUIREMENTS:
    
    - DEBUG: MUST be False
    - HTTPS: REQUIRED (secure cookies enforced)
    - Secrets: MUST be set (no auto-generation)
    - Validation: STRICT - fails loudly if config is incomplete
    - Rate Limiting: MUST use Redis (not memory backend)
    - Logging: WARNING level (minimal output)
    - Error Messages: Generic (no sensitive info exposure)
    
    REQUIRED ENVIRONMENT VARIABLES:
        JWT_SECRET          - Generated with scripts/generate_keys.py
        ENCRYPTION_KEY      - Generated with scripts/generate_keys.py
        BLOCKCHAIN_RPC_URL  - Ethereum RPC endpoint
        CONTRACT_ADDRESS    - Deployed contract address
        PRIVATE_KEY         - Ethereum private key (with 0x prefix)
        PROD_DOMAIN         - Production backend domain
        PROD_FE_DOMAIN      - Production frontend domain
    
    USAGE:
        Set FLASK_ENV=production in environment
        Set all secrets via environment variables or secrets manager
        Use secrets management tool (Vault, AWS Secrets Manager, etc.)
    
    EXAMPLE (Docker/Kubernetes):
        export FLASK_ENV=production
        export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
        export ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
        ...
    """
    DEBUG = False
    ENV = 'production'
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    SESSION_COOKIE_HTTPONLY = True
    LOG_LEVEL = 'WARNING'  # Minimal logging in production
    
    # Production frontend domains
    CORS_ALLOWED_ORIGINS = [
        os.getenv('PROD_DOMAIN', 'https://wallet-trust.com'),
        os.getenv('PROD_FE_DOMAIN', 'https://wallet-trust.com')
    ]
    
    # PRODUCTION REQUIREMENT: Use Redis for rate limiting with multiple workers
    # Default in-memory backend won't work with multiple workers
    RATELIMIT_STORAGE_URL = os.getenv(
        'RATELIMIT_STORAGE_URL',
        'redis://localhost:6379/0'
    )
    RATELIMIT_KEY_PREFIX = 'wallet-trust'
    
    @classmethod
    def validate(cls):
        """
        Strictly validate production configuration.
        
        Raises:
            RuntimeError: If ANY required variable is missing
        """
        # Check base requirements
        super().validate()
        
        # Additional production-only requirements
        required_blockchain = [
            ('BLOCKCHAIN_RPC_URL', 'Ethereum RPC endpoint'),
            ('BLOCKCHAIN_CONTRACT_ADDRESS', 'Smart contract address on Sepolia'),
            ('BLOCKCHAIN_PRIVATE_KEY', 'Private key for transactions'),
        ]
        
        missing = []
        for var_name, description in required_blockchain:
            value = getattr(cls, var_name, None)
            if not value or (isinstance(value, str) and len(value.strip()) == 0):
                missing.append(f"{var_name} ({description})")
        
        if missing:
            error_msg = (
                "\n" + "=" * 80 + "\n"
                "❌ PRODUCTION CONFIGURATION ERROR\n"
                "=" * 80 + "\n\n"
                "The following REQUIRED variables are missing:\n\n"
            )
            for item in missing:
                error_msg += f"  - {item}\n"
            error_msg += (
                "\nPlease set these environment variables before deploying to production.\n"
                "Use a secrets management tool (AWS Secrets Manager, HashiCorp Vault, etc.)\n"
                "\n" + "=" * 80 + "\n"
            )
            raise RuntimeError(error_msg)
        
        # Validate CORS is configured
        if not cls.CORS_ALLOWED_ORIGINS or cls.CORS_ALLOWED_ORIGINS == [None, None]:
            logger.warning(
                "⚠️  CORS_ALLOWED_ORIGINS may not be configured correctly. "
                "Set PROD_DOMAIN and PROD_FE_DOMAIN environment variables."
            )
        
        logger.info(f"✅ Production configuration validated")
        logger.info(f"   CORS Origins: {cls.CORS_ALLOWED_ORIGINS}")
        logger.info(f"   Rate Limiter: {cls.RATELIMIT_STORAGE_URL}")
        logger.info(f"   Blockchain Chain: Sepolia ({cls.BLOCKCHAIN_CHAIN_ID})")


# Get configuration based on environment
def get_config():
    """Get configuration object based on FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'staging': StagingConfig,
        'production': ProductionConfig
    }
    
    cfg_class = config_map.get(env, DevelopmentConfig)
    cfg_class.validate()
    return cfg_class


# Export config instance
config = get_config()
