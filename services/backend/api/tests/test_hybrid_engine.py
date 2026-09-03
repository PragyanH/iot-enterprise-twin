from __future__ import annotations

import unittest
from pathlib import Path

from app.domain.telemetry import TelemetryPoint, TelemetryWindow
from app.services.trust import AttackController, HybridTrustService, _normal_point


MODEL_PATH = Path(__file__).resolve().parents[4] / "model-store" / "aegis-hybrid-trust" / "v1"


def make_service() -> HybridTrustService:
    return HybridTrustService(MODEL_PATH, AttackController("", "", {"pi-syn-demo"}))


class HybridTrustEngineTests(unittest.TestCase):
    def test_all_devices_boot_healthy_above_95(self) -> None:
        service = make_service()
        for device in service.fleet():
            self.assertEqual(device["state"], "HEALTHY")
            self.assertGreaterEqual(device["trust"], 96)
            self.assertLessEqual(device["trust"], 99)

    def test_mock_attack_and_remediation(self) -> None:
        service = make_service()
        attacked = service.trigger_mock_attack("DEV-001")
        self.assertEqual(attacked.state, "ATTACK")
        self.assertLess(attacked.trust, 30)
        self.assertEqual(len(attacked.attention_weights), 20)
        self.assertAlmostEqual(sum(attacked.attention_weights), 1.0, places=4)
        remediation = service.remediate("DEV-001")
        self.assertTrue(remediation["controller"]["stopped"])
        service.tick_mock_devices()
        service.tick_mock_devices()
        recovered = service.state("DEV-001")
        self.assertEqual(recovered["state"], "HEALTHY")
        self.assertGreaterEqual(recovered["trust"], 96)

    def test_pi_syn_replay_drops_immediately(self) -> None:
        service = make_service()
        predictions = [service.ingest(window) for window in service.replay_windows("pi_syn")]
        attacked = [prediction for prediction in predictions if prediction.state == "ATTACK"]
        self.assertTrue(attacked)
        self.assertLess(attacked[0].trust, 30)
        self.assertEqual(attacked[0].attack_type, "syn_flood")
        self.assertGreaterEqual(attacked[0].rule_risk, 0.8)

    def test_pi_recovery_requires_clean_telemetry(self) -> None:
        service = make_service()
        for window in service.replay_windows("pi_syn"):
            service.ingest(window)
        remediation = service.remediate("PI-001")
        self.assertFalse(remediation["controller"]["stopped"])
        profile = service.engine.profile("PI-001")
        for tick in range(3):
            service.ingest(
                TelemetryWindow(
                    device_id="PI-001",
                    source="pi",
                    points=[_normal_point(profile, tick)],
                )
            )
        recovered = service.state("PI-001")
        self.assertEqual(recovered["state"], "HEALTHY")
        self.assertGreaterEqual(recovered["trust"], 96)

    def test_stale_telemetry_freezes_trust(self) -> None:
        service = make_service()
        before = service.state("PI-001")["trust"]
        stale = service.ingest(
            TelemetryWindow(
                device_id="PI-001",
                source="pi",
                points=[TelemetryPoint(capture_loss=0.4)],
            )
        )
        self.assertEqual(stale.state, "STALE")
        self.assertEqual(stale.trust, before)


if __name__ == "__main__":
    unittest.main()
