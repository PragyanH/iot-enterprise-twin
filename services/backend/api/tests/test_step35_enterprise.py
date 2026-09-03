from __future__ import annotations

import smtplib
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.telemetry import TelemetryWindow
from app.main import app
from app.services.auth import AuthService
from app.services.intelligence import IntelligenceService
from app.services.notifications import NotificationService, SMTPSettings
from app.services.trust import AttackController, HybridTrustService
from app.services.workflow import IncidentWorkflowService


ROOT = Path(__file__).resolve().parents[4]
MODEL = ROOT / "model-store" / "aegis-hybrid-trust" / "v1"


def smtp_settings(*, enabled: bool = True) -> SMTPSettings:
    return SMTPSettings(enabled, "smtp.test", 587, "user", "secret", "aegis@test.local", True, 1.0)


class SuccessfulSMTP:
    messages: list[object] = []

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def starttls(self) -> None:
        pass

    def login(self, _username: str, _password: str) -> None:
        pass

    def send_message(self, message: object) -> None:
        self.messages.append(message)

    def quit(self) -> None:
        pass


class AuthenticationFailureSMTP(SuccessfulSMTP):
    def login(self, _username: str, _password: str) -> None:
        raise smtplib.SMTPAuthenticationError(535, b"rejected")


class DeliveryFailureSMTP(SuccessfulSMTP):
    def send_message(self, _message: object) -> None:
        raise smtplib.SMTPConnectError(421, "temporarily unavailable")


def service_with_incident(tmp_path: Path, *, unknown: bool = False) -> tuple[HybridTrustService, str]:
    service = HybridTrustService(
        MODEL, AttackController("", "", {"pi-syn-demo"}),
        incident_db_path=tmp_path / "incidents.db", reports_dir=tmp_path / "reports",
    )
    if unknown:
        prediction = service.ingest(
            TelemetryWindow("PI-001", "xai_simulation", IntelligenceService._unknown_points(service))
        )
        assert prediction.attack_type == "unknown_behavioral_anomaly"
    else:
        for window in service.replay_windows("pi_syn"):
            service.ingest(window)
    incident = service.incidents.list(device_id="PI-001")[0]
    return service, str(incident["incident_id"])


def users(auth: AuthService) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    admin = auth.register(name="Admin", email="admin@test.local", password="admin-pass-123", role="ADMIN")
    owner = auth.register(name="Owner A", email="owner-a@test.local", password="owner-pass-123", role="ASSET_OWNER")
    other = auth.register(name="Owner B", email="owner-b@test.local", password="owner-pass-456", role="ASSET_OWNER")
    vendor = auth.register(name="Vendor", email="vendor@test.local", password="vendor-pass-123", role="SME_VENDOR")
    return admin, owner, other, vendor


def test_auth_registration_hash_login_logout_and_inactive_user(tmp_path: Path) -> None:
    auth = AuthService(tmp_path / "auth.db")
    admin = auth.register(name="Admin", email="ADMIN@Test.Local", password="never-plaintext", role="ADMIN")
    with pytest.raises(ValueError, match="already registered"):
        auth.register(name="Duplicate", email="admin@test.local", password="other-password", role="ADMIN")
    with sqlite3.connect(auth.path) as connection:
        stored = connection.execute("SELECT password_hash FROM users WHERE id=?", (admin["user_id"],)).fetchone()[0]
    assert stored != "never-plaintext" and stored.startswith("scrypt$")
    assert auth.authenticate("admin@test.local", "incorrect") is None
    session = auth.login("admin@test.local", "never-plaintext")
    token = str(session["access_token"])
    assert auth.current_user(token)["role"] == "ADMIN"  # type: ignore[index]
    assert auth.logout(token) is True and auth.current_user(token) is None
    auth.set_active(str(admin["user_id"]), False)
    with pytest.raises(PermissionError):
        auth.login("admin@test.local", "never-plaintext")


def test_api_auth_bootstrap_role_controls_and_public_demo_regression() -> None:
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/logout",
            "/api/v1/auth/me", "/api/v1/auth/users",
            "/api/v1/incidents/{incident_id}/assign",
            "/api/v1/incidents/{incident_id}/acknowledge",
            "/api/v1/incidents/{incident_id}/notes",
            "/api/v1/incidents/{incident_id}/email-report",
            "/api/v1/incidents/{incident_id}/report.pdf",
        ):
            assert path in paths
        bootstrap = client.post("/api/v1/auth/register", json={
            "name": "API Admin", "email": "api-admin@test.local",
            "password": "admin-api-pass", "role": "ADMIN",
        })
        assert bootstrap.status_code == 201
        login = client.post("/api/v1/auth/login", json={"email": "api-admin@test.local", "password": "admin-api-pass"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/auth/me", headers=headers).json()["role"] == "ADMIN"
        created = client.post("/api/v1/auth/register", headers=headers, json={
            "name": "API Owner", "email": "api-owner@test.local",
            "password": "owner-api-pass", "role": "ASSET_OWNER",
        })
        assert created.status_code == 201
        assert client.get("/api/v1/auth/users", headers=headers).status_code == 200
        owner_login = client.post("/api/v1/auth/login", json={"email": "api-owner@test.local", "password": "owner-api-pass"}).json()
        owner_headers = {"Authorization": f"Bearer {owner_login['access_token']}"}
        assert client.get("/api/v1/auth/users", headers=owner_headers).status_code == 403
        assert client.post("/api/v1/auth/register", headers=owner_headers, json={
            "name": "No", "email": "no@test.local", "password": "not-allowed", "role": "SME_VENDOR",
        }).status_code == 403
        assert client.post("/api/v1/auth/logout", headers=headers).json() == {"logged_out": True}
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
        assert client.get("/api/v1/incidents").status_code == 401
        assert client.get("/api/v1/fleet").status_code == 200


def test_assignment_access_history_acknowledgement_and_append_only_notes(tmp_path: Path) -> None:
    trust, incident_id = service_with_incident(tmp_path)
    auth = AuthService(tmp_path / "auth.db")
    admin, owner, other, vendor = users(auth)
    workflow = IncidentWorkflowService(trust.incidents, auth, NotificationService(smtp_settings(enabled=False)))
    assigned = workflow.assign(incident_id, str(owner["user_id"]), admin, "Primary asset owner")
    assert assigned["assignment_status"] == "ASSIGNED"
    assert assigned["email_status"] == "DISABLED" and assigned["email_attempts"] == 0
    assert len(assigned["assignment_history"]) == 1
    assert workflow.require_access(incident_id, owner)["incident_id"] == incident_id
    with pytest.raises(PermissionError):
        workflow.require_access(incident_id, other)
    with pytest.raises(PermissionError):
        workflow.assign(incident_id, str(other["user_id"]), owner)
    delegated = workflow.assign(incident_id, str(vendor["user_id"]), owner, "Specialist analysis")
    assert len(delegated["assignment_history"]) == 2
    assert delegated["assignment_history"][-1]["previous_assignee"]["user_id"] == owner["user_id"]
    acknowledged = workflow.acknowledge(incident_id, vendor)
    assert acknowledged["assignment_status"] == "ACKNOWLEDGED"
    note = workflow.add_note(incident_id, vendor, "Validated SYN exhaustion indicators.")
    assert note["note_id"] == "NOTE-0001" and note["author_role"] == "SME_VENDOR"
    assert workflow.notes(incident_id, vendor) == [note]
    with pytest.raises(PermissionError):
        workflow.add_note(incident_id, other, "Should not persist")
    persisted = trust.incidents.require(incident_id)
    event_types = {event["type"] for event in persisted["timeline"]}
    assert {"INCIDENT_ASSIGNED", "INCIDENT_REASSIGNED", "INCIDENT_ACKNOWLEDGED", "INVESTIGATION_NOTE_ADDED"}.issubset(event_types)


def test_smtp_success_disabled_failures_and_retry_after_persisted_assignment(tmp_path: Path) -> None:
    SuccessfulSMTP.messages.clear()
    trust, incident_id = service_with_incident(tmp_path)
    auth = AuthService(tmp_path / "auth.db")
    admin, owner, _, _ = users(auth)
    delivery_failure = NotificationService(smtp_settings(), smtp_factory=DeliveryFailureSMTP)
    failed_assignment = IncidentWorkflowService(trust.incidents, auth, delivery_failure).assign(
        incident_id, str(owner["user_id"]), admin
    )
    assert failed_assignment["email_status"] == "FAILED" and failed_assignment["email_attempts"] == 1
    assert failed_assignment["assigned_to_user_id"] == owner["user_id"]
    success = NotificationService(smtp_settings(), smtp_factory=SuccessfulSMTP)
    sent = IncidentWorkflowService(trust.incidents, auth, success).email_report(incident_id, admin)
    assert sent["email_status"] == "SENT" and sent["email_attempts"] == 2
    assert SuccessfulSMTP.messages and SuccessfulSMTP.messages[-1].get_content_type() == "multipart/mixed"
    auth_failure = NotificationService(smtp_settings(), smtp_factory=AuthenticationFailureSMTP)
    failed = IncidentWorkflowService(trust.incidents, auth, auth_failure).email_report(incident_id, admin)
    assert failed["email_status"] == "FAILED" and failed["email_attempts"] == 3
    assert failed["assigned_to_user_id"] == owner["user_id"]
    assert "authentication" in str(failed["email_error"]).lower()
    timeout = NotificationService(smtp_settings(), smtp_factory=lambda *_a, **_k: (_ for _ in ()).throw(TimeoutError()))
    timed_out = timeout.send_assignment(failed, owner, admin, None)
    assert timed_out["status"] == "FAILED" and "timed out" in str(timed_out["error"])
    disabled = NotificationService(smtp_settings(enabled=False)).send_assignment(failed, owner, admin, None)
    assert disabled["status"] == "DISABLED" and disabled["attempted"] is False
    retried = IncidentWorkflowService(trust.incidents, auth, success).email_report(incident_id, admin)
    assert retried["email_status"] == "SENT" and retried["email_attempts"] == 4


def test_pdf_known_unknown_idempotence_and_html_survives_pdf_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    known, incident_id = service_with_incident(tmp_path / "known")
    incident = known.incidents.require(incident_id)
    report = incident["report"]
    pdf_path = Path(report["pdf_path"])
    assert report["pdf_ready"] is True and pdf_path.stat().st_size > 500
    content = pdf_path.read_bytes()
    assert content.startswith(b"%PDF") and b"T1498.001" in content
    regenerated = known.incidents.generate_report(incident_id)
    before = len(regenerated["timeline"])
    regenerated = known.incidents.generate_report(incident_id)
    assert regenerated["report"]["pdf_path"] == str(pdf_path.resolve()) and len(regenerated["timeline"]) == before
    unknown, unknown_id = service_with_incident(tmp_path / "unknown", unknown=True)
    unknown_pdf = Path(unknown.incidents.require(unknown_id)["report"]["pdf_path"]).read_bytes()
    assert b"Unmapped / Investigation Required" in unknown_pdf
    failed, failed_id = service_with_incident(tmp_path / "failed")
    failed_incident = failed.incidents.require(failed_id)
    failed_incident["report"]["needs_refresh"] = True
    failed.incidents.repository.save(failed_incident)
    monkeypatch.setattr("app.services.incidents.render_incident_pdf", lambda *_args: (_ for _ in ()).throw(OSError("PDF unavailable")))
    result = failed.incidents.generate_report(failed_id)
    assert result["report"]["html_ready"] is True and Path(result["report"]["html_path"]).exists()
    assert result["report"]["pdf_status"] == "failed"
