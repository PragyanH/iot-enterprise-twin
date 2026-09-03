from __future__ import annotations

from pathlib import Path

import yaml


def load_mitre_scenarios(path: Path) -> dict[str, object]:
    if not path.exists():
        raise ValueError(f"MITRE scenario catalog does not exist: {path}")
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        scenarios = payload["scenarios"]
        required = {
            "technique_id", "technique_name", "tactic", "demo_mode", "description",
            "primary_indicators", "detection_mechanism", "recommended_response",
        }
        if len(scenarios) != 8:
            raise ValueError("MITRE catalog must contain exactly eight scenarios")
        if len({item["technique_id"] for item in scenarios}) != len(scenarios):
            raise ValueError("MITRE technique IDs must be unique")
        for item in scenarios:
            missing = required.difference(item)
            if missing:
                raise ValueError(f"MITRE scenario missing fields: {sorted(missing)}")
        return {"version": str(payload["version"]), "scenarios": scenarios}
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid MITRE scenario catalog {path}: {exc}") from exc
