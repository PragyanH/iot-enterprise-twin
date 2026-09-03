from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal


SourceKind = Literal[
    "mock",
    "pi",
    "replay",
    "live_hardware",
    "recorded_replay",
    "xai_simulation",
]
TrustState = Literal["BOOTSTRAP", "HEALTHY", "SUSPICIOUS", "ATTACK", "RECOVERING", "STALE"]


FEATURE_NAMES = (
    "packet_size",
    "iat",
    "payload_entropy",
    "flow_symmetry",
    "syn_rate",
    "syn_ack_rate",
    "ack_rate",
    "incomplete_ratio",
    "handshake_completion_ratio",
    "unique_sources",
    "unique_destination_ports",
    "rejected_connections",
    "reset_connections",
    "orig_packets",
    "resp_packets",
    "orig_bytes",
    "resp_bytes",
    "connection_duration_mean",
    "ssh_attempts",
    "ssh_failures",
    "capture_loss",
)


@dataclass(slots=True)
class TelemetryPoint:
    packet_size: float = 0.45
    iat: float = 0.50
    payload_entropy: float = 0.35
    flow_symmetry: float = 0.60
    syn_rate: float = 0.0
    syn_ack_rate: float = 0.0
    ack_rate: float = 0.0
    incomplete_ratio: float = 0.0
    handshake_completion_ratio: float = 1.0
    unique_sources: float = 1.0
    unique_destination_ports: float = 1.0
    rejected_connections: float = 0.0
    reset_connections: float = 0.0
    orig_packets: float = 0.0
    resp_packets: float = 0.0
    orig_bytes: float = 0.0
    resp_bytes: float = 0.0
    connection_duration_mean: float = 0.0
    ssh_attempts: float = 0.0
    ssh_failures: float = 0.0
    capture_loss: float = 0.0

    def value(self, feature: str) -> float:
        return float(getattr(self, feature))

    def to_dict(self) -> dict[str, float]:
        return {key: float(value) for key, value in asdict(self).items()}


@dataclass(slots=True)
class TelemetryWindow:
    device_id: str
    source: SourceKind
    points: list[TelemetryPoint]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_seconds: int = 20
    stale: bool = False
    service_healthy: bool = True
    attack_job_id: str | None = None
    sensor: str | None = None
    session_id: str | None = None
    unavailable_features: tuple[str, ...] = ()

    @property
    def latest(self) -> TelemetryPoint:
        if not self.points:
            raise ValueError("telemetry window must contain at least one point")
        return self.points[-1]


@dataclass(slots=True)
class SignalContribution:
    feature: str
    score: float
    direction: str
    severity: str = "low"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class DevicePrediction:
    device_id: str
    source: SourceKind
    trust: float
    state: TrustState
    attack_type: str
    confidence: float
    risk: float
    reconstruction_error: float
    latent_uncertainty: float
    jsd: float
    rule_risk: float
    classifier_risk: float
    vae_risk: float
    baseline_risk: float
    attention_weights: list[float]
    top_anomalies: list[SignalContribution]
    current_features: dict[str, float]
    baseline_features: dict[str, float]
    timestamp: datetime
    model_version: str = "aegis-hybrid-trust/v1"
    baseline_version: str = "v1"
    telemetry_quality: str = "good"
    model_backends: dict[str, str] = field(default_factory=dict)
    source_mode: str = "mock"
    sensor: str = "aegis-simulator"
    raw_features: dict[str, float] = field(default_factory=dict)
    canonical_features: dict[str, float] = field(default_factory=dict)
    feature_deviations: dict[str, dict[str, float | str | bool | None]] = field(default_factory=dict)
    rule: dict[str, object] = field(default_factory=dict)
    jsd_by_feature: dict[str, float] = field(default_factory=dict)
    canonicalization_version: str = "none"
    canonicalization_applied: dict[str, dict[str, float | str]] = field(default_factory=dict)
    feature_availability: dict[str, dict[str, object]] = field(default_factory=dict)
    classifier: dict[str, object] = field(default_factory=dict)
    temporal: dict[str, object] = field(default_factory=dict)
    detectors: dict[str, float] = field(default_factory=dict)
    trust_calculation: dict[str, object] = field(default_factory=dict)
    detection_mode: str = "normal"
    known_attack_risk: float = 0.0
    unknown_anomaly_score: float = 0.0
    classification: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "device_id": self.device_id,
            "source": self.source,
            "trust": self.trust,
            "state": self.state,
            "status": self.state,
            "attack_type": self.attack_type,
            "confidence": self.confidence,
            "risk": self.risk,
            "reconstruction_error": self.reconstruction_error,
            "latent_uncertainty": self.latent_uncertainty,
            "jsd": self.jsd,
            "rule_risk": self.rule_risk,
            "classifier_risk": self.classifier_risk,
            "vae_risk": self.vae_risk,
            "baseline_risk": self.baseline_risk,
            "attention_weights": self.attention_weights,
            "top_anomalies": [item.to_dict() for item in self.top_anomalies],
            "current_features": self.current_features,
            "baseline_features": self.baseline_features,
            "timestamp": self.timestamp.isoformat(),
            "model_version": self.model_version,
            "baseline_version": self.baseline_version,
            "telemetry_quality": self.telemetry_quality,
            "model_backends": self.model_backends,
            "source_mode": self.source_mode,
            "sensor": self.sensor,
            "raw_features": self.raw_features,
            "canonical_features": self.canonical_features,
            "feature_deviations": self.feature_deviations,
            "rule": self.rule,
            "jsd_by_feature": self.jsd_by_feature,
            "canonicalization_version": self.canonicalization_version,
            "canonicalization_applied": self.canonicalization_applied,
            "feature_availability": self.feature_availability,
            "classifier": self.classifier,
            "temporal": self.temporal,
            "detectors": self.detectors,
            "trust_calculation": self.trust_calculation,
            "detection_mode": self.detection_mode,
            "known_attack_risk": self.known_attack_risk,
            "unknown_anomaly_score": self.unknown_anomaly_score,
            "classification": self.classification,
        }
