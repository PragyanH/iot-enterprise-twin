from __future__ import annotations

import json
import socket
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import error

import pytest
from fastapi.testclient import TestClient

from app.domain.telemetry import TelemetryWindow
from app.main import app
from app.services.intelligence import IntelligenceService
from app.services.remediation import AttackControllerStopProvider
from app.services.trust import AttackController, HybridTrustService, _normal_point


ROOT = Path(__file__).resolve().parents[4]
MODEL = ROOT / "model-store" / "aegis-hybrid-trust" / "v1"


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class FakeResponse:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self.payload, self.status = payload, status

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def make_service(tmp_path: Path, controller: AttackController | None = None,
                 clock: FakeClock | None = None) -> HybridTrustService:
    return HybridTrustService(
        MODEL,
        controller or AttackController("", "", {"pi-syn-demo"}),
        incident_db_path=tmp_path / "incidents.db",
        reports_dir=tmp_path / "reports",
        clock=clock,
    )


def attack_pi(service: HybridTrustService) -> None:
    for window in service.replay_windows("pi_syn"):
        service.ingest(window)


def clean_pi(service: HybridTrustService, count: int) -> None:
    profile = service.engine.profile("PI-001")
    for tick in range(count):
        service.ingest(TelemetryWindow("PI-001", "recorded_replay", [_normal_point(profile, tick)]))


def test_incident_exact_once_snapshot_report_recovery_and_second_event(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    attack_pi(service)
    attack_pi(service)
    incidents = service.incidents.list(device_id="PI-001")
    assert len(incidents) == 1
    incident = incidents[0]
    assert str(incident["incident_id"]).startswith("INC-")
    assert incident["severity"] == "CRITICAL"
    assert incident["mitre"]["technique_id"] == "T1498.001"
    snapshot = incident["forensic_snapshot"]
    assert snapshot["raw_features"]["syn_rate"] >= 240
    assert snapshot["rule"]["rule_id"] == "AEGIS-SYN-001"
    assert incident["report"]["report_ready"] is True
    assert len(make_service(tmp_path).incidents.list(device_id="PI-001")) == 1
    report_path = Path(incident["report"]["path"])
    content = report_path.read_text(encoding="utf-8")
    assert "AEGIS-TWIN FORENSIC INCIDENT REPORT" in content
    assert "Detector Evidence" in content and "T1498.001" in content
    regenerated = service.incidents.generate_report(str(incident["incident_id"]))
    assert regenerated["report"]["path"] == str(report_path.resolve())
    before_events = len(regenerated["timeline"])
    assert len(service.incidents.generate_report(str(incident["incident_id"]))["timeline"]) == before_events

    result = service.remediate("PI-001")
    assert result["success"] is True and result["provider"] == "replay_stop"
    assert result["controller"]["stopped"] is False
    phase_count = len(service.incidents.require(str(incident["incident_id"]))["remediation"]["phases"])
    repeated = service.remediate("PI-001")
    assert repeated["success"] is True and repeated["idempotent"] is True
    assert len(service.incidents.require(str(incident["incident_id"]))["remediation"]["phases"]) == phase_count
    clean_pi(service, 1)
    assert service.state("PI-001")["recovery_progress"]["clean_windows_observed"] == 1
    clean_pi(service, 1)
    assert service.state("PI-001")["recovery_progress"]["clean_windows_observed"] == 2
    clean_pi(service, 1)
    closed = service.incidents.require(str(incident["incident_id"]))
    assert closed["status"] == "CLOSED"
    assert closed["recovery_verification"]["status"] == "verified"
    assert closed["recovery_trust"] >= 95
    ids = [event["event_id"] for event in closed["timeline"]]
    assert ids == [f"EVT-{index:04d}" for index in range(1, len(ids) + 1)]
    refreshed = service.incidents.generate_report(str(incident["incident_id"]))
    assert refreshed["report"]["path"] == str(report_path.resolve())
    assert "verified" in report_path.read_text(encoding="utf-8")
    refreshed_event_count = len(refreshed["timeline"])
    assert len(service.incidents.generate_report(str(incident["incident_id"]))["timeline"]) == refreshed_event_count
    operational_types = {event["type"] for event in service.events_since(0)}
    assert {"incident_created", "forensic_report_generated", "remediation_success", "recovery_verified", "incident_closed"}.issubset(operational_types)

    attack_pi(service)
    assert len(service.incidents.list(device_id="PI-001")) == 2


def test_unknown_incident_stays_unmapped_and_preserves_evidence(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    points = IntelligenceService._unknown_points(service)
    prediction = service.ingest(TelemetryWindow("PI-001", "xai_simulation", points))
    incident = service.incidents.list(device_id="PI-001")[0]
    assert prediction.attack_type == "unknown_behavioral_anomaly"
    assert incident["known"] is False
    assert incident["mitre"] is None
    assert incident["mitre_status"] == "unmapped"
    assert incident["forensic_snapshot"]["unknown_anomaly_score"] >= 0.72


def test_incident_minimum_trust_updates_without_replacing_snapshot(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    attack_pi(service)
    incident = service.incidents.list(device_id="PI-001")[0]
    original_raw = deepcopy(incident["forensic_snapshot"]["raw_features"])
    later = deepcopy(incident["forensic_snapshot"])
    later["trust"] = 4.0
    service.incidents.observe(str(incident["device_name"]), later, 5.0)
    updated = service.incidents.require(str(incident["incident_id"]))
    assert updated["minimum_trust"] == 4.0
    assert updated["forensic_snapshot"]["raw_features"] == original_raw


def test_report_failure_never_crashes_inference(tmp_path: Path) -> None:
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("blocked", encoding="utf-8")
    service = HybridTrustService(
        MODEL, AttackController("", "", {"pi-syn-demo"}),
        incident_db_path=tmp_path / "incidents.db", reports_dir=blocked,
    )
    attack_pi(service)
    incident = service.incidents.list()[0]
    assert incident["report"]["status"] == "failed"
    assert incident["state"] if "state" in incident else True


def test_attack_controller_outcomes_are_distinct() -> None:
    allowed = {"pi-syn-demo"}
    assert AttackControllerStopProvider("", "", allowed).execute("other").outcome == "not_allowlisted"
    assert AttackControllerStopProvider("", "", allowed).execute("pi-syn-demo").outcome == "controller_unavailable"
    already = AttackControllerStopProvider("http://controller", "token", allowed, opener=lambda *_args, **_kwargs: FakeResponse({"already_stopped": True}))
    assert already.execute("pi-syn-demo").outcome == "already_stopped"

    def unauthorized(*_args, **_kwargs):
        raise error.HTTPError("url", 401, "unauthorized", {}, None)

    def timeout(*_args, **_kwargs):
        raise socket.timeout("late")

    assert AttackControllerStopProvider("http://controller", "token", allowed, opener=unauthorized).execute("pi-syn-demo").outcome == "authentication_failure"
    assert AttackControllerStopProvider("http://controller", "token", allowed, opener=timeout).execute("pi-syn-demo").outcome == "timeout"


def test_failed_live_remediation_does_not_reset_temporal_context(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    for window in service.replay_windows("pi_syn"):
        window.source = "live_hardware"
        service.ingest(window)
    before = len(service._devices["PI-001"].points)
    result = service.remediate("PI-001")
    assert result["success"] is False
    assert result["phase"] == "FAILED"
    assert len(service._devices["PI-001"].points) == before
    incident = service.incidents.list(device_id="PI-001")[0]
    assert incident["remediation"]["success"] is False


def test_successful_controller_remediation_resets_context(tmp_path: Path) -> None:
    controller = AttackController(
        "http://controller", "token", {"pi-syn-demo"},
        opener=lambda *_args, **_kwargs: FakeResponse({"stopped": True}),
    )
    service = make_service(tmp_path, controller=controller)
    for window in service.replay_windows("pi_syn"):
        window.source = "live_hardware"
        service.ingest(window)
    assert len(service._devices["PI-001"].points) == 20
    result = service.remediate("PI-001")
    assert result["success"] is True
    assert result["provider"] == "attack_controller_stop"
    assert result["provider_result"]["outcome"] == "stopped"
    assert len(service._devices["PI-001"].points) == 0


def test_recovery_counter_resets_after_anomaly(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    attack_pi(service)
    service.remediate("PI-001")
    clean_pi(service, 1)
    assert service._devices["PI-001"].recovery_clean_windows == 1
    service.ingest(service.replay_windows("pi_syn")[-1])
    assert service._devices["PI-001"].recovery_clean_windows == 0


def test_live_staleness_uses_mockable_clock_and_fresh_data_resumes_inference(tmp_path: Path) -> None:
    clock = FakeClock()
    service = make_service(tmp_path, clock=clock)
    profile = service.engine.profile("PI-001")
    fresh = service.ingest(TelemetryWindow("PI-001", "live_hardware", [_normal_point(profile, 0)]))
    assert fresh.state != "STALE"
    clock.advance(4)
    service.refresh_staleness()
    assert service.state("PI-001")["state"] == "STALE"
    resumed = service.ingest(TelemetryWindow("PI-001", "live_hardware", [_normal_point(profile, 1)]))
    assert resumed.state != "STALE"
    assert service.state("PI-001")["stale_since"] is None


def test_replay_after_live_is_not_marked_stale(tmp_path: Path) -> None:
    clock = FakeClock()
    service = make_service(tmp_path, clock=clock)
    profile = service.engine.profile("PI-001")
    service.ingest(TelemetryWindow("PI-001", "live_hardware", [_normal_point(profile, 0)]))
    service.ingest(TelemetryWindow("PI-001", "recorded_replay", [_normal_point(profile, 1)]))
    clock.advance(10)
    service.refresh_staleness()
    assert service.state("PI-001")["source_mode"] == "recorded_replay"
    assert service.state("PI-001")["state"] != "STALE"


def test_incident_and_capability_api_contracts() -> None:
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/incidents", "/api/v1/incidents/{incident_id}",
            "/api/v1/incidents/{incident_id}/timeline",
            "/api/v1/incidents/{incident_id}/report", "/api/v1/system/capabilities",
        ):
            assert path in paths
        capabilities = client.get("/api/v1/system/capabilities")
        assert capabilities.status_code == 200
        providers = capabilities.json()["remediation"]["providers"]
        assert any(item["id"] == "network_isolation" and item["available"] is False for item in providers)
