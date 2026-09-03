from __future__ import annotations

import math
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.domain.telemetry import TelemetryPoint, TelemetryWindow
from app.main import app
from app.ml.hybrid_engine import PI_FEATURES, per_feature_jsd_evidence
from app.services.intelligence import IntelligenceService
from app.services.trust import AttackController, HybridTrustService, _normal_point


ROOT = Path(__file__).resolve().parents[4]
MODEL = ROOT / "model-store" / "aegis-hybrid-trust" / "v1"
RULES = ROOT / "rules" / "aegis_rules.yaml"
MITRE = ROOT / "rules" / "mitre_scenarios.yaml"


def make_service() -> HybridTrustService:
    return HybridTrustService(MODEL, AttackController("", "", {"pi-syn-demo"}))


def make_intelligence() -> IntelligenceService:
    return IntelligenceService(
        MODEL, RULES, MODEL / "canonicalization.json", MODEL / "intelligence.json", MITRE
    )


def test_pi_entropy_is_excluded_and_unavailable_duration_is_neutral() -> None:
    assert "payload_entropy" not in PI_FEATURES
    service = make_service()
    profile = service.engine.profile("PI-001")
    point = _normal_point(profile, 2)
    point.connection_duration_mean = 0.0
    prediction = service.ingest(
        TelemetryWindow(
            "PI-001", "live_hardware", [point],
            unavailable_features=("payload_entropy", "connection_duration_mean"),
        )
    ).to_dict()
    assert prediction["raw_features"]["connection_duration_mean"] == 0.0
    assert prediction["canonical_features"]["connection_duration_mean"] == 0.8
    duration = prediction["feature_deviations"]["connection_duration_mean"]
    assert duration["available"] is False
    assert duration["normalized_deviation"] == 0.0
    assert all(item["feature"] != "connection_duration_mean" for item in prediction["top_anomalies"])


def test_classifier_distribution_and_unknown_path_are_explicit() -> None:
    intelligence = make_intelligence()
    normal = intelligence.run_xai("normal")["prediction"]
    unknown = intelligence.run_xai("unknown_anomaly")["prediction"]
    probabilities = unknown["classifier"]["probabilities"]
    assert set(probabilities) == {"normal", "syn_flood", "port_scan", "ssh_bruteforce"}
    assert math.isclose(sum(probabilities.values()), 1.0, abs_tol=2e-6)
    assert unknown["classifier"]["backend"] in {"xgboost", "calibrated-fallback"}
    assert normal["detection_mode"] == "normal"
    assert unknown["state"] == "ATTACK"
    assert unknown["attack_type"] == "unknown_behavioral_anomaly"
    assert unknown["detection_mode"] == "unknown_anomaly"
    assert unknown["classification"]["known"] is False
    assert unknown["classification"]["mitre_status"] == "unmapped"
    assert unknown["unknown_anomaly_score"] >= 0.72


def test_known_attack_mitre_vae_and_trust_evidence() -> None:
    prediction = make_intelligence().run_xai("known_attack")["prediction"]
    assert prediction["detection_mode"] == "known_attack"
    assert prediction["classification"]["mitre"]["technique_id"] == "T1498.001"
    assert prediction["trust"] <= 25
    temporal = prediction["temporal"]
    assert temporal["raw_reconstruction_error"] >= 0
    assert temporal["threshold"] > 0
    assert 0 <= temporal["normalized_anomaly_risk"] <= 1
    assert len(temporal["attention_weights"]) == 20
    assert math.isclose(sum(temporal["attention_weights"]), 1.0, abs_tol=2e-5)
    calculation = prediction["trust_calculation"]
    expected = sum(item["risk"] * item["weight"] for item in calculation["components"])
    assert math.isclose(expected, calculation["profile_risk"], abs_tol=2e-6)
    assert calculation["final_trust"] == prediction["trust"]


def test_jsd_handles_constant_invalid_and_unavailable_features() -> None:
    service = make_service()
    profile = service.engine.profile("DEV-001")
    constant = [TelemetryPoint(**profile.baseline) for _ in range(20)]
    global_score, per_feature, availability = per_feature_jsd_evidence(
        constant, profile, {"iat"}
    )
    assert math.isfinite(global_score)
    assert all(math.isfinite(value) for value in per_feature.values())
    assert "iat" not in per_feature
    assert availability["iat"]["available"] is False
    invalid = [TelemetryPoint(**{**profile.baseline, "packet_size": float("nan")})]
    score, values, evidence = per_feature_jsd_evidence(invalid, profile)
    assert math.isfinite(score)
    assert "packet_size" not in values
    assert evidence["packet_size"]["reason"] == "invalid_or_empty_window"


def test_top_anomaly_order_is_deterministic_and_has_severity() -> None:
    first = make_intelligence().run_xai("unknown_anomaly")["prediction"]["top_anomalies"]
    second = make_intelligence().run_xai("unknown_anomaly")["prediction"]["top_anomalies"]
    assert first == second
    assert all(item["severity"] in {"low", "medium", "high", "critical"} for item in first)


def test_mitre_catalog_xai_determinism_and_api_contracts() -> None:
    intelligence = make_intelligence()
    scenarios = intelligence.mitre_scenarios()["scenarios"]
    assert len(scenarios) == 8
    for item in scenarios:
        first = intelligence.run_xai("mitre", item["technique_id"])
        second = intelligence.run_xai("mitre", item["technique_id"])
        assert first == second
        json.dumps(first, allow_nan=False)
        assert first["provenance"]["mitre_scenario"]["demo_mode"] == item["demo_mode"]
    for scenario in ("normal", "known_attack", "unknown_anomaly"):
        json.dumps(intelligence.run_xai(scenario), allow_nan=False)
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/devices/{device_id}/explainability" in paths
        assert "/api/v1/model/metrics" in paths
        assert "/api/v1/mitre/scenarios" in paths
        assert "/api/v1/xai/scenarios/{scenario}" in paths
        metrics = client.get("/api/v1/model/metrics").json()
        assert metrics["confusion_matrix"] is None
        assert metrics["per_class_metrics"] is None
        response = client.post("/api/v1/xai/scenarios/unknown_anomaly")
        assert response.status_code == 200
        assert response.json()["prediction"]["attack_type"] == "unknown_behavioral_anomaly"
