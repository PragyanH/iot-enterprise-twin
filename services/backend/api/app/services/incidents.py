from __future__ import annotations

import html
import json
import logging
import sqlite3
import threading
from copy import deepcopy
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


LOGGER = logging.getLogger("aegis.incidents")
ACTIVE_STATUSES = {"OPEN", "CONTAINMENT_REQUESTED", "CONTAINED", "RECOVERING"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentRepository:
    """Small SQLite JSON document store with deterministic per-database IDs."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with closing(self._connect()) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY, device_id TEXT NOT NULL, status TEXT NOT NULL,
                severity TEXT NOT NULL, source_mode TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, document TEXT NOT NULL)"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_incident_device ON incidents(device_id, status)")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5.0, isolation_level=None)

    def next_id(self, now: datetime) -> str:
        prefix = f"INC-{now:%Y%m%d}-"
        with self._lock, closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT incident_id FROM incidents WHERE incident_id LIKE ? ORDER BY incident_id DESC LIMIT 1",
                (f"{prefix}%",),
            ).fetchone()
        number = int(row[0].rsplit("-", 1)[1]) + 1 if row else 1
        return f"{prefix}{number:04d}"

    def save(self, incident: dict[str, object]) -> None:
        document = json.dumps(incident, separators=(",", ":"), allow_nan=False)
        with self._lock, closing(self._connect()) as connection:
            connection.execute(
                """INSERT INTO incidents VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(incident_id) DO UPDATE SET status=excluded.status,
                severity=excluded.severity, source_mode=excluded.source_mode,
                updated_at=excluded.updated_at, document=excluded.document""",
                (
                    incident["incident_id"], incident["device_id"], incident["status"],
                    incident["severity"], incident["source_mode"], incident["created_at"],
                    incident["updated_at"], document,
                ),
            )

    def get(self, incident_id: str) -> dict[str, object] | None:
        with self._lock, closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT document FROM incidents WHERE incident_id=?", (incident_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def active_for_device(self, device_id: str) -> dict[str, object] | None:
        placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
        with self._lock, closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT document FROM incidents WHERE device_id=? AND status IN ({placeholders}) ORDER BY created_at DESC LIMIT 1",
                (device_id, *sorted(ACTIVE_STATUSES)),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, filters: dict[str, str | None]) -> list[dict[str, object]]:
        clauses, values = [], []
        for field in ("device_id", "status", "severity", "source_mode"):
            if filters.get(field):
                clauses.append(f"{field}=?")
                values.append(filters[field])
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock, closing(self._connect()) as connection:
            rows = connection.execute(
                f"SELECT document FROM incidents{where} ORDER BY created_at DESC", values
            ).fetchall()
        return [json.loads(row[0]) for row in rows]


class IncidentService:
    def __init__(
        self,
        repository: IncidentRepository,
        reports_dir: Path,
        *,
        clock: Callable[[], datetime] = utc_now,
        event_sink: Callable[[str, dict[str, object]], None] | None = None,
    ) -> None:
        self.repository = repository
        self.reports_dir = reports_dir
        self.clock = clock
        self.event_sink = event_sink
        self._lock = threading.RLock()

    def _now(self) -> str:
        return self.clock().astimezone(timezone.utc).isoformat()

    def _emit(self, event: str, incident: dict[str, object], **metadata: object) -> None:
        fields = {"incident_id": incident["incident_id"], "device_id": incident["device_id"], **metadata}
        LOGGER.info(json.dumps({"event": event, **fields}, separators=(",", ":"), default=str))
        if self.event_sink:
            self.event_sink(event, fields)

    def _timeline(self, incident: dict[str, object], event_type: str, title: str,
                  description: str, metadata: dict[str, object] | None = None) -> None:
        timeline = incident["timeline"]
        assert isinstance(timeline, list)
        timeline.append({
            "event_id": f"EVT-{len(timeline) + 1:04d}",
            "incident_id": incident["incident_id"],
            "device_id": incident["device_id"],
            "timestamp": self._now(),
            "type": event_type,
            "title": title,
            "description": description,
            "metadata": metadata or {},
        })
        incident["updated_at"] = timeline[-1]["timestamp"]

    def observe(self, device_name: str, prediction: dict[str, object], pre_trust: float) -> dict[str, object] | None:
        if prediction["state"] != "ATTACK" or float(prediction["trust"]) >= 30:
            active = self.repository.active_for_device(str(prediction["device_id"]))
            if active:
                active["current_trust"] = prediction["trust"]
                active["updated_at"] = self._now()
                report = active["report"]
                assert isinstance(report, dict)
                report["needs_refresh"] = True
                self.repository.save(active)
            return active
        with self._lock:
            existing = self.repository.active_for_device(str(prediction["device_id"]))
            if existing:
                existing["current_trust"] = prediction["trust"]
                existing["minimum_trust"] = min(float(existing["minimum_trust"]), float(prediction["trust"]))
                existing["updated_at"] = self._now()
                report = existing["report"]
                assert isinstance(report, dict)
                report["needs_refresh"] = True
                self.repository.save(existing)
                return existing
            now = self.clock().astimezone(timezone.utc)
            incident_id = self.repository.next_id(now)
            snapshot = deepcopy(prediction)
            known = bool(prediction["classification"].get("known"))  # type: ignore[union-attr]
            attack_type = str(prediction["attack_type"])
            severity = "CRITICAL" if attack_type in {"syn_flood", "unknown_behavioral_anomaly"} else "HIGH"
            incident: dict[str, object] = {
                "incident_id": incident_id,
                "device_id": prediction["device_id"], "device_name": device_name,
                "status": "OPEN", "severity": severity,
                "source_mode": prediction["source_mode"], "sensor": prediction["sensor"],
                "detection_mode": prediction["detection_mode"], "attack_type": attack_type,
                "known": known, "mitre": prediction["classification"].get("mitre"),  # type: ignore[union-attr]
                "mitre_status": prediction["classification"].get("mitre_status"),  # type: ignore[union-attr]
                "created_at": now.isoformat(), "detected_at": prediction["timestamp"],
                "updated_at": now.isoformat(), "closed_at": None,
                "pre_incident_trust": round(float(pre_trust), 2),
                "minimum_trust": prediction["trust"], "current_trust": prediction["trust"],
                "recovery_trust": None,
                "forensic_snapshot": snapshot,
                "report": {"status": "pending", "report_ready": False, "report_id": None, "path": None, "generated_at": None, "error": None, "needs_refresh": False},
                "remediation": {"requested": False, "provider": None, "phase": "IDLE", "success": None, "outcome": None, "started_at": None, "completed_at": None, "error": None, "phases": []},
                "recovery_verification": {"status": "not_started", "clean_windows_required": 3, "clean_windows_observed": 0, "recovery_threshold": 95, "current_trust": prediction["trust"], "last_clean_timestamp": None},
                "timeline": [],
            }
            self._timeline(incident, "ATTACK_DECLARED", "Attack declared", f"{attack_type} reduced trust below 30.", {"trust": prediction["trust"]})
            if prediction["rule"].get("matched"):  # type: ignore[union-attr]
                self._timeline(incident, "RULE_MATCHED", "Detection rule matched", str(prediction["rule"].get("rule_id")), {"rule": prediction["rule"]})  # type: ignore[union-attr]
            self._timeline(incident, "KNOWN_ATTACK_CLASSIFIED" if known else "UNKNOWN_ANOMALY_DECLARED", "Classification established", attack_type, {"classification": prediction["classification"]})
            if incident["mitre"]:
                self._timeline(incident, "MITRE_MAPPED", "MITRE ATT&CK mapped", str(incident["mitre"]), {"mitre": incident["mitre"]})
            self._timeline(incident, "FORENSIC_SNAPSHOT_CAPTURED", "Forensic snapshot captured", "Detection-time evidence was frozen before remediation.")
            self.repository.save(incident)
            self._emit("incident_created", incident, attack_type=attack_type, severity=severity)
            self._emit("forensic_snapshot_captured", incident)
            return self.generate_report(incident_id)

    def generate_report(self, incident_id: str) -> dict[str, object]:
        with self._lock:
            incident = self.require(incident_id)
            report = incident["report"]
            assert isinstance(report, dict)
            existing_path = Path(str(report["path"])) if report.get("path") else None
            if report.get("status") == "ready" and not report.get("needs_refresh") and existing_path and existing_path.exists():
                return incident
            try:
                self.reports_dir.mkdir(parents=True, exist_ok=True)
                path = self.reports_dir / f"{incident_id}.html"
                snapshot = incident["forensic_snapshot"]
                sections = [
                    ("Incident Summary", {key: incident.get(key) for key in ("incident_id", "status", "severity", "created_at", "minimum_trust")}),
                    ("Protected Asset", {"device_id": incident["device_id"], "device_name": incident["device_name"], "source_mode": incident["source_mode"], "sensor": incident["sensor"]}),
                    ("Detection Summary", {"detection_mode": incident["detection_mode"], "attack_type": incident["attack_type"], "known": incident["known"]}),
                    ("Trust Timeline", incident["timeline"]),
                    ("Attack / Anomaly Classification", snapshot["classification"]),
                    ("MITRE ATT&CK Mapping", incident["mitre"] or "Unmapped / Investigation Required"),
                    ("Behavioral Twin Deviation", snapshot["feature_deviations"]),
                    ("Detector Evidence", snapshot["detectors"]),
                    ("Top Anomalous Features", snapshot["top_anomalies"]),
                    ("Mathematical Evidence", {"classifier": snapshot["classifier"], "temporal": snapshot["temporal"], "jsd": snapshot["jsd"], "jsd_by_feature": snapshot["jsd_by_feature"], "trust": snapshot["trust_calculation"]}),
                    ("Remediation", incident["remediation"]),
                    ("Recovery Verification", incident["recovery_verification"]),
                    ("Incident Timeline", incident["timeline"]),
                    ("Provenance / Validation Context", {"source_mode": incident["source_mode"], "sensor": incident["sensor"], "raw_features": snapshot["raw_features"], "canonical_features": snapshot["canonical_features"], "baseline_features": snapshot["baseline_features"]}),
                ]
                body = "".join(f"<h2>{index}. {html.escape(title)}</h2><pre>{html.escape(json.dumps(content, indent=2))}</pre>" for index, (title, content) in enumerate(sections, 1))
                content = f"<!doctype html><html><head><meta charset='utf-8'><title>{incident_id}</title><style>body{{font:14px Arial;max-width:1000px;margin:40px auto;color:#152238}}h1{{color:#0b5}}pre{{white-space:pre-wrap;background:#f3f6f8;padding:12px}}</style></head><body><h1>AEGIS-TWIN FORENSIC INCIDENT REPORT</h1>{body}</body></html>"
                path.write_text(content, encoding="utf-8")
                report.update({"status": "ready", "report_ready": True, "report_id": f"RPT-{incident_id}", "path": str(path.resolve()), "generated_at": self._now(), "error": None, "needs_refresh": False})
                self._timeline(incident, "REPORT_GENERATED", "Forensic report generated", "Idempotent HTML report is ready.", {"report_id": report["report_id"]})
                self._emit("forensic_report_generated", incident, report_id=report["report_id"])
            except (OSError, TypeError, ValueError, KeyError) as exc:
                report.update({"status": "failed", "report_ready": False, "error": str(exc)})
                self._emit("forensic_report_failed", incident, error=str(exc))
            self.repository.save(incident)
            return incident

    def remediation_event(self, incident_id: str, phase: str, title: str, description: str,
                          metadata: dict[str, object] | None = None, status: str | None = None) -> dict[str, object]:
        incident = self.require(incident_id)
        if status:
            incident["status"] = status
        remediation = incident["remediation"]
        assert isinstance(remediation, dict)
        remediation["phase"] = phase
        phases = remediation["phases"]
        assert isinstance(phases, list)
        phases.append({"phase": phase, "timestamp": self._now(), "description": description})
        report = incident["report"]
        assert isinstance(report, dict)
        report["needs_refresh"] = True
        self._timeline(incident, phase, title, description, metadata)
        self.repository.save(incident)
        return incident

    def recovery_progress(self, incident_id: str, observed: int, required: int, trust: float,
                          clean: bool, verified: bool) -> dict[str, object]:
        incident = self.require(incident_id)
        recovery = incident["recovery_verification"]
        assert isinstance(recovery, dict)
        recovery.update({
            "status": "verified" if verified else "pending",
            "clean_windows_required": required,
            "clean_windows_observed": observed,
            "current_trust": trust,
            "last_clean_timestamp": self._now() if clean else recovery.get("last_clean_timestamp"),
        })
        report = incident["report"]
        assert isinstance(report, dict)
        report["needs_refresh"] = True
        event_type = "RECOVERY_VERIFIED" if verified else f"CLEAN_WINDOW_{observed}" if clean else "RECOVERY_WINDOW_REJECTED"
        self._timeline(incident, event_type, "Recovery verified" if verified else "Recovery verification", f"Clean windows: {observed}/{required}.", {"clean": clean, "trust": trust})
        if verified:
            incident["status"] = "CLOSED"
            incident["recovery_trust"] = trust
            incident["closed_at"] = self._now()
            self._timeline(incident, "HEALTHY", "Device healthy", "Hybrid telemetry returned to healthy trust.", {"trust": trust})
            self._timeline(incident, "INCIDENT_CLOSED", "Incident closed", "Closure followed verified recovery.")
            self._emit("recovery_verified", incident, trust=trust)
            self._emit("incident_closed", incident)
        else:
            incident["status"] = "RECOVERING"
            self._emit("recovery_window", incident, observed=observed, required=required, clean=clean)
        self.repository.save(incident)
        return incident

    def require(self, incident_id: str) -> dict[str, object]:
        incident = self.repository.get(incident_id)
        if incident is None:
            raise KeyError(f"unknown incident: {incident_id}")
        return incident

    def list(self, **filters: str | None) -> list[dict[str, object]]:
        return self.repository.list(filters)
