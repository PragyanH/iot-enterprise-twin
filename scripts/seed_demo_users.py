from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "backend" / "api"
sys.path.insert(0, str(API_ROOT))

from app.core.config import AUTH_DB_PATH, AUTH_TOKEN_HOURS  # noqa: E402
from app.services.auth import AuthService  # noqa: E402


DEMO_USERS = (
    ("Aegis Demo Administrator", "admin@aegis.local", "ADMIN", "AEGIS_DEMO_ADMIN_PASSWORD"),
    ("Aegis Asset Owner", "owner@aegis.local", "ASSET_OWNER", "AEGIS_DEMO_OWNER_PASSWORD"),
    ("Aegis SME Vendor", "vendor@aegis.local", "SME_VENDOR", "AEGIS_DEMO_VENDOR_PASSWORD"),
)


def main() -> int:
    service = AuthService(Path(AUTH_DB_PATH), token_hours=AUTH_TOKEN_HOURS)
    existing = {str(user["email"]) for user in service.list_users()}
    missing = [key for _, email, _, key in DEMO_USERS if email not in existing and not os.getenv(key)]
    if missing:
        print("Missing required environment variables: " + ", ".join(missing))
        print("No passwords are embedded in this script or written to output.")
        return 2
    created = 0
    for name, email, role, secret_key in DEMO_USERS:
        if email in existing:
            print(f"SKIP {email}: already exists")
            continue
        service.register(name=name, email=email, password=os.environ[secret_key], role=role)
        print(f"CREATED {email} ({role})")
        created += 1
    print(f"Demo user seed complete: {created} created, {len(DEMO_USERS) - created} unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
