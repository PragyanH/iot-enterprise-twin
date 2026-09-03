from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.api.dependencies.auth import current_user
from app.core.runtime import notification_service, trust_service, workflow_service


router = APIRouter()


class AssignmentPayload(BaseModel):
    assignee_user_id: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)


class NotePayload(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


def _workflow_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/incidents", summary="List persistent security incidents")
def list_incidents(
    device_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    source_mode: str | None = Query(default=None),
    user: dict[str, object] = Depends(current_user),
) -> dict[str, object]:
    incidents = workflow_service.visible_incidents(
        user,
        device_id=device_id, status=status, severity=severity, source_mode=source_mode
    )
    return {"count": len(incidents), "incidents": incidents}


@router.get("/incidents/{incident_id}", summary="Get a persistent incident")
def incident_details(
    incident_id: str, user: dict[str, object] = Depends(current_user)
) -> dict[str, object]:
    try:
        return workflow_service.require_access(incident_id, user)
    except (KeyError, PermissionError) as exc:
        raise _workflow_error(exc) from exc


@router.get("/incidents/{incident_id}/timeline", summary="Get the ordered incident timeline")
def incident_timeline(
    incident_id: str, user: dict[str, object] = Depends(current_user)
) -> dict[str, object]:
    try:
        incident = workflow_service.require_access(incident_id, user)
    except (KeyError, PermissionError) as exc:
        raise _workflow_error(exc) from exc
    return {"incident_id": incident_id, "timeline": incident["timeline"]}


@router.get("/incidents/{incident_id}/report", summary="Get or refresh the idempotent forensic report")
def incident_report(
    incident_id: str, user: dict[str, object] = Depends(current_user)
) -> FileResponse:
    try:
        workflow_service.require_access(incident_id, user)
        incident = trust_service.incidents.generate_report(incident_id)
    except (KeyError, PermissionError) as exc:
        raise _workflow_error(exc) from exc
    report = incident["report"]
    assert isinstance(report, dict)
    if not report.get("report_ready") or not report.get("path"):
        raise HTTPException(status_code=503, detail={"status": report.get("status"), "error": report.get("error")})
    path = Path(str(report["path"]))
    if not path.exists():
        raise HTTPException(status_code=503, detail="report file is unavailable")
    return FileResponse(path, media_type="text/html", filename=path.name)


@router.get("/incidents/{incident_id}/report.pdf", summary="Download the forensic PDF")
def incident_pdf_report(
    incident_id: str, user: dict[str, object] = Depends(current_user)
) -> FileResponse:
    try:
        workflow_service.require_access(incident_id, user)
        incident = trust_service.incidents.generate_report(incident_id)
    except (KeyError, PermissionError) as exc:
        raise _workflow_error(exc) from exc
    report = incident["report"]
    assert isinstance(report, dict)
    if not report.get("pdf_ready") or not report.get("pdf_path"):
        raise HTTPException(
            status_code=503,
            detail={"status": report.get("pdf_status"), "error": report.get("pdf_error")},
        )
    path = Path(str(report["pdf_path"]))
    if not path.exists():
        raise HTTPException(status_code=503, detail="PDF report file is unavailable")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.post("/incidents/{incident_id}/assign", summary="Assign or delegate an incident")
def assign_incident(
    incident_id: str,
    payload: AssignmentPayload,
    user: dict[str, object] = Depends(current_user),
) -> dict[str, object]:
    try:
        return workflow_service.assign(incident_id, payload.assignee_user_id, user, payload.reason)
    except (KeyError, PermissionError, ValueError) as exc:
        raise _workflow_error(exc) from exc


@router.post("/incidents/{incident_id}/acknowledge", summary="Acknowledge an assignment")
def acknowledge_incident(
    incident_id: str, user: dict[str, object] = Depends(current_user)
) -> dict[str, object]:
    try:
        return workflow_service.acknowledge(incident_id, user)
    except (KeyError, PermissionError, ValueError) as exc:
        raise _workflow_error(exc) from exc


@router.post("/incidents/{incident_id}/notes", status_code=201, summary="Append an investigation note")
def add_incident_note(
    incident_id: str,
    payload: NotePayload,
    user: dict[str, object] = Depends(current_user),
) -> dict[str, object]:
    try:
        return workflow_service.add_note(incident_id, user, payload.text)
    except (KeyError, PermissionError, ValueError) as exc:
        raise _workflow_error(exc) from exc


@router.get("/incidents/{incident_id}/notes", summary="List append-only investigation notes")
def incident_notes(
    incident_id: str, user: dict[str, object] = Depends(current_user)
) -> dict[str, object]:
    try:
        notes = workflow_service.notes(incident_id, user)
    except (KeyError, PermissionError) as exc:
        raise _workflow_error(exc) from exc
    return {"incident_id": incident_id, "count": len(notes), "notes": notes}


@router.post("/incidents/{incident_id}/email-report", summary="Retry the assignment/report email")
def email_incident_report(
    incident_id: str, user: dict[str, object] = Depends(current_user)
) -> dict[str, object]:
    try:
        return workflow_service.email_report(incident_id, user)
    except (KeyError, PermissionError, ValueError) as exc:
        raise _workflow_error(exc) from exc


@router.get("/system/capabilities", summary="Get safe runtime and remediation capabilities")
def system_capabilities() -> dict[str, object]:
    return {
        "remediation": trust_service.capabilities(),
        "authentication": {"enabled": True, "roles": ["ADMIN", "ASSET_OWNER", "SME_VENDOR"]},
        "email": notification_service.capability(),
        "reports": {"html": True, "pdf": True},
    }
