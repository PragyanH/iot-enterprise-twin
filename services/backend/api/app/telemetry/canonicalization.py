from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from app.domain.telemetry import FEATURE_NAMES, TelemetryPoint


RATIO_FEATURES = {
    "payload_entropy",
    "flow_symmetry",
    "incomplete_ratio",
    "handshake_completion_ratio",
    "capture_loss",
}


@dataclass(frozen=True, slots=True)
class CanonicalizationResult:
    raw: TelemetryPoint
    canonical: TelemetryPoint
    version: str
    applied: dict[str, dict[str, float | str]]


class FeatureCanonicalizer:
    """Validate raw telemetry and stabilize only configured severe attack regions."""

    def __init__(self, version: str, severe_syn: dict[str, float]) -> None:
        self.version = version
        self.severe_syn = severe_syn

    @classmethod
    def from_path(cls, path: Path | None) -> "FeatureCanonicalizer":
        if path is None:
            return cls.default()
        if not path.exists():
            raise ValueError(f"canonicalization config does not exist: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            version = str(payload["version"])
            severe_syn = {key: float(value) for key, value in payload["severe_syn"].items()}
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid canonicalization config {path}: {exc}") from exc
        required = {
            "syn_rate_min",
            "incomplete_ratio_min",
            "handshake_completion_ratio_max",
            "syn_rate_value",
            "incomplete_ratio_value",
            "handshake_completion_ratio_value",
        }
        missing = required.difference(severe_syn)
        if missing:
            raise ValueError(f"canonicalization config missing keys: {sorted(missing)}")
        return cls(version, severe_syn)

    @classmethod
    def default(cls) -> "FeatureCanonicalizer":
        return cls(
            "canonicalization-v1-default",
            {
                "syn_rate_min": 100.0,
                "incomplete_ratio_min": 0.75,
                "handshake_completion_ratio_max": 0.25,
                "syn_rate_value": 250.0,
                "incomplete_ratio_value": 0.95,
                "handshake_completion_ratio_value": 0.05,
            },
        )

    @staticmethod
    def validate(point: TelemetryPoint) -> TelemetryPoint:
        values = point.to_dict()
        for feature in FEATURE_NAMES:
            value = values[feature]
            if not math.isfinite(value):
                raise ValueError(f"feature {feature} must be finite")
            if value < 0:
                raise ValueError(f"feature {feature} must be non-negative")
            if feature in RATIO_FEATURES and value > 1:
                raise ValueError(f"feature {feature} must be between 0 and 1")
        return TelemetryPoint(**values)

    def transform(
        self,
        point: TelemetryPoint,
        *,
        apply_attack_buckets: bool,
        neutral_values: dict[str, float] | None = None,
    ) -> CanonicalizationResult:
        raw = self.validate(point)
        values = raw.to_dict()
        applied: dict[str, dict[str, float | str]] = {}
        for feature, neutral_value in (neutral_values or {}).items():
            if feature not in FEATURE_NAMES:
                raise ValueError(f"cannot neutralize unknown feature {feature}")
            observed = values[feature]
            values[feature] = float(neutral_value)
            applied[feature] = {
                "bucket": "unavailable_neutral",
                "raw": observed,
                "canonical": float(neutral_value),
            }
        cfg = self.severe_syn
        severe = (
            apply_attack_buckets
            and raw.syn_rate >= cfg["syn_rate_min"]
            and raw.incomplete_ratio >= cfg["incomplete_ratio_min"]
            and raw.handshake_completion_ratio <= cfg["handshake_completion_ratio_max"]
        )
        if severe:
            replacements = {
                "syn_rate": cfg["syn_rate_value"],
                "incomplete_ratio": cfg["incomplete_ratio_value"],
                "handshake_completion_ratio": cfg["handshake_completion_ratio_value"],
            }
            for feature, replacement in replacements.items():
                observed = values[feature]
                values[feature] = replacement
                applied[feature] = {
                    "bucket": "severe_syn",
                    "raw": observed,
                    "canonical": replacement,
                }
        return CanonicalizationResult(raw, TelemetryPoint(**values), self.version, applied)
