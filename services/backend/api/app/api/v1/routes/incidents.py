from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.runtime import trust_service


router = APIRouter()


@router.get("/incidents", summary="List persistent security incidents")
def list_incidents(
    device_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    source_mode: str | None = Query(default=None),
) -> dict[str, object]:
    incidents = trust_service.incidents.list(
        device_id=device_id, status=status, severity=severity, source_mode=source_mode
    )
    return {"count": len(incidents), "incidents": incidents}


@router.get("/incidents/{incident_id}", summary="Get a persistent incident")
def incident_details(incident_id: str) -> dict[str, object]:
    try:
        return trust_service.incidents.require(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/incidents/{incident_id}/timeline", summary="Get the ordered incident timeline")
def incident_timeline(incident_id: str) -> dict[str, object]:
    try:
        incident = trust_service.incidents.require(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"incident_id": incident_id, "timeline": incident["timeline"]}


@router.get("/incidents/{incident_id}/report", summary="Get or refresh the idempotent forensic report")
def incident_report(incident_id: str) -> FileResponse:
    try:
        incident = trust_service.incidents.generate_report(incident_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    report = incident["report"]
    assert isinstance(report, dict)
    if not report.get("report_ready") or not report.get("path"):
        raise HTTPException(status_code=503, detail={"status": report.get("status"), "error": report.get("error")})
    path = Path(str(report["path"]))
    if not path.exists():
        raise HTTPException(status_code=503, detail="report file is unavailable")
    return FileResponse(path, media_type="text/html", filename=path.name)


@router.get("/system/capabilities", summary="Get safe runtime and remediation capabilities")
def system_capabilities() -> dict[str, object]:
    return {"remediation": trust_service.capabilities()}
