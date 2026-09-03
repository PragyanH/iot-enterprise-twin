from __future__ import annotations

import math
import json
import sys
from pathlib import Path

import pytest

from app.domain.telemetry import TelemetryPoint, TelemetryWindow
from app.ml.hybrid_engine import per_feature_jsd
from app.rules.engine import load_rule_engine
from app.services.trust import AttackController, HybridTrustService
from app.telemetry.canonicalization import FeatureCanonicalizer


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.tshark_live import (
    CaptureStats,
    SessionRecorder,
    WindowAccumulator,
    build_parser,
    build_tshark_command,
    locate_tshark,
    parse_tshark_line,
    run_live,
)


MODEL_PATH = ROOT / "model-store" / "aegis-hybrid-trust" / "v1"
RULES_PATH = ROOT / "rules" / "aegis_rules.yaml"


def make_service() -> HybridTrustService:
    return HybridTrustService(
        MODEL_PATH,
        AttackController("", "", {"pi-syn-demo"}),
        rules_path=RULES_PATH,
        canonicalization_path=MODEL_PATH / "canonicalization.json",
    )


def test_canonicalization_preserves_raw_and_stabilizes_severe_syn() -> None:
    canonicalizer = FeatureCanonicalizer.from_path(MODEL_PATH / "canonicalization.json")
    result = canonicalizer.transform(
        TelemetryPoint(
            syn_rate=183.0,
            incomplete_ratio=0.88,
            handshake_completion_ratio=0.12,
        ),
        apply_attack_buckets=True,
    )
    assert result.raw.syn_rate == 183.0
    assert result.canonical.syn_rate == 250.0
    assert result.canonical.incomplete_ratio == 0.95
    assert result.applied["syn_rate"]["bucket"] == "severe_syn"


def test_canonicalization_does_not_modify_normal_and_rejects_nan() -> None:
    canonicalizer = FeatureCanonicalizer.default()
    normal = TelemetryPoint(syn_rate=3.0, incomplete_ratio=0.03, handshake_completion_ratio=0.96)
    result = canonicalizer.transform(normal, apply_attack_buckets=True)
    assert result.raw.to_dict() == result.canonical.to_dict()
    assert result.applied == {}
    with pytest.raises(ValueError, match="must be finite"):
        canonicalizer.transform(TelemetryPoint(iat=math.nan), apply_attack_buckets=True)


def test_yaml_rule_loads_and_exposes_condition_evidence() -> None:
    engine = load_rule_engine(RULES_PATH)
    raw = TelemetryPoint(syn_rate=183.0, incomplete_ratio=0.88, handshake_completion_ratio=0.12)
    canonical = TelemetryPoint(syn_rate=250.0, incomplete_ratio=0.95, handshake_completion_ratio=0.05)
    result = engine.evaluate(canonical, raw)[0]
    payload = result.to_dict()
    assert result.matched is True
    assert result.rule_id == "AEGIS-SYN-001"
    assert result.mitre["technique_id"] == "T1498.001"
    assert payload["conditions"][0]["raw_observed"] == 183.0  # type: ignore[index]
    assert len(payload["matched_conditions"]) == 3  # type: ignore[arg-type]


def test_yaml_rule_rejects_malformed_definition(tmp_path: Path) -> None:
    malformed = tmp_path / "bad.yaml"
    malformed.write_text(
        "ruleset_version: test\nrules:\n  - id: BAD\n    conditions:\n      - feature: nope\n        operator: '>='\n        threshold: 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown feature"):
        load_rule_engine(malformed)


def test_all_migrated_known_rules_are_versioned_yaml() -> None:
    engine = load_rule_engine(RULES_PATH)
    assert {rule.rule_id for rule in engine.rules} == {
        "AEGIS-SYN-001",
        "AEGIS-SCAN-001",
        "AEGIS-SSH-001",
    }


def test_jsd_is_finite_for_constant_features() -> None:
    service = make_service()
    profile = service.engine.profile("DEV-001")
    points = [TelemetryPoint(**profile.baseline) for _ in range(20)]
    jsd, by_feature = per_feature_jsd(points, profile)
    assert math.isfinite(jsd)
    assert all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in by_feature.values())


def test_tshark_parser_and_aggregation_use_correct_syn_semantics() -> None:
    rows = [
        "1710000000.000000\t60\t192.168.56.10\t192.168.56.20\t51000\t80\t1\t0\t0\t",
        "1710000000.010000\t60\t192.168.56.20\t192.168.56.10\t80\t51000\t1\t1\t0\t",
        "1710000000.020000\t60\t192.168.56.10\t192.168.56.20\t51000\t80\t0\t1\t0\t",
    ]
    accumulator = WindowAccumulator("192.168.56.20", 1.0)
    for row in rows:
        accumulator.add(parse_tshark_line(row))
    point = accumulator.point()
    assert point["syn_rate"] == 1.0
    assert point["syn_ack_rate"] == 1.0
    assert point["ack_rate"] == 1.0
    assert point["handshake_completion_ratio"] == 1.0
    assert point["incomplete_ratio"] == 0.0
    assert point["orig_packets"] == 2.0
    assert point["resp_packets"] == 1.0


def test_tshark_packet_silence_has_explicit_zero_packet_values() -> None:
    point = WindowAccumulator("192.168.56.20", 1.0).point()
    assert point["packet_size"] == 0.0
    assert point["iat"] == 1.0
    assert point["flow_symmetry"] == 1.0
    assert point["handshake_completion_ratio"] == 1.0


def test_tshark_command_is_interface_and_private_target_scoped() -> None:
    command = build_tshark_command(Path("C:/Program Files/Wireshark/tshark.exe"), "4", "192.168.56.20")
    assert command[command.index("-i") + 1] == "4"
    assert command[command.index("-f") + 1] == "host 192.168.56.20 and tcp"
    assert "separator=/t" in command


def test_session_recorder_writes_real_twenty_point_sequences(tmp_path: Path) -> None:
    destination = tmp_path / "pi_sessions.jsonl"
    recorder = SessionRecorder(destination, "normal", "test-baseline")
    for index in range(20):
        payload = {
            "device_id": "PI-001",
            "source": "live_hardware",
            "sensor": "tshark_npcap",
            "session_id": "session-1",
            "timestamp": f"2026-09-03T10:00:{index:02d}Z",
            "points": [{"syn_rate": float(index)}],
        }
        assert recorder.add(payload) is (index == 19)
    rows = destination.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    recorded = json.loads(rows[0])
    assert recorded["session_id"] == "session-1"
    assert recorded["label"] == "normal"
    assert len(recorded["points"]) == 20


def test_missing_tshark_has_clear_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("scripts.tshark_live.shutil.which", lambda _: None)
    monkeypatch.setattr(Path, "is_file", lambda _: False)
    with pytest.raises(FileNotFoundError, match="No live telemetry was generated"):
        locate_tshark("Z:/missing/tshark.exe")


def test_live_hardware_payload_is_sensor_neutral_and_explainable() -> None:
    service = make_service()
    prediction = service.ingest(
        TelemetryWindow(
            device_id="PI-001",
            source="live_hardware",
            sensor="tshark_npcap",
            attack_job_id="pi-syn-demo",
            points=[
                TelemetryPoint(
                    syn_rate=183.0,
                    syn_ack_rate=2.0,
                    ack_rate=1.0,
                    incomplete_ratio=0.88,
                    handshake_completion_ratio=0.12,
                    orig_packets=700.0,
                    resp_packets=5.0,
                    iat=0.001,
                )
            ],
        )
    )
    payload = prediction.to_dict()
    assert prediction.state == "ATTACK"
    assert prediction.trust < 30
    assert payload["source_mode"] == "live_hardware"
    assert payload["sensor"] == "tshark_npcap"
    assert payload["raw_features"]["syn_rate"] == 183.0  # type: ignore[index]
    assert payload["canonical_features"]["syn_rate"] == 250.0  # type: ignore[index]
    assert payload["rule"]["rule_id"] == "AEGIS-SYN-001"  # type: ignore[index]
    assert payload["rule"]["matched"] is True  # type: ignore[index]


def test_capture_stats_render_reports_every_summary_field() -> None:
    stats = CaptureStats(
        session_id="pi-20260903T100000Z-abcdef01",
        label="normal",
        scenario="finals-normal-01",
        interface="4",
        target_ip="192.168.56.20",
        started_at=0.0,
        raw_packets_seen=42,
        telemetry_intervals=3,
        windows_written=1,
        malformed_rows=2,
        post_successes=3,
        post_failures=0,
    )
    summary = stats.render(Path("data/finals-capture/pi_sessions.jsonl"), 60.0)
    assert "AEGIS-TWIN CAPTURE SUMMARY" in summary
    assert "Session ID: pi-20260903T100000Z-abcdef01" in summary
    assert "Label: normal" in summary
    assert "Scenario: finals-normal-01" in summary
    assert "Source mode: live_hardware" in summary
    assert "Sensor: tshark_npcap" in summary
    assert "Raw packets seen: 42" in summary
    assert "Telemetry intervals: 3" in summary
    assert "20-point windows written: 1" in summary
    assert "Malformed packet rows: 2" in summary
    assert "API POST successes: 3" in summary
    assert "API POST failures: 0" in summary
    assert "Output path: data" in summary


def test_capture_stats_render_without_recording_notes_not_recording() -> None:
    stats = CaptureStats(
        session_id="s",
        label="normal",
        scenario=None,
        interface="4",
        target_ip="192.168.56.20",
        started_at=0.0,
    )
    summary = stats.render(None, None)
    assert "Scenario: (none)" in summary
    assert "Output path: (not recording)" in summary
    assert "unbounded (Ctrl+C to stop)" in summary


class _FakeStream:
    def readline(self) -> str:
        return ""


class _FakeProcess:
    def __init__(self) -> None:
        self.stdout = _FakeStream()
        self.stderr = _FakeStream()
        self.returncode: int | None = None
        self._terminated = False

    def poll(self) -> int | None:
        return self.returncode if self._terminated else None

    def terminate(self) -> None:
        self._terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self._terminated = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int | None:
        return self.returncode


def test_duration_seconds_stops_cleanly_and_prints_capture_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("scripts.tshark_live.subprocess.Popen", lambda *args, **kwargs: _FakeProcess())
    monkeypatch.setattr(
        "scripts.tshark_live.post_window",
        lambda *args, **kwargs: {"trust": 98.0, "state": "HEALTHY"},
    )
    parser = build_parser()
    args = parser.parse_args(
        [
            "--interface",
            "4",
            "--target-ip",
            "192.168.56.20",
            "--sample-interval",
            "0.05",
            "--duration-seconds",
            "0.15",
            "--session-id",
            "test-session-duration",
        ]
    )
    exit_code = run_live(args, Path("tshark"))
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "AEGIS-TWIN CAPTURE SUMMARY" in output
    assert "Session ID: test-session-duration" in output
    assert "Requested duration: 0.15" in output


def test_replay_provenance_is_never_live_hardware() -> None:
    service = make_service()
    prediction = service.ingest(service.replay_windows("pi_syn")[0])
    assert prediction.source_mode == "recorded_replay"
    assert prediction.sensor == "aegis-replay"


def test_sse_fleet_payload_is_json_finite_and_contains_provenance() -> None:
    service = make_service()
    payload = {"version": service.version, "devices": service.fleet()}
    encoded = json.dumps(payload, allow_nan=False)
    decoded = json.loads(encoded)
    assert decoded["devices"]
    assert all("source_mode" in device and "sensor" in device for device in decoded["devices"])
    pi = next(device for device in decoded["devices"] if device["id"] == "PI-001")
    assert pi["source_mode"] == "mock"
    assert pi["sensor"] == "aegis-simulator"
