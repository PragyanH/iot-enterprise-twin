from __future__ import annotations

import asyncio
import json
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.v1.schemas.telemetry import TelemetryWindowPayload
from app.core.runtime import trust_service


router = APIRouter()


class ForensicRecipientPayload(BaseModel):
    email: str = Field(min_length=3, max_length=320)


@router.get("/notifications/recipient", summary="Get the configured forensic report recipient")
def notification_recipient() -> dict[str, object]:
    from app.core.runtime import notification_service
    return notification_service.recipient_status()


@router.post("/notifications/recipient", summary="Set the forensic report recipient")
def set_notification_recipient(payload: ForensicRecipientPayload) -> dict[str, object]:
    email = payload.email.strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(status_code=422, detail="email must be a valid address")
    from app.core.runtime import notification_service
    notification_service.set_recipient(email)
    return notification_service.recipient_status()


@router.post("/telemetry/windows", summary="Ingest one normalized telemetry window")
def ingest_window(payload: TelemetryWindowPayload) -> dict[str, object]:
    try:
        return trust_service.ingest(payload.to_domain()).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/devices/{device_id}/state", summary="Get the current hybrid trust state")
def device_state(device_id: str) -> dict[str, object]:
    try:
        return trust_service.state(device_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/devices/{device_id}/remediate", summary="Run the allowlisted remediation flow")
def remediate_device(device_id: str) -> dict[str, object]:
    try:
        if device_id == "PI-001":
            return trust_service.reset_pi_device(device_id)
        return trust_service.remediate(device_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError:
        # Fallback to direct device reset if no active incident is recorded
        return trust_service.reset_pi_device(device_id)



@router.post("/devices/{device_id}/simulate-attack", summary="Trigger a mock-device behavioral attack")
def simulate_mock_attack(device_id: str) -> dict[str, object]:
    try:
        return trust_service.trigger_mock_attack(device_id).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


async def _run_replay(scenario: str, interval_seconds: float) -> None:
    for window in trust_service.replay_windows(scenario):
        trust_service.ingest(window)
        await asyncio.sleep(interval_seconds)


@router.post("/demo/replay/{scenario}", summary="Start a deterministic Zeek-compatible demo replay")
async def start_replay(scenario: str, speed: float = 4.0) -> dict[str, object]:
    if speed <= 0 or speed > 20:
        raise HTTPException(status_code=422, detail="speed must be greater than 0 and at most 20")
    try:
        trust_service.replay_windows(scenario)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    asyncio.create_task(_run_replay(scenario, 1.0 / speed))
    return {"scenario": scenario, "status": "started", "speed": speed}


@router.get("/events/trust", summary="Stream trust-state changes with server-sent events")
async def trust_events(request: Request) -> StreamingResponse:
    async def stream():
        last_version = -1
        last_event_sequence = 0
        heartbeat = 0
        while not await request.is_disconnected():
            version = trust_service.version
            if version != last_version:
                operational_events = trust_service.events_since(last_event_sequence)
                if operational_events:
                    last_event_sequence = int(operational_events[-1]["sequence"])
                payload = {
                    "version": version,
                    "devices": trust_service.fleet(),
                    "operational_events": operational_events,
                }
                yield f"event: trust\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
                last_version = version
                heartbeat = 0
            else:
                heartbeat += 1
                if heartbeat >= 20:
                    yield ": heartbeat\n\n"
                    heartbeat = 0
            await asyncio.sleep(0.5)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
