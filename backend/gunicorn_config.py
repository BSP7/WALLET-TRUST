# Gunicorn Configuration for WALLET-TRUST Backend
# Production-ready WSGI server configuration
#
# Usage:
#     gunicorn -c backend/gunicorn_config.py backend.app:app
#
# Or with environment variables:
#     GUNICORN_WORKERS=4 GUNICORN_THREADS=2 gunicorn -c backend/gunicorn_config.py backend.app:app

import os
import multiprocessing

# ================================================================================
# SOCKET CONFIGURATION
# ================================================================================
# Bind to localhost:5000 (or use Unix socket in production)
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:5000')

# Alternative Unix socket for reverse proxy (Nginx/Apache):
# bind = 'unix:/var/run/wallet-trust/wallet-trust.sock'

# ================================================================================
# WORKER CONFIGURATION
# ================================================================================
# Production recommendations:
# - Default workers = (2 × CPU count) + 1
# - For CPU-bound: (2 × CPU count) + 1
# - For I/O-bound (like Web3 calls): 4-8 × CPU count

worker_class = 'sync'  # 'sync', 'gevent', 'eventlet', or 'tornado'
workers = int(os.getenv('GUNICORN_WORKERS', (multiprocessing.cpu_count() * 2) + 1))
threads = int(os.getenv('GUNICORN_THREADS', 2))

# Worker heartbeat (monitors worker health)
worker_connections = 1000
keepalive = 5

# ================================================================================
# TIMEOUT CONFIGURATION
# ================================================================================
# Timeout for workers (blockchain operations may take time)
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))  # 120 seconds

# Graceful timeout for shutdown
graceful_timeout = 30

# ================================================================================
# LOGGING
# ================================================================================
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
access_log = os.getenv('GUNICORN_ACCESS_LOG', '-')  # Log to stdout
error_logfile = os.getenv('GUNICORN_ERROR_LOG', '-')  # Log to stderr

# Capture output
capture_output = True

# ================================================================================
# SERVER CONFIGURATION
# ================================================================================
# Keep-alive timeout (for connection reuse)
keepalive = 5

# Max simultaneous connections
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = 100  # Prevent thundering herd

# ================================================================================
# APPLICATION SETTINGS
# ================================================================================
# Preload application code (reduces memory footprint)
preload_app = True

# Number of seconds to wait for gunicorn to become ready
timeout = 120

# ================================================================================
# ENVIRONMENT VARIABLES
# ================================================================================
# Load environment variables from .env file
from pathlib import Path
env_file = Path(__file__).parent / '.env'

if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# ================================================================================
# EXAMPLES
# ================================================================================
"""
EXAMPLE 1: Development
    gunicorn -c backend/gunicorn_config.py backend.app:app --reload

EXAMPLE 2: Production (single machine)
    gunicorn -c backend/gunicorn_config.py\
        --workers 8 \
        --worker-class sync \
        --bind 0.0.0.0:5000 \
        --timeout 120 \
        --access-logfile - \
        backend.app:app

EXAMPLE 3: Production (with Unix socket)
    gunicorn -c backend/gunicorn_config.py \
        --workers 8 \
        --bind unix:/var/run/wallet-trust/wallet-trust.sock \
        backend.app:app

EXAMPLE 4: Production (with environment variables)
    export GUNICORN_WORKERS=8
    export GUNICORN_TIMEOUT=120
    export GUNICORN_BIND=0.0.0.0:5000
    gunicorn -c backend/gunicorn_config.py backend.app:app

EXAMPLE 5: Systemd service file
    [Unit]
    Description=WALLET-TRUST Backend
    After=network.target
    
    [Service]
    Type=notify
    WorkingDirectory=/path/to/WALLET-TRUST/backend
    Environment="FLASK_ENV=production"
    ExecStart=/path/to/venv/bin/gunicorn \
        -c gunicorn_config.py \
        --workers 8 \
        --bind unix:/var/run/wallet-trust/wallet-trust.sock \
        app:app
    ExecReload=/bin/kill -s HUP $MAINPID
    KillMode=mixed
    
    [Install]
    WantedBy=multi-user.target
"""
