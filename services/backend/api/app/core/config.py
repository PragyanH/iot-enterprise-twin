from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
AUTH_DB_PATH = os.getenv("AEGIS_AUTH_DB_PATH", str(BASE_DIR / "data" / "aegis_auth.db"))
