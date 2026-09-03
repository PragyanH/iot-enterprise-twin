from __future__ import annotations

import unittest

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError as exc:  # Allows standard-library core checks before dependencies are installed.
    raise unittest.SkipTest("FastAPI test dependencies are not installed") from exc

from app.main import app


def test_openapi_contains_hybrid_trust_routes() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/api/v1/telemetry/windows" in paths
    assert "/api/v1/devices/{device_id}/state" in paths
    assert "/api/v1/devices/{device_id}/remediate" in paths
    assert "/api/v1/events/trust" in paths


def test_fleet_and_mock_workflow() -> None:
    with TestClient(app) as client:
        fleet = client.get("/api/v1/fleet")
        assert fleet.status_code == 200
        assert len(fleet.json()) == 5

        attacked = client.post("/api/v1/devices/DEV-002/simulate-attack")
        assert attacked.status_code == 200
        assert attacked.json()["state"] == "ATTACK"
        assert attacked.json()["trust"] < 30

        remediated = client.post("/api/v1/devices/DEV-002/remediate")
        assert remediated.status_code == 200
        assert remediated.json()["controller"]["stopped"] is True


def test_pi_syn_telemetry_contract() -> None:
    payload = {
        "device_id": "PI-001",
        "source": "pi",
        "attack_job_id": "pi-syn-demo",
        "points": [
            {
                "syn_rate": 250,
                "syn_ack_rate": 2,
                "ack_rate": 1,
                "incomplete_ratio": 0.95,
                "handshake_completion_ratio": 0.03,
                "orig_packets": 900,
                "resp_packets": 5,
                "iat": 0.001
            }
        ]
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/telemetry/windows", json=payload)
    assert response.status_code == 200
    assert response.json()["state"] == "ATTACK"
    assert response.json()["attack_type"] == "syn_flood"
    assert response.json()["trust"] < 30
    assert response.json()["source_mode"] == "live_hardware"
    assert response.json()["rule"]["rule_id"] == "AEGIS-SYN-001"
    assert response.json()["raw_features"]["syn_rate"] == 250
    assert response.json()["canonical_features"]["syn_rate"] == 250
