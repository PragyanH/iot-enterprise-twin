from app.core.config import (
    ALLOWED_ATTACK_JOB_IDS,
    ATTACK_CONTROLLER_TOKEN,
    ATTACK_CONTROLLER_URL,
    MODEL_PACKAGE_PATH,
    CANONICALIZATION_PATH,
    INTELLIGENCE_CONFIG_PATH,
    RULES_PATH,
    MITRE_SCENARIOS_PATH,
    INCIDENT_DB_PATH,
    FORENSIC_REPORTS_DIR,
    RECOVERY_CLEAN_WINDOWS,
    TELEMETRY_STALE_SECONDS,
    ATTACK_CONTROLLER_TIMEOUT_SECONDS,
    TSHARK_PATH,
    TSHARK_INTERFACE,
    AUTH_DB_PATH,
    AUTH_TOKEN_HOURS,
    SMTP_ENABLED,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_USE_TLS,
    SMTP_TIMEOUT_SECONDS,
)
from pathlib import Path

from app.services.auth import AuthService
from app.services.intelligence import IntelligenceService
from app.services.notifications import NotificationService, SMTPSettings
from app.services.trust import AttackController, HybridTrustService
from app.services.workflow import IncidentWorkflowService


auth_service = AuthService(Path(AUTH_DB_PATH), token_hours=AUTH_TOKEN_HOURS)


attack_controller = AttackController(
    base_url=ATTACK_CONTROLLER_URL,
    token=ATTACK_CONTROLLER_TOKEN,
    allowed_job_ids=ALLOWED_ATTACK_JOB_IDS,
    timeout_seconds=ATTACK_CONTROLLER_TIMEOUT_SECONDS,
)
trust_service = HybridTrustService(
    MODEL_PACKAGE_PATH,
    attack_controller,
    rules_path=RULES_PATH,
    canonicalization_path=CANONICALIZATION_PATH,
    intelligence_path=INTELLIGENCE_CONFIG_PATH,
    incident_db_path=INCIDENT_DB_PATH,
    reports_dir=FORENSIC_REPORTS_DIR,
    recovery_clean_windows_required=RECOVERY_CLEAN_WINDOWS,
    stale_timeout_seconds=TELEMETRY_STALE_SECONDS,
    tshark_path=TSHARK_PATH,
    tshark_interface=TSHARK_INTERFACE,
)
notification_service = NotificationService(SMTPSettings(
    enabled=SMTP_ENABLED, host=SMTP_HOST, port=SMTP_PORT,
    username=SMTP_USERNAME, password=SMTP_PASSWORD, sender=SMTP_FROM,
    use_tls=SMTP_USE_TLS, timeout_seconds=SMTP_TIMEOUT_SECONDS,
))
workflow_service = IncidentWorkflowService(trust_service.incidents, auth_service, notification_service)
intelligence_service = IntelligenceService(
    MODEL_PACKAGE_PATH,
    RULES_PATH,
    CANONICALIZATION_PATH,
    INTELLIGENCE_CONFIG_PATH,
    MITRE_SCENARIOS_PATH,
)
