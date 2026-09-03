from __future__ import annotations

from pathlib import Path

from app.services.auth import AuthService
from app.services.incidents import IncidentService
from app.services.notifications import NotificationService


class IncidentWorkflowService:
    def __init__(self, incidents: IncidentService, auth: AuthService,
                 notifications: NotificationService) -> None:
        self.incidents = incidents
        self.auth = auth
        self.notifications = notifications

    def visible_incidents(self, user: dict[str, object], **filters: str | None) -> list[dict[str, object]]:
        values = self.incidents.list(**filters)
        return values if user["role"] == "ADMIN" else [item for item in values if self.incidents.can_access(item, user)]

    def require_access(self, incident_id: str, user: dict[str, object]) -> dict[str, object]:
        incident = self.incidents.require(incident_id)
        if not self.incidents.can_access(incident, user):
            raise PermissionError("incident is not assigned to this user")
        return incident

    def assign(self, incident_id: str, assignee_user_id: str, actor: dict[str, object],
               reason: str | None = None) -> dict[str, object]:
        incident = self.incidents.require(incident_id)
        assignee = self.auth.get_user(assignee_user_id)
        if assignee is None or not assignee["active"]:
            raise ValueError("assignee does not exist or is inactive")
        if actor["role"] == "ADMIN":
            pass
        elif (
            actor["role"] == "ASSET_OWNER"
            and self.incidents.can_access(incident, actor)
            and assignee["role"] == "SME_VENDOR"
        ):
            pass
        else:
            raise PermissionError("this role cannot assign the incident to that user")
        incident = self.incidents.assign(incident_id, assignee, actor, reason)
        # Refresh the same report files from the now-persisted assignment. Email
        # is attempted only afterward and can never roll back assignment state.
        incident = self.incidents.generate_report(incident_id)
        report = incident["report"]
        assert isinstance(report, dict)
        pdf_path = Path(str(report["pdf_path"])) if report.get("pdf_ready") and report.get("pdf_path") else None
        history = incident.get("assignment_history")
        original_assigner = actor
        if isinstance(history, list) and history:
            recorded = history[-1].get("assigned_by")
            if isinstance(recorded, dict):
                original_assigner = recorded
        delivery = self.notifications.send_assignment(incident, assignee, original_assigner, pdf_path)
        return self.incidents.update_email(incident_id, delivery)

    def acknowledge(self, incident_id: str, actor: dict[str, object]) -> dict[str, object]:
        incident = self.require_access(incident_id, actor)
        if actor["role"] != "ADMIN" and str(incident["assigned_to_user_id"]) != str(actor["user_id"]):
            raise PermissionError("only the assignee or an administrator can acknowledge")
        return self.incidents.acknowledge(incident_id, actor)

    def add_note(self, incident_id: str, actor: dict[str, object], text: str) -> dict[str, object]:
        self.require_access(incident_id, actor)
        return self.incidents.add_note(incident_id, actor, text)

    def notes(self, incident_id: str, actor: dict[str, object]) -> list[dict[str, object]]:
        incident = self.require_access(incident_id, actor)
        return list(incident["notes"])  # type: ignore[arg-type]

    def email_report(self, incident_id: str, actor: dict[str, object]) -> dict[str, object]:
        incident = self.require_access(incident_id, actor)
        assignee_id = incident.get("assigned_to_user_id")
        if not assignee_id:
            raise ValueError("incident must be assigned before email can be sent")
        assignee = self.auth.get_user(str(assignee_id))
        if assignee is None or not assignee["active"]:
            raise ValueError("assigned user does not exist or is inactive")
        incident = self.incidents.generate_report(incident_id)
        report = incident["report"]
        assert isinstance(report, dict)
        pdf_path = Path(str(report["pdf_path"])) if report.get("pdf_ready") and report.get("pdf_path") else None
        history = incident.get("assignment_history")
        original_assigner = actor
        if isinstance(history, list) and history:
            recorded = history[-1].get("assigned_by")
            if isinstance(recorded, dict):
                original_assigner = recorded
        delivery = self.notifications.send_assignment(incident, assignee, original_assigner, pdf_path)
        return self.incidents.update_email(incident_id, delivery)
