"""Validate a captured PI-001 physical session dataset before Step 4B training.

This is a capture-quality gate, not a model evaluation. It rejects malformed
or mislabeled physical datasets and reports whether the controlled SYN
attack actually produced the expected physical telemetry signature. It never
modifies model thresholds, baselines, or artifacts.

Pure standard library so it can run without the backend virtualenv.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "finals-capture" / "pi_sessions.jsonl"
DEFAULT_REPORT = ROOT / "data" / "finals-capture" / "validation_report.json"
DEFAULT_MANIFEST = ROOT / "data" / "finals-capture" / "capture_manifest.json"

KNOWN_LABELS = {"normal", "syn_flood", "port_scan", "ssh_bruteforce"}
REQUIRED_ROW_FIELDS = ("device_id", "source", "sensor", "session_id", "timestamp", "points", "label")
RATIO_FEATURES = {"incomplete_ratio", "handshake_completion_ratio", "flow_symmetry", "payload_entropy", "capture_loss"}
EXPECTED_DEVICE = "PI-001"
EXPECTED_SOURCE = "live_hardware"
EXPECTED_SENSOR = "tshark_npcap"
MIN_POINTS = 20

SANITY_FEATURES = (
    "packet_size",
    "iat",
    "flow_symmetry",
    "syn_rate",
    "syn_ack_rate",
    "ack_rate",
    "incomplete_ratio",
    "handshake_completion_ratio",
    "unique_sources",
    "unique_destination_ports",
    "orig_packets",
    "resp_packets",
    "reset_connections",
    "rejected_connections",
    "connection_duration_mean",
    "ssh_attempts",
    "ssh_failures",
)
COMPARISON_FEATURES = (
    "syn_rate",
    "incomplete_ratio",
    "handshake_completion_ratio",
    "iat",
    "flow_symmetry",
    "orig_packets",
    "resp_packets",
)
ALWAYS_UNAVAILABLE = {"payload_entropy", "connection_duration_mean"}


@dataclass(slots=True)
class Issue:
    severity: str  # FAIL | WARN
    message: str
    session_id: str | None = None
    line_no: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"severity": self.severity, "message": self.message, "session_id": self.session_id, "line_no": self.line_no}


@dataclass(slots=True)
class Row:
    line_no: int
    device_id: str
    source: str
    sensor: str
    session_id: str
    label: str
    scenario: str | None
    timestamp: str
    points: list[dict[str, float]]
    unavailable_features: set[str]
    raw_text: str


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def load_rows(path: Path, issues: list[Issue]) -> list[Row]:
    rows: list[Row] = []
    if not path.is_file():
        issues.append(Issue("FAIL", f"input file does not exist: {path}"))
        return rows
    text = path.read_text(encoding="utf-8")
    seen_exact_lines: Counter[str] = Counter()
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            issues.append(Issue("FAIL", f"invalid JSON: {exc}", line_no=line_no))
            continue
        if not isinstance(payload, dict):
            issues.append(Issue("FAIL", "row is not a JSON object", line_no=line_no))
            continue

        missing = [field_name for field_name in REQUIRED_ROW_FIELDS if field_name not in payload]
        if missing:
            issues.append(Issue("FAIL", f"missing required fields: {missing}", line_no=line_no))
            continue

        canonical = json.dumps(payload, sort_keys=True)
        seen_exact_lines[canonical] += 1
        if seen_exact_lines[canonical] > 1:
            issues.append(Issue("WARN", "exact duplicate row detected", session_id=str(payload.get("session_id")), line_no=line_no))

        session_id = str(payload.get("session_id") or "")
        if not session_id:
            issues.append(Issue("FAIL", "session_id is empty", line_no=line_no))

        label = str(payload.get("label", ""))
        if label not in KNOWN_LABELS:
            issues.append(Issue("FAIL", f"unknown label {label!r} (expected one of {sorted(KNOWN_LABELS)})", session_id=session_id, line_no=line_no))

        device_id = str(payload.get("device_id", ""))
        if device_id != EXPECTED_DEVICE:
            issues.append(Issue("FAIL", f"device_id {device_id!r} != {EXPECTED_DEVICE!r}", session_id=session_id, line_no=line_no))

        source = str(payload.get("source", ""))
        if source != EXPECTED_SOURCE:
            issues.append(Issue("FAIL", f"source {source!r} != {EXPECTED_SOURCE!r} (this validator is for the physical dataset)", session_id=session_id, line_no=line_no))

        sensor = str(payload.get("sensor", ""))
        if sensor != EXPECTED_SENSOR:
            issues.append(Issue("FAIL", f"sensor {sensor!r} != {EXPECTED_SENSOR!r}", session_id=session_id, line_no=line_no))

        timestamp = str(payload.get("timestamp", ""))
        if _parse_timestamp(timestamp) is None:
            issues.append(Issue("FAIL", f"timestamp does not parse as ISO 8601: {timestamp!r}", session_id=session_id, line_no=line_no))

        points = payload.get("points")
        if not isinstance(points, list) or len(points) < MIN_POINTS:
            actual = len(points) if isinstance(points, list) else "not a list"
            issues.append(Issue("FAIL", f"expected >= {MIN_POINTS} points, found {actual}", session_id=session_id, line_no=line_no))
            points = points if isinstance(points, list) else []

        clean_points: list[dict[str, float]] = []
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                issues.append(Issue("FAIL", f"point {point_index} is not an object", session_id=session_id, line_no=line_no))
                continue
            clean_point: dict[str, float] = {}
            for feature, value in point.items():
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    issues.append(Issue("FAIL", f"point {point_index} feature {feature!r} is not numeric", session_id=session_id, line_no=line_no))
                    continue
                numeric = float(value)
                if not math.isfinite(numeric):
                    issues.append(Issue("FAIL", f"point {point_index} feature {feature!r} is not finite", session_id=session_id, line_no=line_no))
                    continue
                if numeric < 0:
                    issues.append(Issue("FAIL", f"point {point_index} feature {feature!r} is negative ({numeric})", session_id=session_id, line_no=line_no))
                    continue
                if feature in RATIO_FEATURES and not (0.0 <= numeric <= 1.0):
                    issues.append(Issue("FAIL", f"point {point_index} feature {feature!r} out of [0,1]: {numeric}", session_id=session_id, line_no=line_no))
                    continue
                clean_point[feature] = numeric
            clean_points.append(clean_point)

        unavailable = set(ALWAYS_UNAVAILABLE)
        declared_unavailable = payload.get("unavailable_features")
        if isinstance(declared_unavailable, list):
            unavailable.update(str(item) for item in declared_unavailable)

        rows.append(
            Row(
                line_no=line_no,
                device_id=device_id,
                source=source,
                sensor=sensor,
                session_id=session_id,
                label=label,
                scenario=payload.get("scenario"),
                timestamp=timestamp,
                points=clean_points,
                unavailable_features=unavailable,
                raw_text=canonical,
            )
        )
    return rows


def check_session_consistency(rows: list[Row], issues: list[Issue]) -> None:
    labels_by_session: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.session_id:
            labels_by_session[row.session_id].add(row.label)
    for session_id, labels in labels_by_session.items():
        if len(labels) > 1:
            issues.append(Issue("FAIL", f"session {session_id!r} has inconsistent labels: {sorted(labels)}", session_id=session_id))


def check_leakage_readiness(rows: list[Row], issues: list[Issue]) -> dict[str, int]:
    sessions_by_label: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.label and row.session_id:
            sessions_by_label[row.label].add(row.session_id)
    independent_counts = {label: len(sessions) for label, sessions in sessions_by_label.items()}
    for label, count in independent_counts.items():
        if count < 2:
            issues.append(
                Issue(
                    "WARN",
                    f"label {label!r} has only {count} independent session(s); a session-level held-out split needs at least 2, ideally 5-8",
                )
            )
    return independent_counts


def _feature_values(rows: list[Row], feature: str, label: str | None = None) -> list[float]:
    values: list[float] = []
    for row in rows:
        if label is not None and row.label != label:
            continue
        for point in row.points:
            if feature in point:
                values.append(point[feature])
    return values


def build_feature_report(rows: list[Row], features: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    report: dict[str, dict[str, Any]] = {}
    declared_unavailable = set()
    for row in rows:
        declared_unavailable |= row.unavailable_features
    for feature in features:
        values = _feature_values(rows, feature)
        entry: dict[str, Any] = {"available": bool(values) and feature not in declared_unavailable}
        if feature in declared_unavailable:
            entry["note"] = "adapter reports this field as unavailable; values are placeholders, not evidence"
        if values:
            entry["min"] = min(values)
            entry["max"] = max(values)
            entry["mean"] = statistics.fmean(values)
            entry["stddev"] = statistics.pstdev(values) if len(values) > 1 else 0.0
            entry["count"] = len(values)
        else:
            entry["count"] = 0
        report[feature] = entry
    return report


def build_normal_vs_attack_table(rows: list[Row], issues: list[Issue]) -> dict[str, dict[str, float | None]]:
    table: dict[str, dict[str, float | None]] = {}
    for feature in COMPARISON_FEATURES:
        normal_values = _feature_values(rows, feature, label="normal")
        syn_values = _feature_values(rows, feature, label="syn_flood")
        table[feature] = {
            "normal_mean": statistics.fmean(normal_values) if normal_values else None,
            "syn_flood_mean": statistics.fmean(syn_values) if syn_values else None,
        }

    def _mean(feature: str, label: str) -> float | None:
        values = table.get(feature, {}).get(f"{label}_mean")
        return values

    syn_rate_normal = _mean("syn_rate", "normal")
    syn_rate_syn = _mean("syn_rate", "syn_flood")
    incomplete_normal = _mean("incomplete_ratio", "normal")
    incomplete_syn = _mean("incomplete_ratio", "syn_flood")
    handshake_normal = _mean("handshake_completion_ratio", "normal")
    handshake_syn = _mean("handshake_completion_ratio", "syn_flood")

    if None not in (syn_rate_normal, syn_rate_syn):
        if syn_rate_syn <= syn_rate_normal * 1.5 + 1e-9:
            issues.append(Issue("WARN", f"SYN rate barely changed under attack (normal mean {syn_rate_normal:.2f}, syn_flood mean {syn_rate_syn:.2f})"))
    if None not in (incomplete_normal, incomplete_syn):
        if (incomplete_syn - incomplete_normal) < 0.2:
            issues.append(Issue("WARN", f"incomplete_ratio did not rise materially under attack (normal {incomplete_normal:.2f} -> syn_flood {incomplete_syn:.2f})"))
    if None not in (handshake_normal, handshake_syn):
        if (handshake_normal - handshake_syn) < 0.2:
            issues.append(Issue("WARN", f"handshake_completion_ratio did not collapse under attack (normal {handshake_normal:.2f} -> syn_flood {handshake_syn:.2f})"))
    if None not in (syn_rate_normal, syn_rate_syn, incomplete_normal, incomplete_syn, handshake_normal, handshake_syn):
        if syn_rate_syn <= syn_rate_normal * 1.5 and (incomplete_syn - incomplete_normal) < 0.2 and (handshake_normal - handshake_syn) < 0.2:
            issues.append(Issue("WARN", "normal and SYN-flood windows appear indistinguishable on the core SYN-flood indicators; diagnose physical capture/topology before Step 4B"))

    normal_syn_rate_values = _feature_values(rows, "syn_rate", label="normal")
    if len(normal_syn_rate_values) > 1:
        mean = statistics.fmean(normal_syn_rate_values)
        stdev = statistics.pstdev(normal_syn_rate_values)
        if mean > 1e-9 and (stdev / mean) > 1.0:
            issues.append(Issue("WARN", f"normal background syn_rate is highly unstable (mean {mean:.2f}, stddev {stdev:.2f})"))

    return table


def build_report(rows: list[Row], issues: list[Issue]) -> dict[str, Any]:
    check_session_consistency(rows, issues)
    leakage = check_leakage_readiness(rows, issues)
    sessions = {row.session_id for row in rows if row.session_id}
    windows_per_session = Counter(row.session_id for row in rows if row.session_id)
    labels = Counter(row.label for row in rows if row.label)
    timestamps = [parsed for row in rows if (parsed := _parse_timestamp(row.timestamp)) is not None]
    span = None
    if timestamps:
        span = {"first": min(timestamps).isoformat(), "last": max(timestamps).isoformat()}

    return {
        "sessions": len(sessions),
        "rows": len(rows),
        "windows_per_session": dict(windows_per_session),
        "labels": dict(labels),
        "normal_count": labels.get("normal", 0),
        "syn_flood_count": labels.get("syn_flood", 0),
        "timestamp_span": span,
        "independent_sessions_per_label": leakage,
        "feature_sanity": build_feature_report(rows, SANITY_FEATURES),
        "normal_vs_syn_flood": build_normal_vs_attack_table(rows, issues),
    }


def write_manifest(rows: list[Row], args: argparse.Namespace, destination: Path) -> None:
    sessions_meta = []
    for row in sorted({r.session_id for r in rows if r.session_id}):
        session_rows = [r for r in rows if r.session_id == row]
        sessions_meta.append(
            {
                "session_id": row,
                "label": session_rows[0].label if session_rows else None,
                "scenario": session_rows[0].scenario if session_rows else None,
                "windows": len(session_rows),
            }
        )
    manifest = {
        "capture_date": args.capture_date,
        "host": args.host,
        "device_id": EXPECTED_DEVICE,
        "pi_ip": args.pi_ip,
        "tshark_interface": args.interface,
        "sensor": EXPECTED_SENSOR,
        "sample_interval_seconds": 1.0,
        "sequence_length": MIN_POINTS,
        "sessions": sessions_meta,
        "vm_attack_rate": args.vm_attack_rate,
        "attack_port": args.attack_port,
        "attack_job_id": args.attack_job_id,
        "notes": args.notes,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def render_human(report: dict[str, Any], issues: list[Issue]) -> str:
    lines = ["AEGIS-TWIN DATASET VALIDATION", ""]
    lines.append(f"Sessions: {report['sessions']}")
    lines.append(f"Rows (windows): {report['rows']}")
    lines.append(f"Labels: {report['labels']}")
    lines.append(f"Normal windows: {report['normal_count']}  SYN-flood windows: {report['syn_flood_count']}")
    lines.append(f"Timestamp span: {report['timestamp_span']}")
    lines.append(f"Independent sessions per label (for held-out split): {report['independent_sessions_per_label']}")
    lines.append("")
    lines.append("FEATURE SANITY")
    for feature, stats in report["feature_sanity"].items():
        if not stats.get("available"):
            lines.append(f"  {feature}: UNAVAILABLE ({stats.get('note', 'no data')})")
            continue
        if stats.get("count"):
            lines.append(
                f"  {feature}: min={stats['min']:.4f} max={stats['max']:.4f} mean={stats['mean']:.4f} stddev={stats['stddev']:.4f} (n={stats['count']})"
            )
        else:
            lines.append(f"  {feature}: no observations")
    lines.append("")
    lines.append("NORMAL vs SYN FLOOD")
    lines.append(f"  {'FEATURE':<28}{'NORMAL':>14}{'SYN':>14}")
    for feature, values in report["normal_vs_syn_flood"].items():
        normal = values["normal_mean"]
        syn = values["syn_flood_mean"]
        normal_text = f"{normal:.4f}" if normal is not None else "n/a"
        syn_text = f"{syn:.4f}" if syn is not None else "n/a"
        lines.append(f"  {feature:<28}{normal_text:>14}{syn_text:>14}")
    lines.append("")
    fails = [issue for issue in issues if issue.severity == "FAIL"]
    warns = [issue for issue in issues if issue.severity == "WARN"]
    if fails:
        lines.append(f"FAILURES ({len(fails)}):")
        for issue in fails[:50]:
            location = f" [line {issue.line_no}]" if issue.line_no else ""
            session = f" (session {issue.session_id})" if issue.session_id else ""
            lines.append(f"  [FAIL]{location}{session} {issue.message}")
        if len(fails) > 50:
            lines.append(f"  ... {len(fails) - 50} more failures omitted")
    if warns:
        lines.append(f"WARNINGS ({len(warns)}):")
        for issue in warns[:50]:
            session = f" (session {issue.session_id})" if issue.session_id else ""
            lines.append(f"  [WARN]{session} {issue.message}")
    lines.append("")
    lines.append("DATASET STATUS: " + ("REJECTED" if fails else "ACCEPTED FOR STEP 4B REVIEW"))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a captured PI-001 physical session dataset")
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json", action="store_true", help="Write validation_report.json alongside human output")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--capture-date", default="")
    parser.add_argument("--host", default="")
    parser.add_argument("--pi-ip", default="")
    parser.add_argument("--interface", default="")
    parser.add_argument("--vm-attack-rate", default="")
    parser.add_argument("--attack-port", default="")
    parser.add_argument("--attack-job-id", default="pi-syn-demo")
    parser.add_argument("--notes", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    issues: list[Issue] = []
    rows = load_rows(args.input, issues)
    report = build_report(rows, issues)
    print(render_human(report, issues))
    if args.json:
        payload = {"report": report, "issues": [issue.to_dict() for issue in issues]}
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote {args.report_path}")
    if args.write_manifest:
        write_manifest(rows, args, args.manifest_path)
        print(f"Wrote {args.manifest_path}")
    return 1 if any(issue.severity == "FAIL" for issue in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
