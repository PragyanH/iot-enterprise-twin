from __future__ import annotations

from app.domain.telemetry import SourceKind


_SOURCE_MODES = {
    "mock": "mock",
    "pi": "live_hardware",
    "live_hardware": "live_hardware",
    "replay": "recorded_replay",
    "recorded_replay": "recorded_replay",
    "xai_simulation": "xai_simulation",
}


def normalize_source_mode(source: SourceKind | str) -> str:
    """Return the public provenance label while retaining legacy API aliases."""

    try:
        return _SOURCE_MODES[str(source)]
    except KeyError as exc:
        raise ValueError(f"unsupported telemetry source: {source}") from exc


def sensor_name(source_mode: str, supplied: str | None = None) -> str:
    if supplied and supplied.strip():
        return supplied.strip()
    return {
        "mock": "aegis-simulator",
        "live_hardware": "unspecified-live-sensor",
        "recorded_replay": "aegis-replay",
        "xai_simulation": "aegis-xai-simulator",
    }[source_mode]
