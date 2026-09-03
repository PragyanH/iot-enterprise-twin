from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.domain.telemetry import TelemetryPoint, TelemetryWindow
from app.intelligence.mitre import load_mitre_scenarios
from app.services.trust import AttackController, HybridTrustService, _normal_point


XAI_TIMESTAMP = datetime(2026, 1, 1, tzinfo=timezone.utc)


class IntelligenceService:
    """Read-only evidence APIs and deterministic scenarios using the production pipeline."""

    def __init__(self, model_path: Path, rules_path: Path, canonicalization_path: Path,
                 intelligence_path: Path, mitre_path: Path) -> None:
        self.model_path = model_path
        self.rules_path = rules_path
        self.canonicalization_path = canonicalization_path
        self.intelligence_path = intelligence_path
        self.mitre_catalog = load_mitre_scenarios(mitre_path)

    def _service(self) -> HybridTrustService:
        return HybridTrustService(
            self.model_path,
            AttackController("", "", {"pi-syn-demo"}),
            rules_path=self.rules_path,
            canonicalization_path=self.canonicalization_path,
            intelligence_path=self.intelligence_path,
        )

    def metrics(self) -> dict[str, object]:
        path = self.model_path / "metrics.json"
        if not path.exists():
            return {"available": False, "source": None, "metrics": None}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            "available": True,
            "model_version": "aegis-hybrid-trust/v1",
            "source": payload.get("source"),
            "metric_scope": payload.get("metric_scope"),
            "metrics": payload,
            "confusion_matrix": payload.get("confusion_matrix"),
            "per_class_metrics": payload.get("per_class_metrics"),
            "limitations": (
                "Confusion matrix and per-class metrics are unavailable in the frozen artifact."
                if payload.get("confusion_matrix") is None else None
            ),
        }

    def mitre_scenarios(self) -> dict[str, object]:
        return self.mitre_catalog

    @staticmethod
    def _unknown_points(service: HybridTrustService) -> list[TelemetryPoint]:
        profile = service.engine.profile("PI-001")
        points: list[TelemetryPoint] = []
        for tick in range(20):
            point = _normal_point(profile, tick)
            point.packet_size = 1150.0 + (tick % 3) * 90.0
            point.iat = 0.48 if tick % 2 else 0.005
            point.flow_symmetry = 0.08 + (tick % 4) * 0.01
            point.orig_packets = 260.0 + tick * 3.0
            point.resp_packets = 4.0 + tick % 2
            points.append(point)
        return points

    @staticmethod
    def _mitre_points(service: HybridTrustService, technique_id: str) -> list[TelemetryPoint]:
        profile = service.engine.profile("PI-001")
        points = [_normal_point(profile, tick) for tick in range(20)]
        for point in points:
            if technique_id == "T1498.001":
                point.syn_rate, point.incomplete_ratio = 260.0, 0.95
                point.handshake_completion_ratio, point.orig_packets, point.resp_packets = 0.03, 900.0, 5.0
            elif technique_id == "T1046":
                point.unique_destination_ports, point.rejected_connections = 70.0, 45.0
            elif technique_id == "T1110.001":
                point.ssh_attempts, point.ssh_failures = 35.0, 30.0
            else:
                point.packet_size, point.iat, point.flow_symmetry = 1200.0, 0.48, 0.08
                point.orig_packets, point.resp_packets = 280.0, 4.0
        return points

    @staticmethod
    def _explain(scenario: str, prediction: dict[str, object], provenance: dict[str, object]) -> dict[str, object]:
        calculation = prediction["trust_calculation"]
        return {
            "scenario": scenario,
            "provenance": provenance,
            "deterministic": True,
            "prediction": prediction,
            "calculation_steps": [
                {
                    "step": "detector_normalization",
                    "inputs": prediction["detectors"],
                    "result": calculation["profile_risk"],  # type: ignore[index]
                    "interpretation": "Each detector is normalized to risk in [0,1].",
                },
                {
                    "step": "known_unknown_decision",
                    "inputs": {
                        "known_attack_risk": prediction["known_attack_risk"],
                        "unknown_anomaly_score": prediction["unknown_anomaly_score"],
                        "detection_mode": prediction["detection_mode"],
                    },
                    "result": prediction["classification"],
                    "interpretation": "Known signatures and class support are evaluated separately from behavioral novelty.",
                },
                {
                    "step": "trust_composition",
                    "inputs": calculation["components"],  # type: ignore[index]
                    "formula": calculation["trust_formula"],  # type: ignore[index]
                    "result": calculation["final_trust"],  # type: ignore[index]
                    "interpretation": "The same state constraints used by live and replay scoring produce final trust.",
                },
            ],
        }

    def run_xai(self, scenario: str, technique_id: str | None = None) -> dict[str, object]:
        service = self._service()
        provenance: dict[str, object] = {
            "source_mode": "xai_simulation",
            "sensor": "aegis-xai-fixture",
            "timestamp": XAI_TIMESTAMP.isoformat(),
        }
        if scenario == "normal":
            profile = service.engine.profile("DEV-001")
            window = TelemetryWindow("DEV-001", "xai_simulation", [_normal_point(profile, tick) for tick in range(20)], timestamp=XAI_TIMESTAMP, sensor="aegis-xai-fixture")
        elif scenario == "known_attack":
            window = TelemetryWindow("PI-001", "xai_simulation", self._mitre_points(service, "T1498.001"), timestamp=XAI_TIMESTAMP, sensor="aegis-xai-fixture")
        elif scenario == "unknown_anomaly":
            window = TelemetryWindow("PI-001", "xai_simulation", self._unknown_points(service), timestamp=XAI_TIMESTAMP, sensor="aegis-xai-fixture")
        elif scenario == "mitre":
            catalog = {item["technique_id"]: item for item in self.mitre_catalog["scenarios"]}  # type: ignore[index]
            if not technique_id or technique_id not in catalog:
                raise ValueError("a valid technique_id from the MITRE catalog is required")
            provenance["mitre_scenario"] = catalog[technique_id]
            window = TelemetryWindow("PI-001", "xai_simulation", self._mitre_points(service, technique_id), timestamp=XAI_TIMESTAMP, sensor="aegis-xai-fixture")
        else:
            raise ValueError("scenario must be normal, known_attack, unknown_anomaly, or mitre")
        prediction = service.ingest(window).to_dict()
        return self._explain(scenario, prediction, provenance)
