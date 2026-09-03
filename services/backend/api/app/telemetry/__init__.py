"""Sensor-neutral telemetry validation and transformation."""

from app.telemetry.canonicalization import CanonicalizationResult, FeatureCanonicalizer
from app.telemetry.provenance import normalize_source_mode, sensor_name

__all__ = [
    "CanonicalizationResult",
    "FeatureCanonicalizer",
    "normalize_source_mode",
    "sensor_name",
]
