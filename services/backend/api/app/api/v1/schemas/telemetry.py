from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.telemetry import TelemetryPoint, TelemetryWindow


class TelemetryPointPayload(BaseModel):
    packet_size: float = 0.45
    iat: float = 0.50
    payload_entropy: float = 0.35
    flow_symmetry: float = 0.60
    syn_rate: float = 0.0
    syn_ack_rate: float = 0.0
    ack_rate: float = 0.0
    incomplete_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    handshake_completion_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    unique_sources: float = Field(default=1.0, ge=0.0)
    unique_destination_ports: float = Field(default=1.0, ge=0.0)
    rejected_connections: float = Field(default=0.0, ge=0.0)
    reset_connections: float = Field(default=0.0, ge=0.0)
    orig_packets: float = Field(default=0.0, ge=0.0)
    resp_packets: float = Field(default=0.0, ge=0.0)
    orig_bytes: float = Field(default=0.0, ge=0.0)
    resp_bytes: float = Field(default=0.0, ge=0.0)
    connection_duration_mean: float = Field(default=0.0, ge=0.0)
    ssh_attempts: float = Field(default=0.0, ge=0.0)
    ssh_failures: float = Field(default=0.0, ge=0.0)
    capture_loss: float = Field(default=0.0, ge=0.0, le=1.0)

    def to_domain(self) -> TelemetryPoint:
        return TelemetryPoint(**self.model_dump())


class TelemetryWindowPayload(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    source: Literal["mock", "pi", "replay", "live_hardware", "recorded_replay", "xai_simulation"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_seconds: int = Field(default=20, ge=1, le=120)
    stale: bool = False
    service_healthy: bool = True
    attack_job_id: str | None = Field(default=None, max_length=128)
    sensor: str | None = Field(default=None, max_length=128)
    session_id: str | None = Field(default=None, max_length=128)
    unavailable_features: list[str] = Field(default_factory=list, max_length=21)
    points: list[TelemetryPointPayload] = Field(min_length=1, max_length=20)

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    def to_domain(self) -> TelemetryWindow:
        return TelemetryWindow(
            device_id=self.device_id,
            source=self.source,
            timestamp=self.timestamp,
            sequence_seconds=self.sequence_seconds,
            stale=self.stale,
            service_healthy=self.service_healthy,
            attack_job_id=self.attack_job_id,
            sensor=self.sensor,
            session_id=self.session_id,
            unavailable_features=tuple(self.unavailable_features),
            points=[point.to_domain() for point in self.points],
        )
