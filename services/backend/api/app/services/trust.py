from __future__ import annotations

import json
import logging
import math
import threading
import tempfile
import shutil
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.domain.telemetry import DevicePrediction, TelemetryPoint, TelemetryWindow
from app.ml.hybrid_engine import DEFAULT_PROFILES, DeviceProfile, HybridTrustEngine, clamp, load_profiles
from app.rules.engine import load_rule_engine
from app.services.incidents import IncidentRepository, IncidentService
from app.services.remediation import (
    AttackControllerStopProvider,
    MockResetProvider,
    ReplayStopProvider,
)
from app.telemetry.canonicalization import FeatureCanonicalizer


LOGGER = logging.getLogger("aegis.trust")


def _log_event(event: str, **fields: object) -> None:
    LOGGER.info(json.dumps({"event": event, **fields}, separators=(",", ":"), default=str))


@dataclass(slots=True)
class DeviceRuntime:
    prediction: DevicePrediction
    points: deque[TelemetryPoint]
    previous_risk: float = 0.02
    recovering: bool = False
    recovery_clean_windows: int = 0
    mock_attack: bool = False
    tick: int = 0
    attack_job_id: str | None = None
    last_live_seen: datetime | None = None
    stale_since: datetime | None = None


# Backward-compatible public name retained for existing integrations/tests.
AttackController = AttackControllerStopProvider


def _normal_point(profile: DeviceProfile, tick: int) -> TelemetryPoint:
    values: dict[str, float] = {}
    for index, feature in enumerate(profile.feature_names):
        phase = (tick + index * 3) / 4.0
        variation = math.sin(phase) * profile.deviation[feature] * 0.18
        value = max(0.0, profile.baseline[feature] + variation)
        if feature in {
            "payload_entropy",
            "flow_symmetry",
            "incomplete_ratio",
            "handshake_completion_ratio",
            "capture_loss",
        }:
            value = min(1.0, value)
        values[feature] = value
    return TelemetryPoint(**values)


def _mock_attack_point(profile: DeviceProfile, tick: int) -> TelemetryPoint:
    point = _normal_point(profile, tick)
    point.packet_size = clamp(profile.baseline["packet_size"] + 0.35, 0.0, 1.0)
    point.iat = clamp(profile.baseline["iat"] - 0.28, 0.0, 1.0)
    point.payload_entropy = clamp(profile.baseline["payload_entropy"] + 0.32, 0.0, 1.0)
    point.flow_symmetry = clamp(profile.baseline["flow_symmetry"] - 0.38, 0.0, 1.0)
    return point


class HybridTrustService:
    def __init__(
        self,
        model_path: Path,
        attack_controller: AttackController,
        *,
        rules_path: Path | None = None,
        canonicalization_path: Path | None = None,
        intelligence_path: Path | None = None,
        incident_db_path: Path | None = None,
        reports_dir: Path | None = None,
        recovery_clean_windows_required: int = 3,
        stale_timeout_seconds: float = 3.0,
        clock: Callable[[], datetime] | None = None,
        tshark_path: str = "",
        tshark_interface: str = "",
    ) -> None:
        baseline_path = model_path / "baselines.json"
        profiles = load_profiles(baseline_path) if baseline_path.exists() else DEFAULT_PROFILES
        repository_root = model_path.parents[2]
        resolved_rules = rules_path or repository_root / "rules" / "aegis_rules.yaml"
        resolved_canonicalization = canonicalization_path or model_path / "canonicalization.json"
        resolved_intelligence = intelligence_path or model_path / "intelligence.json"
        self.canonicalizer = FeatureCanonicalizer.from_path(resolved_canonicalization)
        self.engine = HybridTrustEngine(
            profiles,
            model_path / "xgboost.json",
            model_path,
            load_rule_engine(resolved_rules),
            resolved_intelligence,
        )
        self.attack_controller = attack_controller
        self.recovery_clean_windows_required = max(1, int(recovery_clean_windows_required))
        self.stale_timeout_seconds = max(0.1, float(stale_timeout_seconds))
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.tshark_path = tshark_path
        self.tshark_interface = tshark_interface
        self._lock = threading.RLock()
        self._event_lock = threading.RLock()
        self._version = 0
        self._event_sequence = 0
        self._operational_events: deque[dict[str, object]] = deque(maxlen=500)
        self._temporary_storage = tempfile.TemporaryDirectory(prefix="aegis-incidents-") if incident_db_path is None else None
        storage_root = Path(self._temporary_storage.name) if self._temporary_storage else incident_db_path.parent
        resolved_db = incident_db_path or storage_root / "aegis_incidents.db"
        resolved_reports = reports_dir or storage_root / "reports"
        self.incidents = IncidentService(
            IncidentRepository(resolved_db), resolved_reports,
            clock=self.clock, event_sink=self._emit_operational_event,
        )
        self._devices: dict[str, DeviceRuntime] = {}
        for profile in self.engine.profiles.values():
            points = deque((_normal_point(profile, tick) for tick in range(20)), maxlen=20)
            prediction = self.engine.score(
                TelemetryWindow(
                    device_id=profile.device_id,
                    # PI-001 starts from a deterministic baseline seed until the
                    # first sensor/replay window arrives. Never label that seed
                    # as physical live telemetry.
                    source="mock" if profile.source == "pi" else profile.source,  # type: ignore[arg-type]
                    points=list(points),
                    sensor="aegis-simulator",
                ),
                raw_latest=points[-1],
                canonicalization_version=self.canonicalizer.version,
            )
            self._devices[profile.device_id] = DeviceRuntime(prediction=prediction, points=points)

    def _emit_operational_event(self, event_type: str, metadata: dict[str, object]) -> None:
        # Separate lock avoids incident-lock ↔ trust-lock inversion when a
        # report request and telemetry ingestion happen concurrently.
        with self._event_lock:
            self._event_sequence += 1
            self._operational_events.append({
                "sequence": self._event_sequence,
                "timestamp": self.clock().astimezone(timezone.utc).isoformat(),
                "type": event_type,
                "metadata": metadata,
            })
            self._version += 1

    def events_since(self, sequence: int) -> list[dict[str, object]]:
        with self._event_lock:
            return [event for event in self._operational_events if int(event["sequence"]) > sequence]

    @property
    def version(self) -> int:
        with self._event_lock:
            return self._version

    def ingest(self, window: TelemetryWindow) -> DevicePrediction:
        with self._lock:
            runtime = self._devices.get(window.device_id)
            if runtime is None:
                raise KeyError(f"unknown device: {window.device_id}")
            previous_state = runtime.prediction.state
            previous_trust = runtime.prediction.trust
            was_stale = runtime.stale_since is not None
            runtime.attack_job_id = window.attack_job_id or runtime.attack_job_id
            profile = self.engine.profile(window.device_id)
            unknown_unavailable = set(window.unavailable_features).difference(
                set(profile.feature_names).union({"payload_entropy"})
            )
            if unknown_unavailable:
                raise ValueError(f"unknown unavailable features: {sorted(unknown_unavailable)}")
            neutral_values = {
                feature: profile.baseline[feature]
                for feature in window.unavailable_features
                if feature in profile.baseline
            }
            latest_result = None
            for point in window.points:
                latest_result = self.canonicalizer.transform(
                    point,
                    apply_attack_buckets=profile.source == "pi",
                    neutral_values=neutral_values,
                )
                runtime.points.append(latest_result.canonical)
            if latest_result is None:
                raise ValueError("telemetry window must contain at least one point")
            normalized_window = TelemetryWindow(
                device_id=window.device_id,
                source=window.source,
                points=list(runtime.points),
                timestamp=window.timestamp,
                sequence_seconds=window.sequence_seconds,
                stale=window.stale,
                service_healthy=window.service_healthy,
                attack_job_id=runtime.attack_job_id,
                sensor=window.sensor,
                session_id=window.session_id,
                unavailable_features=window.unavailable_features,
            )
            prediction = self.engine.score(
                normalized_window,
                previous_trust=runtime.prediction.trust,
                previous_risk=runtime.previous_risk,
                recovering=runtime.recovering,
                recovery_clean_windows=runtime.recovery_clean_windows,
                recovery_clean_windows_required=self.recovery_clean_windows_required,
                raw_latest=latest_result.raw,
                canonicalization_version=latest_result.version,
                supplied_sensor=window.sensor,
                canonicalization_applied=latest_result.applied,
                unavailable_features=set(window.unavailable_features),
            )
            runtime.prediction = prediction
            runtime.previous_risk = prediction.risk
            if prediction.source_mode == "live_hardware":
                runtime.last_live_seen = self.clock().astimezone(timezone.utc)
                runtime.stale_since = None
                if was_stale:
                    self._emit_operational_event("device_live_again", {"device_id": window.device_id, "state": prediction.state})
                    _log_event("device_live_again", device_id=window.device_id, state=prediction.state)
            active_incident = self.incidents.observe(profile.name, prediction.to_dict(), previous_trust)
            if runtime.recovering:
                clean_recovery = (
                    prediction.state in {"RECOVERING", "HEALTHY"}
                    and prediction.telemetry_quality == "good"
                    and not bool(prediction.rule.get("matched"))
                    and not bool(prediction.classifier.get("accepted_as_known_attack"))
                    and prediction.unknown_anomaly_score < 0.72
                )
                if clean_recovery:
                    runtime.recovery_clean_windows += 1
                    verified = (
                        runtime.recovery_clean_windows >= self.recovery_clean_windows_required
                        and prediction.state == "HEALTHY"
                        and prediction.trust >= 95
                    )
                    if verified:
                        runtime.recovering = False
                else:
                    runtime.recovery_clean_windows = 0
                    verified = False
                if active_incident and active_incident["status"] in {"CONTAINED", "RECOVERING"}:
                    self.incidents.recovery_progress(
                        str(active_incident["incident_id"]),
                        runtime.recovery_clean_windows,
                        self.recovery_clean_windows_required,
                        prediction.trust,
                        clean_recovery,
                        verified,
                    )
            with self._event_lock:
                self._version += 1
            if prediction.state != previous_state:
                _log_event(
                    "device_state_changed",
                    device_id=window.device_id,
                    previous_state=previous_state,
                    state=prediction.state,
                    trust=prediction.trust,
                    source_mode=prediction.source_mode,
                )
                if prediction.rule.get("matched"):
                    _log_event(
                        "rule_matched",
                        device_id=window.device_id,
                        rule_id=prediction.rule.get("rule_id"),
                        attack_type=prediction.attack_type,
                    )
            return prediction

    def tick_mock_devices(self) -> None:
        with self._lock:
            mock_ids = [
                device_id
                for device_id, profile in self.engine.profiles.items()
                if profile.source == "mock"
            ]
        for device_id in mock_ids:
            with self._lock:
                runtime = self._devices[device_id]
                profile = self.engine.profile(device_id)
                runtime.tick += 1
                point = _mock_attack_point(profile, runtime.tick) if runtime.mock_attack else _normal_point(profile, runtime.tick)
            self.ingest(TelemetryWindow(device_id=device_id, source="mock", points=[point]))

    def trigger_mock_attack(self, device_id: str) -> DevicePrediction:
        with self._lock:
            profile = self.engine.profile(device_id)
            if profile.source != "mock":
                raise ValueError("mock attack controls are only available for mock devices")
            runtime = self._devices[device_id]
            runtime.mock_attack = True
            runtime.recovering = False
            runtime.recovery_clean_windows = 0
            attack_points = [_mock_attack_point(profile, runtime.tick + offset) for offset in range(1, 21)]
        return self.ingest(TelemetryWindow(device_id=device_id, source="mock", points=attack_points))

    def reset_pi_device(self, device_id: str = "PI-001") -> dict[str, Any]:
        with self._lock:
            runtime = self._devices.get(device_id)
            if runtime is None:
                raise KeyError(f"unknown device: {device_id}")
            profile = self.engine.profile(device_id)
            runtime.mock_attack = False
            runtime.recovering = False
            runtime.recovery_clean_windows = 0
            runtime.attack_job_id = None
            runtime.points.clear()
            for tick in range(20):
                runtime.points.append(_normal_point(profile, tick))
            normal_window = TelemetryWindow(
                device_id=device_id,
                source="mock" if profile.source == "pi" else profile.source,
                points=list(runtime.points),
                sensor="aegis-simulator",
            )
            prediction = self.engine.score(
                normal_window,
                raw_latest=runtime.points[-1],
                canonicalization_version=self.canonicalizer.version,
            )
            runtime.prediction = prediction
            runtime.previous_risk = prediction.risk
            with self._event_lock:
                self._version += 1
            _log_event("pi_device_remediated", device_id=device_id, trust=prediction.trust)
            return prediction.to_dict()

    def remediate(self, device_id: str) -> dict[str, Any]:

        with self._lock:
            profile = self.engine.profile(device_id)
            runtime = self._devices[device_id]
            incident = self.incidents.repository.active_for_device(device_id)
            if incident is None:
                raise ValueError("no active incident exists for this device")
            incident_id = str(incident["incident_id"])
            existing_remediation = incident["remediation"]
            assert isinstance(existing_remediation, dict)
            if existing_remediation.get("success") is True:
                return {
                    "incident_id": incident_id,
                    "device_id": device_id,
                    "requested_action": "stop_registered_attack_job" if profile.source == "pi" else "reset_mock_generator",
                    "provider": existing_remediation.get("provider"),
                    "phase": existing_remediation.get("phase"),
                    "success": True,
                    "idempotent": True,
                    "started_at": existing_remediation.get("started_at"),
                    "completion_timestamp": existing_remediation.get("completed_at"),
                    "error": None,
                    "state": runtime.prediction.state,
                    "target_trust": 97.0,
                    "controller": existing_remediation.get("controller_result", {}),
                    "provider_result": existing_remediation.get("provider_result", {}),
                    "recovery_verification": incident["recovery_verification"],
                    "prediction": runtime.prediction.to_dict(),
                }
            started_at = self.clock().astimezone(timezone.utc).isoformat()
            remediation = incident["remediation"]
            assert isinstance(remediation, dict)
            remediation.update({"requested": True, "started_at": started_at})
            self.incidents.repository.save(incident)
            self.incidents.remediation_event(
                incident_id, "REMEDIATION_REQUESTED", "Remediation requested",
                "A controlled containment action was requested.", status="CONTAINMENT_REQUESTED",
            )
            self._emit_operational_event("remediation_requested", {"incident_id": incident_id, "device_id": device_id})
            if profile.source == "mock":
                runtime.mock_attack = False
                provider = MockResetProvider()
                result = provider.execute()
                controller_result = result.to_dict()
            elif runtime.prediction.source_mode == "recorded_replay":
                provider = ReplayStopProvider()
                result = provider.execute(runtime.attack_job_id)
                # Preserve the legacy controller field honestly: no physical
                # controller was contacted for a recorded replay.
                controller_result = self.attack_controller.stop(runtime.attack_job_id)
            else:
                provider = self.attack_controller
                result = provider.execute(runtime.attack_job_id)
                controller_result = result.to_dict()
            incident = self.incidents.require(incident_id)
            remediation = incident["remediation"]
            assert isinstance(remediation, dict)
            remediation["provider"] = provider.provider_id
            self.incidents.repository.save(incident)
            self.incidents.remediation_event(
                incident_id, "APPLYING_POLICY", "Containment policy started",
                f"Provider {provider.provider_id} started.",
            )
            _log_event("remediation_provider_started", incident_id=incident_id, device_id=device_id, provider=provider.provider_id)
            action_phase = {
                "attack_controller_stop": "TERMINATING_MALICIOUS_SESSION",
                "replay_stop": "TERMINATING_REPLAY_STREAM",
                "mock_generator_reset": "RESETTING_MOCK_GENERATOR",
            }[provider.provider_id]
            self.incidents.remediation_event(
                incident_id, action_phase, "Applying containment",
                f"Provider outcome: {result.outcome}.", {"provider_result": result.to_dict()},
            )
            _log_event(
                "remediation_requested",
                incident_id=incident_id,
                device_id=device_id,
                job_id=runtime.attack_job_id,
                provider=provider.provider_id,
                success=result.success,
                reason=result.outcome,
            )
            completed_at = self.clock().astimezone(timezone.utc).isoformat()
            incident = self.incidents.require(incident_id)
            remediation = incident["remediation"]
            assert isinstance(remediation, dict)
            remediation.update({
                "success": result.success, "outcome": result.outcome,
                "completed_at": completed_at, "error": result.error,
                "provider_result": result.to_dict(),
                "controller_result": controller_result,
            })
            self.incidents.repository.save(incident)
            if result.success:
                completed_phase, completed_title = {
                    "attack_controller_stop": ("MALICIOUS_SESSION_TERMINATED", "Registered attack job terminated"),
                    "replay_stop": ("REPLAY_STREAM_TERMINATED", "Replay attack stream terminated"),
                    "mock_generator_reset": ("MOCK_GENERATOR_RESET", "Mock generator reset"),
                }[provider.provider_id]
                self.incidents.remediation_event(
                    incident_id, completed_phase, completed_title,
                    f"Provider confirmed outcome: {result.outcome}.", {"provider_result": result.to_dict()},
                )
                self.incidents.remediation_event(
                    incident_id, "CONTAINED", "Containment completed",
                    f"{provider.provider_id} completed successfully.", status="CONTAINED",
                )
                runtime.recovering = True
                runtime.recovery_clean_windows = 0
                # Detection-time evidence is already persisted. Only after a
                # successful provider outcome do we clear attack-contaminated
                # temporal samples and begin a new verification epoch.
                runtime.points.clear()
                self.incidents.remediation_event(
                    incident_id, "RESETTING_TEMPORAL_CONTEXT", "Temporal context reset",
                    "The rolling inference buffer was cleared after containment.",
                )
                self.incidents.remediation_event(
                    incident_id, "VERIFYING_RECOVERY", "Recovery verification started",
                    f"Waiting for {self.recovery_clean_windows_required} consecutive clean hybrid windows.", status="RECOVERING",
                )
                self._emit_operational_event("remediation_success", {"incident_id": incident_id, "device_id": device_id, "provider": provider.provider_id})
                _log_event("remediation_success", incident_id=incident_id, device_id=device_id, provider=provider.provider_id)
            else:
                runtime.recovering = False
                runtime.recovery_clean_windows = 0
                self.incidents.remediation_event(
                    incident_id, "FAILED", "Remediation failed",
                    f"Containment did not succeed: {result.outcome}.", {"error": result.error}, status="OPEN",
                )
                self._emit_operational_event("remediation_failure", {"incident_id": incident_id, "device_id": device_id, "outcome": result.outcome})
                _log_event("remediation_failure", incident_id=incident_id, device_id=device_id, outcome=result.outcome)

        if profile.source == "mock" and result.success:
            clean_points = [_normal_point(profile, runtime.tick + offset) for offset in range(1, 21)]
            prediction = self.ingest(TelemetryWindow(device_id=device_id, source="mock", points=clean_points))
        else:
            prediction = runtime.prediction
        return {
            "incident_id": incident_id,
            "device_id": device_id,
            "requested_action": "stop_registered_attack_job" if profile.source == "pi" else "reset_mock_generator",
            "provider": provider.provider_id,
            "phase": "VERIFYING_RECOVERY" if result.success else "FAILED",
            "success": result.success,
            "started_at": started_at,
            "completion_timestamp": completed_at,
            "error": result.error,
            "state": "RECOVERING" if result.success else prediction.state,
            "target_trust": 97.0,
            "controller": controller_result,
            "provider_result": result.to_dict(),
            "recovery_verification": self.incidents.require(incident_id)["recovery_verification"],
            "prediction": prediction.to_dict(),
        }

    def state(self, device_id: str) -> dict[str, Any]:
        self.refresh_staleness()
        with self._lock:
            profile = self.engine.profile(device_id)
            runtime = self._devices[device_id]
            payload = runtime.prediction.to_dict()
            now = self.clock().astimezone(timezone.utc)
            seconds_since = (
                max(0.0, (now - runtime.last_live_seen).total_seconds())
                if runtime.last_live_seen else None
            )
            active = self.incidents.repository.active_for_device(device_id)
            payload.update({
                "name": profile.name, "sector": profile.sector,
                "last_seen": runtime.last_live_seen.isoformat() if runtime.last_live_seen else None,
                "seconds_since_last_seen": round(seconds_since, 3) if seconds_since is not None else None,
                "stale_since": runtime.stale_since.isoformat() if runtime.stale_since else None,
                "active_incident_id": active["incident_id"] if active else None,
                "recovery_progress": {
                    "clean_windows_required": self.recovery_clean_windows_required,
                    "clean_windows_observed": runtime.recovery_clean_windows,
                    "recovery_threshold": 95,
                },
            })
            return payload

    def fleet(self) -> list[dict[str, Any]]:
        self.refresh_staleness()
        with self._lock:
            result = []
            for device_id, runtime in self._devices.items():
                profile = self.engine.profile(device_id)
                status = {
                    "HEALTHY": "Healthy",
                    "ATTACK": "Compromised",
                    "SUSPICIOUS": "Monitoring",
                    "RECOVERING": "Recovering",
                    "STALE": "Telemetry delayed",
                    "BOOTSTRAP": "Bootstrap",
                }[runtime.prediction.state]
                result.append(
                    {
                        "id": device_id,
                        "name": profile.name,
                        "sector": profile.sector,
                        "source": profile.source,
                        "source_mode": runtime.prediction.source_mode,
                        "sensor": runtime.prediction.sensor,
                        "status": status,
                        "trust": round(runtime.prediction.trust),
                        "state": runtime.prediction.state,
                        "attack_type": runtime.prediction.attack_type,
                        "confidence": runtime.prediction.confidence,
                        "updated_at": runtime.prediction.timestamp.isoformat(),
                        "last_seen": runtime.last_live_seen.isoformat() if runtime.last_live_seen else None,
                        "stale_since": runtime.stale_since.isoformat() if runtime.stale_since else None,
                        "active_incident_id": (
                            active["incident_id"]
                            if (active := self.incidents.repository.active_for_device(device_id)) else None
                        ),
                    }
                )
            return result

    def refresh_staleness(self) -> None:
        now = self.clock().astimezone(timezone.utc)
        with self._lock:
            for device_id, runtime in self._devices.items():
                if runtime.last_live_seen is None or runtime.prediction.source_mode != "live_hardware":
                    continue
                elapsed = (now - runtime.last_live_seen).total_seconds()
                if elapsed > self.stale_timeout_seconds and runtime.stale_since is None:
                    runtime.stale_since = now
                    runtime.prediction = replace(
                        runtime.prediction,
                        state="STALE",
                        telemetry_quality="stale",
                        attack_type="none",
                        detection_mode="stale",
                    )
                    self._emit_operational_event(
                        "device_stale",
                        {"device_id": device_id, "seconds_since_last_seen": round(elapsed, 3)},
                    )
                    _log_event("device_stale", device_id=device_id, seconds_since_last_seen=elapsed)

    def capabilities(self) -> dict[str, object]:
        controller = self.attack_controller.capability()
        try:
            self.incidents.reports_dir.mkdir(parents=True, exist_ok=True)
            forensic_writable = self.incidents.reports_dir.is_dir()
        except OSError:
            forensic_writable = False
        pi = self._devices["PI-001"]
        return {
            "live_sensor_configured": bool(self.tshark_interface),
            "pi_telemetry_live": pi.last_live_seen is not None and pi.stale_since is None,
            "attack_controller_configured": bool(controller["available"]),
            "attack_controller_reachable": None,
            "providers": [
                controller,
                ReplayStopProvider().capability(),
                MockResetProvider().capability(),
                {"id": "network_isolation", "available": False, "mode": "not_configured"},
            ],
            "replay_available": True,
            "forensic_storage_writable": forensic_writable,
            "model_loaded": True,
            "rules_loaded": self.engine.rule_engine is not None,
            "tshark_available": bool(shutil.which(self.tshark_path or "tshark")),
            "notes": "Controller reachability is not probed because capability checks never perform network actions.",
        }

    def replay_windows(self, scenario: str) -> list[TelemetryWindow]:
        profile = self.engine.profile("PI-001")
        windows = []
        if scenario not in {"pi_syn", "pi_normal"}:
            raise ValueError("unknown replay scenario")
        for tick in range(8):
            point = _normal_point(profile, tick)
            if scenario == "pi_syn" and tick >= 3:
                point.syn_rate = 240.0 + tick * 12.0
                point.syn_ack_rate = 3.0
                point.ack_rate = 2.0
                point.incomplete_ratio = 0.94
                point.handshake_completion_ratio = 0.04
                point.orig_packets = 800.0
                point.resp_packets = 6.0
                point.iat = 0.001
            windows.append(
                TelemetryWindow(
                    device_id="PI-001",
                    source="recorded_replay",
                    points=[point],
                    timestamp=datetime.now(timezone.utc),
                    attack_job_id="pi-syn-demo",
                    sensor="aegis-replay",
                )
            )
        return windows
