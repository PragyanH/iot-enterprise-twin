from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_pi_sessions import build_report, load_rows, main


def _point(**overrides: float) -> dict[str, float]:
    base = {
        "packet_size": 60.0,
        "iat": 0.05,
        "flow_symmetry": 0.9,
        "syn_rate": 2.0,
        "syn_ack_rate": 2.0,
        "ack_rate": 2.0,
        "incomplete_ratio": 0.02,
        "handshake_completion_ratio": 0.98,
        "unique_sources": 1.0,
        "unique_destination_ports": 1.0,
        "rejected_connections": 0.0,
        "reset_connections": 0.0,
        "orig_packets": 4.0,
        "resp_packets": 4.0,
        "orig_bytes": 240.0,
        "resp_bytes": 240.0,
        "ssh_attempts": 0.0,
        "ssh_failures": 0.0,
        "capture_loss": 0.0,
    }
    base.update(overrides)
    return base


def _row(session_id: str, label: str, *, points: int = 20, timestamp: str = "2026-09-03T10:00:00Z", **point_overrides: float) -> dict[str, object]:
    return {
        "device_id": "PI-001",
        "source": "live_hardware",
        "sensor": "tshark_npcap",
        "session_id": session_id,
        "timestamp": timestamp,
        "label": label,
        "scenario": "test",
        "unavailable_features": ["payload_entropy", "connection_duration_mean"],
        "points": [_point(**point_overrides) for _ in range(points)],
    }


def _write(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    destination = tmp_path / "pi_sessions.jsonl"
    with destination.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    return destination


def test_good_dataset_passes(tmp_path: Path) -> None:
    rows = [
        _row("normal-1", "normal", timestamp="2026-09-03T10:00:00Z"),
        _row("normal-2", "normal", timestamp="2026-09-03T10:01:00Z"),
        _row("syn-1", "syn_flood", timestamp="2026-09-03T10:02:00Z", syn_rate=250.0, incomplete_ratio=0.95, handshake_completion_ratio=0.05, flow_symmetry=0.05, orig_packets=250.0),
        _row("syn-2", "syn_flood", timestamp="2026-09-03T10:03:00Z", syn_rate=250.0, incomplete_ratio=0.95, handshake_completion_ratio=0.05, flow_symmetry=0.05, orig_packets=250.0),
    ]
    path = _write(tmp_path, rows)
    issues: list = []
    parsed = load_rows(path, issues)
    report = build_report(parsed, issues)
    assert not any(issue.severity == "FAIL" for issue in issues)
    assert report["sessions"] == 4
    assert report["normal_count"] == 2
    assert report["syn_flood_count"] == 2
    assert main([str(path)]) == 0


def test_unknown_label_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, [_row("s1", "totally_made_up_attack")])
    issues: list = []
    load_rows(path, issues)
    assert any(issue.severity == "FAIL" and "unknown label" in issue.message for issue in issues)
    assert main([str(path)]) == 1


def test_missing_required_field_is_rejected(tmp_path: Path) -> None:
    row = _row("s1", "normal")
    del row["sensor"]
    path = _write(tmp_path, [row])
    issues: list = []
    load_rows(path, issues)
    assert any(issue.severity == "FAIL" and "missing required fields" in issue.message for issue in issues)


def test_too_few_points_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, [_row("s1", "normal", points=5)])
    issues: list = []
    load_rows(path, issues)
    assert any(issue.severity == "FAIL" and ">= 20 points" in issue.message for issue in issues)


def test_wrong_device_source_sensor_is_rejected(tmp_path: Path) -> None:
    bad_device = _row("s1", "normal")
    bad_device["device_id"] = "DEV-999"
    bad_source = _row("s2", "normal")
    bad_source["source"] = "mock"
    bad_sensor = _row("s3", "normal")
    bad_sensor["sensor"] = "aegis-simulator"
    path = _write(tmp_path, [bad_device, bad_source, bad_sensor])
    issues: list = []
    load_rows(path, issues)
    messages = [issue.message for issue in issues if issue.severity == "FAIL"]
    assert any("device_id" in message for message in messages)
    assert any("source" in message for message in messages)
    assert any("sensor" in message for message in messages)


def test_inconsistent_session_labels_are_rejected(tmp_path: Path) -> None:
    rows = [
        _row("shared-session", "normal", timestamp="2026-09-03T10:00:00Z"),
        _row("shared-session", "syn_flood", timestamp="2026-09-03T10:00:20Z"),
    ]
    path = _write(tmp_path, rows)
    issues: list = []
    parsed = load_rows(path, issues)
    build_report(parsed, issues)
    assert any(issue.severity == "FAIL" and "inconsistent labels" in issue.message for issue in issues)


def test_duplicate_rows_are_flagged(tmp_path: Path) -> None:
    row = _row("s1", "normal")
    path = _write(tmp_path, [row, dict(row)])
    issues: list = []
    load_rows(path, issues)
    assert any(issue.severity == "WARN" and "duplicate row" in issue.message for issue in issues)


def test_single_session_per_label_warns_about_leakage(tmp_path: Path) -> None:
    rows = [
        _row("only-normal", "normal"),
        _row("only-syn", "syn_flood", syn_rate=250.0),
    ]
    path = _write(tmp_path, rows)
    issues: list = []
    parsed = load_rows(path, issues)
    build_report(parsed, issues)
    assert any(issue.severity == "WARN" and "independent session" in issue.message for issue in issues)


def test_bad_physical_separation_warns_without_touching_thresholds(tmp_path: Path) -> None:
    rows = [
        _row("normal-1", "normal", timestamp="2026-09-03T10:00:00Z"),
        _row("normal-2", "normal", timestamp="2026-09-03T10:01:00Z"),
        # "attack" session that barely differs from normal - a bad physical capture.
        _row("syn-1", "syn_flood", timestamp="2026-09-03T10:02:00Z", syn_rate=2.5, incomplete_ratio=0.05, handshake_completion_ratio=0.95),
        _row("syn-2", "syn_flood", timestamp="2026-09-03T10:03:00Z", syn_rate=2.5, incomplete_ratio=0.05, handshake_completion_ratio=0.95),
    ]
    path = _write(tmp_path, rows)
    issues: list = []
    parsed = load_rows(path, issues)
    build_report(parsed, issues)
    assert any("barely changed" in issue.message for issue in issues)
    assert any("indistinguishable" in issue.message for issue in issues)


def test_out_of_range_ratio_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, [_row("s1", "normal", incomplete_ratio=1.5)])
    issues: list = []
    load_rows(path, issues)
    assert any(issue.severity == "FAIL" and "out of [0,1]" in issue.message for issue in issues)
