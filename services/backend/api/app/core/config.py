from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
load_dotenv(REPOSITORY_ROOT / ".env")

def repository_path(environment_key: str, default: str) -> Path:
    configured = Path(os.getenv(environment_key, default))
    return configured if configured.is_absolute() else REPOSITORY_ROOT / configured


AUTH_DB_PATH = repository_path(
    "AEGIS_AUTH_DB_PATH",
    "services/backend/api/data/aegis_auth.db",
)
AUTH_TOKEN_HOURS = int(os.getenv("AEGIS_AUTH_TOKEN_HOURS", "12"))


MODEL_PACKAGE_PATH = repository_path(
    "AEGIS_MODEL_PACKAGE_PATH",
    "model-store/aegis-hybrid-trust/v1",
)
ATTACK_CONTROLLER_URL = os.getenv("AEGIS_ATTACK_CONTROLLER_URL", "").rstrip("/")
ATTACK_CONTROLLER_TOKEN = os.getenv("AEGIS_ATTACK_CONTROLLER_TOKEN", "")
ALLOWED_ATTACK_JOB_IDS = {
    value.strip()
    for value in os.getenv("AEGIS_ALLOWED_ATTACK_JOB_IDS", "pi-syn-demo").split(",")
    if value.strip()
}
RULES_PATH = repository_path("AEGIS_RULES_PATH", "rules/aegis_rules.yaml")
CANONICALIZATION_PATH = repository_path(
    "AEGIS_CANONICALIZATION_PATH",
    "model-store/aegis-hybrid-trust/v1/canonicalization.json",
)
INTELLIGENCE_CONFIG_PATH = repository_path(
    "AEGIS_INTELLIGENCE_CONFIG_PATH",
    "model-store/aegis-hybrid-trust/v1/intelligence.json",
)
MITRE_SCENARIOS_PATH = repository_path("AEGIS_MITRE_SCENARIOS_PATH", "rules/mitre_scenarios.yaml")
PI_TARGET_IP = os.getenv("AEGIS_PI_TARGET_IP", "192.168.56.20")
VM_MANAGEMENT_IP = os.getenv("AEGIS_VM_MANAGEMENT_IP", "192.168.57.10")
TSHARK_PATH = os.getenv("AEGIS_TSHARK_PATH", "")
TSHARK_INTERFACE = os.getenv("AEGIS_TSHARK_INTERFACE", "")
TELEMETRY_API_URL = os.getenv("AEGIS_TELEMETRY_API_URL", "http://localhost:8000")
TELEMETRY_SAMPLE_INTERVAL = float(os.getenv("AEGIS_TELEMETRY_SAMPLE_INTERVAL", "1.0"))
TELEMETRY_STALE_SECONDS = float(os.getenv("AEGIS_TELEMETRY_STALE_SECONDS", "3.0"))
INCIDENT_DB_PATH = repository_path("AEGIS_INCIDENT_DB_PATH", "data/aegis_incidents_v1.db")
FORENSIC_REPORTS_DIR = repository_path("AEGIS_FORENSIC_REPORTS_DIR", "reports/incidents-v1")
RECOVERY_CLEAN_WINDOWS = int(os.getenv("AEGIS_RECOVERY_CLEAN_WINDOWS", "3"))
ATTACK_CONTROLLER_TIMEOUT_SECONDS = float(os.getenv("AEGIS_ATTACK_CONTROLLER_TIMEOUT_SECONDS", "3.0"))
SMTP_ENABLED = os.getenv("AEGIS_SMTP_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
SMTP_HOST = os.getenv("AEGIS_SMTP_HOST", "")
SMTP_PORT = int(os.getenv("AEGIS_SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("AEGIS_SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("AEGIS_SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("AEGIS_SMTP_FROM", "aegis@localhost")
SMTP_USE_TLS = os.getenv("AEGIS_SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
SMTP_TIMEOUT_SECONDS = float(os.getenv("AEGIS_SMTP_TIMEOUT_SECONDS", "5.0"))
