"""Run repeated normal → attack → remediation demo scenarios without pytest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "backend" / "api"
sys.path.insert(0, str(API_ROOT))

from app.domain.telemetry import TelemetryWindow
from app.services.trust import AttackController, HybridTrustService, _normal_point


def run_once(iteration: int) -> dict[str, object]:
    model_path = ROOT / "model-store" / "aegis-hybrid-trust" / "v1"
    service = HybridTrustService(model_path, AttackController("", "", {"pi-syn-demo"}))
    normal_ok = all(96 <= float(device["trust"]) <= 99 for device in service.fleet())

    mock_attack = service.trigger_mock_attack("DEV-001")
    mock_attack_ok = mock_attack.state == "ATTACK" and mock_attack.trust < 30
    service.remediate("DEV-001")
    service.tick_mock_devices()
    service.tick_mock_devices()
    mock_recovered = service.state("DEV-001")
    mock_recovery_ok = mock_recovered["state"] == "HEALTHY" and float(mock_recovered["trust"]) >= 96

    pi_predictions = [service.ingest(window) for window in service.replay_windows("pi_syn")]
    pi_attack_ok = any(
        prediction.state == "ATTACK"
        and prediction.trust < 30
        and prediction.classification.get("mitre", {}).get("technique_id") == "T1498.001"
        for prediction in pi_predictions
    )
    pi_incidents = service.incidents.list(device_id="PI-001")
    exactly_one_incident = len(pi_incidents) == 1
    incident = pi_incidents[0] if pi_incidents else {}
    snapshot_ok = bool(incident.get("forensic_snapshot"))
    report = incident.get("report", {}) if incident else {}
    report_ok = bool(report.get("report_ready")) and Path(str(report.get("path", ""))).exists()
    remediation = service.remediate("PI-001")
    remediation_ok = bool(remediation["success"]) and remediation["phase"] == "VERIFYING_RECOVERY"
    profile = service.engine.profile("PI-001")
    recovery_progress = []
    for tick in range(3):
        service.ingest(TelemetryWindow(device_id="PI-001", source="pi", points=[_normal_point(profile, tick)]))
        recovery_progress.append(service.state("PI-001")["recovery_progress"]["clean_windows_observed"])
    pi_recovered = service.state("PI-001")
    pi_recovery_ok = pi_recovered["state"] == "HEALTHY" and float(pi_recovered["trust"]) >= 96
    final_incident = service.incidents.require(str(incident["incident_id"])) if incident else {}
    recovery_verified = (
        recovery_progress == [1, 2, 3]
        and final_incident.get("status") == "CLOSED"
        and final_incident.get("recovery_verification", {}).get("status") == "verified"
    )

    passed = all((
        normal_ok, mock_attack_ok, mock_recovery_ok, pi_attack_ok,
        exactly_one_incident, snapshot_ok, report_ok, remediation_ok,
        pi_recovery_ok, recovery_verified,
    ))
    return {
        "iteration": iteration,
        "passed": passed,
        "normal_ok": normal_ok,
        "mock_attack_ok": mock_attack_ok,
        "mock_recovery_ok": mock_recovery_ok,
        "pi_attack_ok": pi_attack_ok,
        "exactly_one_incident": exactly_one_incident,
        "forensic_snapshot_ok": snapshot_ok,
        "report_ready": report_ok,
        "remediation_ok": remediation_ok,
        "recovery_progress": recovery_progress,
        "pi_recovery_ok": pi_recovery_ok,
        "recovery_verified": recovery_verified,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loops", type=int, default=20)
    args = parser.parse_args()
    results = [run_once(iteration + 1) for iteration in range(args.loops)]
    passed = sum(bool(result["passed"]) for result in results)
    summary = {
        "loops": args.loops,
        "passed": passed,
        "failed": args.loops - passed,
        "demo_scenario_success_rate": round(100.0 * passed / max(args.loops, 1), 2),
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if passed == args.loops else 1)


if __name__ == "__main__":
    main()
