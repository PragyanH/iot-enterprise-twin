from __future__ import annotations

import smtplib
import socket
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Callable


@dataclass(frozen=True, slots=True)
class SMTPSettings:
    enabled: bool
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_tls: bool
    timeout_seconds: float


class NotificationService:
    def __init__(self, settings: SMTPSettings, *, smtp_factory: Callable[..., object] = smtplib.SMTP,
                 clock: Callable[[], datetime] | None = None, recipient_path: Path | None = None) -> None:
        self.settings = settings
        self.smtp_factory = smtp_factory
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.recipient_path = recipient_path
        self.recipient: str | None = self._load_recipient()

    def _load_recipient(self) -> str | None:
        if not self.recipient_path or not self.recipient_path.exists():
            return None
        try:
            value = json.loads(self.recipient_path.read_text(encoding="utf-8")).get("email")
            return str(value).strip() if value else None
        except (OSError, TypeError, ValueError):
            return None

    def set_recipient(self, email: str | None) -> None:
        self.recipient = email.strip() if email and email.strip() else None
        if self.recipient_path:
            try:
                self.recipient_path.parent.mkdir(parents=True, exist_ok=True)
                self.recipient_path.write_text(json.dumps({"email": self.recipient}), encoding="utf-8")
            except OSError:
                pass

    def recipient_status(self) -> dict[str, object]:
        return {"configured": bool(self.recipient), "recipient": self.recipient}

    def capability(self) -> dict[str, object]:
        return {
            "enabled": self.settings.enabled,
            "configured": bool(self.settings.host and self.settings.sender),
            "host": self.settings.host if self.settings.enabled else None,
            "port": self.settings.port,
            "use_tls": self.settings.use_tls,
        }

    @staticmethod
    def _mitre_text(incident: dict[str, object]) -> str:
        mitre = incident.get("mitre")
        if isinstance(mitre, dict):
            return f"{mitre.get('technique_id')} — {mitre.get('technique_name')}"
        return "Unmapped / Investigation Required"

    def send_assignment(self, incident: dict[str, object], recipient: dict[str, object],
                        assigned_by: dict[str, object], pdf_path: Path | None) -> dict[str, object]:
        email = str(recipient["email"])
        if not self.settings.enabled:
            return {"status": "DISABLED", "recipient": email, "sent_at": None, "error": None, "attempted": False, "attachment": False}
        if not self.settings.host or not self.settings.sender:
            return {"status": "FAILED", "recipient": email, "sent_at": None, "error": "SMTP is enabled but host/from is not configured", "attempted": True, "attachment": False}
        message = EmailMessage()
        readable_attack = str(incident["attack_type"]).replace("_", " ").title()
        message["Subject"] = f"[Aegis-Twin] {incident['severity']} Incident Assigned — {incident['device_id']} — {readable_attack}"
        message["From"] = self.settings.sender
        message["To"] = email
        message.set_content(
            "\n".join([
                "AEGIS-TWIN INCIDENT ASSIGNMENT",
                f"Incident ID: {incident['incident_id']}",
                f"Device: {incident['device_id']} — {incident['device_name']}",
                f"Severity: {incident['severity']}",
                f"Attack / anomaly: {readable_attack}",
                f"MITRE: {self._mitre_text(incident)}",
                f"Minimum trust: {incident['minimum_trust']}",
                f"Detection time: {incident['detected_at']}",
                f"Current status: {incident['status']}",
                f"Assigned by: {assigned_by['name']} ({assigned_by['email']})",
                f"Incident reference: /api/v1/incidents/{incident['incident_id']}",
            ])
        )
        attached = False
        if pdf_path and pdf_path.exists() and pdf_path.stat().st_size <= 10 * 1024 * 1024:
            message.add_attachment(
                pdf_path.read_bytes(), maintype="application", subtype="pdf", filename=pdf_path.name
            )
            attached = True
        try:
            client = self.smtp_factory(
                self.settings.host, self.settings.port, timeout=self.settings.timeout_seconds
            )
            try:
                if self.settings.use_tls:
                    client.starttls()
                if self.settings.username:
                    client.login(self.settings.username, self.settings.password)
                client.send_message(message)
            finally:
                try:
                    client.quit()
                except Exception:
                    pass
            return {
                "status": "SENT", "recipient": email,
                "sent_at": self.clock().astimezone(timezone.utc).isoformat(),
                "error": None, "attempted": True, "attachment": attached,
            }
        except smtplib.SMTPAuthenticationError:
            error_text = "SMTP authentication failed"
        except (TimeoutError, socket.timeout):
            error_text = "SMTP connection timed out"
        except (smtplib.SMTPException, OSError) as exc:
            error_text = f"SMTP delivery failed: {exc}"
        except Exception as exc:  # External SMTP adapters must never roll back persisted workflow state.
            error_text = f"SMTP delivery failed unexpectedly: {type(exc).__name__}"
        return {"status": "FAILED", "recipient": email, "sent_at": None, "error": error_text, "attempted": True, "attachment": attached}

    def send_forensic_report(self, incident: dict[str, object], pdf_path: Path | None) -> dict[str, object]:
        if not self.recipient:
            return {"status": "NOT_CONFIGURED", "recipient": None, "sent_at": None, "error": "No forensic report recipient configured", "attempted": False, "attachment": False}
        email = self.recipient
        if not self.settings.enabled:
            return {"status": "DISABLED", "recipient": email, "sent_at": None, "error": None, "attempted": False, "attachment": False}
        if not self.settings.host or not self.settings.sender:
            return {"status": "FAILED", "recipient": email, "sent_at": None, "error": "SMTP is enabled but host/from is not configured", "attempted": True, "attachment": False}
        message = EmailMessage()
        readable_attack = str(incident["attack_type"]).replace("_", " ").title()
        message["Subject"] = f"[Aegis-Twin] {incident['severity']} Forensic Report — {incident['device_id']} — {readable_attack}"
        message["From"] = self.settings.sender
        message["To"] = email
        message.set_content("\n".join([
            "AEGIS-TWIN FORENSIC INCIDENT REPORT",
            f"Incident ID: {incident['incident_id']}",
            f"Device: {incident['device_id']} — {incident['device_name']}",
            f"Severity: {incident['severity']}",
            f"Attack / anomaly: {readable_attack}",
            f"MITRE: {self._mitre_text(incident)}",
            f"Minimum trust: {incident['minimum_trust']}",
            f"Detection time: {incident['detected_at']}",
            "The attached PDF contains the detection-time forensic snapshot and incident timeline.",
        ]))
        attached = False
        if pdf_path and pdf_path.exists() and pdf_path.stat().st_size <= 10 * 1024 * 1024:
            message.add_attachment(pdf_path.read_bytes(), maintype="application", subtype="pdf", filename=pdf_path.name)
            attached = True
        try:
            client = self.smtp_factory(self.settings.host, self.settings.port, timeout=self.settings.timeout_seconds)
            try:
                if self.settings.use_tls:
                    client.starttls()
                if self.settings.username:
                    client.login(self.settings.username, self.settings.password)
                client.send_message(message)
            finally:
                try:
                    client.quit()
                except Exception:
                    pass
            return {"status": "SENT", "recipient": email, "sent_at": self.clock().astimezone(timezone.utc).isoformat(), "error": None, "attempted": True, "attachment": attached}
        except smtplib.SMTPAuthenticationError:
            error_text = "SMTP authentication failed"
        except (TimeoutError, socket.timeout):
            error_text = "SMTP connection timed out"
        except (smtplib.SMTPException, OSError) as exc:
            error_text = f"SMTP delivery failed: {exc}"
        except Exception as exc:
            error_text = f"SMTP delivery failed unexpectedly: {type(exc).__name__}"
        return {"status": "FAILED", "recipient": email, "sent_at": None, "error": error_text, "attempted": True, "attachment": attached}
