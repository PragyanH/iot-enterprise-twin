from __future__ import annotations

import os
import tempfile
from pathlib import Path


# API tests import the process-wide runtime service. Keep its persistent test
# incidents away from the application's real local SQLite/report locations.
_runtime_root = Path(tempfile.mkdtemp(prefix="aegis-runtime-tests-"))
os.environ.setdefault("AEGIS_INCIDENT_DB_PATH", str(_runtime_root / "incidents.db"))
os.environ.setdefault("AEGIS_FORENSIC_REPORTS_DIR", str(_runtime_root / "reports"))
