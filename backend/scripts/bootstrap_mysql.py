"""Bootstrap MySQL database and create tables.

This script:
- Loads backend/.env
- Ensures the configured MySQL database exists (if AUTO_CREATE_DATABASE=true)
- Creates all SQLAlchemy tables (same behavior as app startup)

Run:
  python scripts/bootstrap_mysql.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_dir))
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    # Ensure this is enabled during bootstrap unless user disabled it
    os.environ.setdefault("AUTO_CREATE_DATABASE", "true")

    from app_factory import create_app

    app = create_app()
    print("[DONE] ✅ MySQL database and tables are ready")


if __name__ == "__main__":
    main()
