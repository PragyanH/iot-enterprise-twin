from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _sections(incident: dict[str, object]) -> list[tuple[str, object]]:
    snapshot = incident["forensic_snapshot"]
    source_mode = str(incident["source_mode"])
    provenance_label = {
        "live_hardware": "LIVE HARDWARE",
        "recorded_replay": "RECORDED REPLAY",
        "xai_simulation": "XAI SIMULATION",
        "mock": "MOCK FLEET",
    }.get(source_mode, source_mode.upper())
    return [
        ("Incident Summary", {key: incident.get(key) for key in ("incident_id", "status", "severity", "created_at", "detected_at", "pre_incident_trust", "minimum_trust", "current_trust", "recovery_trust")}),
        ("Protected Asset", {key: incident.get(key) for key in ("device_id", "device_name", "source_mode", "sensor")}),
        ("Attack / Unknown Anomaly", {"attack_type": incident["attack_type"], "detection_mode": incident["detection_mode"], "known": incident["known"]}),
        ("MITRE ATT&CK", incident.get("mitre") or "Unmapped / Investigation Required"),
        ("Behavioral Twin Evidence - Raw", snapshot["raw_features"]),
        ("Behavioral Twin Evidence - Canonical", snapshot["canonical_features"]),
        ("Behavioral Twin Evidence - Baseline", snapshot["baseline_features"]),
        ("Behavioral Twin Deviations", snapshot["feature_deviations"]),
        ("Rule Evidence", snapshot["rule"]),
        ("XGBoost Probabilities", snapshot["classifier"]),
        ("LSTM-VAE Evidence", snapshot["temporal"]),
        ("Jensen-Shannon Divergence", {"global": snapshot["jsd"], "per_feature": snapshot["jsd_by_feature"]}),
        ("Unknown-Anomaly Evidence", {"score": snapshot["unknown_anomaly_score"], "detection_mode": snapshot["detection_mode"]}),
        ("Trust Composition", snapshot["trust_calculation"]),
        ("Incident Timeline", incident["timeline"]),
        ("Assignment", {key: incident.get(key) for key in ("assignment_status", "assigned_to_user_id", "assigned_to_name", "assigned_to_email", "assigned_to_role", "assigned_by_user_id", "assigned_at", "assignment_history")}),
        ("Investigation Notes", incident.get("notes", [])),
        ("Remediation", incident["remediation"]),
        ("Recovery Verification", incident["recovery_verification"]),
        ("Provenance", {"source_mode": source_mode, "source_label": provenance_label, "sensor": incident["sensor"]}),
    ]


def render_incident_pdf(incident: dict[str, object], destination: Path) -> None:
    """Write one standards-compliant, deterministic and Windows-native PDF."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".pdf.tmp")
    document = canvas.Canvas(
        str(temporary), pagesize=A4, pageCompression=0, invariant=1,
        title=f"Aegis-Twin Forensic Incident {incident['incident_id']}",
        author="AEGIS-TWIN",
    )
    width, height = A4
    margin, line_height = 42, 10
    y = height - margin

    def new_page() -> None:
        nonlocal y
        document.showPage()
        document.setFont("Helvetica", 7)
        y = height - margin

    document.setFont("Helvetica-Bold", 16)
    document.drawString(margin, y, "AEGIS-TWIN")
    y -= 20
    document.setFont("Helvetica-Bold", 13)
    document.drawString(margin, y, "FORENSIC INCIDENT REPORT")
    y -= 24
    for number, (title, payload) in enumerate(_sections(incident), 1):
        if y < 70:
            new_page()
        document.setFont("Helvetica-Bold", 10)
        document.drawString(margin, y, f"{number}. {title}")
        y -= 14
        document.setFont("Courier", 6.7)
        serialized = payload if isinstance(payload, str) else json.dumps(payload, indent=2, sort_keys=True, default=str)
        for source_line in str(serialized).splitlines() or [""]:
            for line in textwrap.wrap(source_line, width=112, replace_whitespace=False, drop_whitespace=False) or [""]:
                if y < 45:
                    new_page()
                    document.setFont("Courier", 6.7)
                document.drawString(margin, y, line[:112])
                y -= line_height
        y -= 7
    document.save()
    os.replace(temporary, destination)
