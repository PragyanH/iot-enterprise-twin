from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.domain.telemetry import (
    DevicePrediction,
    SignalContribution,
    TelemetryPoint,
    TelemetryWindow,
)
from app.rules.engine import RuleEngine
from app.telemetry.provenance import normalize_source_mode, sensor_name
from app.ml.trust_composer import TrustComposer


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    device_id: str
    name: str
    sector: str
    source: str
    baseline: dict[str, float]
    deviation: dict[str, float]
    feature_names: tuple[str, ...]


MOCK_FEATURES = ("packet_size", "iat", "payload_entropy", "flow_symmetry")
PI_FEATURES = (
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
    "rejected_connections",
    "reset_connections",
    "orig_packets",
    "resp_packets",
    "connection_duration_mean",
    "ssh_attempts",
    "ssh_failures",
)
CLASS_LABELS = ("normal", "syn_flood", "port_scan", "ssh_bruteforce")


@dataclass(frozen=True, slots=True)
class ClassifierResult:
    label: str
    confidence: float
    probabilities: dict[str, float]
    margin: float
    confident: bool
    known_attack_confident: bool
    status: str
    backend: str
    model_version: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 6),
            "probabilities": {key: round(value, 6) for key, value in self.probabilities.items()},
            "margin": round(self.margin, 6),
            "confident": self.confident,
            "known_attack_confident": self.known_attack_confident,
            "status": self.status,
            "backend": self.backend,
            "model_version": self.model_version,
        }


def load_intelligence_config(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        raise ValueError(f"intelligence configuration does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        classifier = payload["classifier"]
        unknown = payload["unknown_anomaly"]
        trust_profiles = payload["trust_profiles"]
        unknown_weights = unknown["weights"]
        for values in (classifier, unknown_weights, trust_profiles["pi"], trust_profiles["mock"]):
            if not isinstance(values, dict):
                raise TypeError("configuration section must be a mapping")
            if not all(math.isfinite(float(value)) and float(value) >= 0 for value in values.values()):
                raise ValueError("configuration weights and thresholds must be finite and non-negative")
        if not math.isclose(sum(float(value) for value in unknown_weights.values()), 1.0, abs_tol=1e-6):
            raise ValueError("unknown anomaly weights must sum to 1")
        for profile_name in ("pi", "mock"):
            if not math.isclose(
                sum(float(value) for value in trust_profiles[profile_name].values()),
                1.0,
                abs_tol=1e-6,
            ):
                raise ValueError(f"{profile_name} trust weights must sum to 1")
        return payload
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid intelligence configuration {path}: {exc}") from exc


def _mock_profile(
    device_id: str,
    name: str,
    sector: str,
    baseline: tuple[float, float, float, float],
) -> DeviceProfile:
    means = dict(zip(MOCK_FEATURES, baseline, strict=True))
    return DeviceProfile(
        device_id=device_id,
        name=name,
        sector=sector,
        source="mock",
        baseline=means,
        deviation={feature: 0.035 for feature in MOCK_FEATURES},
        feature_names=MOCK_FEATURES,
    )


DEFAULT_PROFILES: dict[str, DeviceProfile] = {
    "PI-001": DeviceProfile(
        device_id="PI-001",
        name="AEGIS Raspberry Pi",
        sector="Hardware Lab",
        source="pi",
        baseline={
            "packet_size": 420.0,
            "iat": 0.12,
            "flow_symmetry": 0.92,
            "syn_rate": 3.0,
            "syn_ack_rate": 2.8,
            "ack_rate": 2.7,
            "incomplete_ratio": 0.03,
            "handshake_completion_ratio": 0.96,
            "unique_sources": 2.0,
            "unique_destination_ports": 2.0,
            "rejected_connections": 0.2,
            "reset_connections": 0.2,
            "orig_packets": 24.0,
            "resp_packets": 22.0,
            "connection_duration_mean": 0.8,
            "ssh_attempts": 0.1,
            "ssh_failures": 0.0,
        },
        deviation={
            "packet_size": 100.0,
            "iat": 0.05,
            "flow_symmetry": 0.08,
            "syn_rate": 3.0,
            "syn_ack_rate": 2.0,
            "ack_rate": 2.0,
            "incomplete_ratio": 0.05,
            "handshake_completion_ratio": 0.05,
            "unique_sources": 2.0,
            "unique_destination_ports": 2.0,
            "rejected_connections": 1.0,
            "reset_connections": 1.0,
            "orig_packets": 12.0,
            "resp_packets": 12.0,
            "connection_duration_mean": 0.4,
            "ssh_attempts": 1.0,
            "ssh_failures": 1.0,
        },
        feature_names=PI_FEATURES,
    ),
    "DEV-001": _mock_profile("DEV-001", "AEGIS Pump 01", "Alpha", (0.40, 0.50, 0.30, 0.60)),
    "DEV-002": _mock_profile("DEV-002", "Assembly Arm", "Beta", (0.60, 0.30, 0.70, 0.50)),
    "DEV-003": _mock_profile("DEV-003", "Grid Node 0X", "Gamma", (0.35, 0.62, 0.45, 0.70)),
    "DEV-004": _mock_profile("DEV-004", "Security Camera", "Alpha", (0.52, 0.42, 0.66, 0.56)),
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def sigmoid(value: float) -> float:
    if value >= 0:
        exp_value = math.exp(-value)
        return 1.0 / (1.0 + exp_value)
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def _softmax(values: list[float]) -> list[float]:
    if not values:
        return []
    peak = max(values)
    weights = [math.exp(min(20.0, value - peak)) for value in values]
    denominator = sum(weights) or 1.0
    return [round(value / denominator, 6) for value in weights]


def _histogram(values: list[float], edges: list[float]) -> list[float]:
    counts = [1e-6] * (len(edges) - 1)
    for value in values:
        index = len(counts) - 1
        for candidate in range(len(counts)):
            if value < edges[candidate + 1]:
                index = candidate
                break
        counts[index] += 1.0
    total = sum(counts)
    return [count / total for count in counts]


def _jsd_distribution(p: list[float], q: list[float]) -> float:
    mixture = [(left + right) / 2.0 for left, right in zip(p, q, strict=True)]

    def divergence(values: list[float]) -> float:
        return sum(value * math.log2(value / middle) for value, middle in zip(values, mixture, strict=True))

    return clamp(0.5 * (divergence(p) + divergence(q)))


def _reference_values(mean: float, deviation: float, count: int) -> list[float]:
    pattern = (-0.55, 0.25, -0.15, 0.45, 0.05, -0.35, 0.60, -0.05, 0.32, -0.42)
    return [mean + deviation * pattern[index % len(pattern)] for index in range(max(count, 10))]


def per_feature_jsd_evidence(
    points: list[TelemetryPoint],
    profile: DeviceProfile,
    unavailable_features: set[str] | None = None,
) -> tuple[float, dict[str, float], dict[str, dict[str, object]]]:
    unavailable = unavailable_features or set()
    feature_scores: dict[str, float] = {}
    availability: dict[str, dict[str, object]] = {}
    for feature in profile.feature_names:
        if feature in unavailable:
            availability[feature] = {
                "available": False,
                "reason": "sensor_does_not_supply_feature",
                "jsd": None,
            }
            continue
        current = [point.value(feature) for point in points]
        if not current or not all(math.isfinite(value) for value in current):
            availability[feature] = {
                "available": False,
                "reason": "invalid_or_empty_window",
                "jsd": None,
            }
            continue
        mean = profile.baseline[feature]
        deviation = max(profile.deviation[feature], 1e-6)
        reference = _reference_values(mean, deviation, len(current))
        low = min(min(current), min(reference), mean - 4.0 * deviation)
        high = max(max(current), max(reference), mean + 4.0 * deviation)
        if math.isclose(low, high):
            feature_scores[feature] = 0.0
            availability[feature] = {"available": True, "reason": None, "jsd": 0.0}
            continue
        width = (high - low) / 8.0
        edges = [low + width * index for index in range(9)]
        score = _jsd_distribution(
            _histogram(current, edges),
            _histogram(reference, edges),
        )
        score = score if math.isfinite(score) else 0.0
        feature_scores[feature] = clamp(score)
        availability[feature] = {
            "available": True,
            "reason": None,
            "jsd": round(feature_scores[feature], 6),
        }
    global_score = _mean(feature_scores.values()) if feature_scores else 0.0
    return clamp(global_score), feature_scores, availability


def per_feature_jsd(points: list[TelemetryPoint], profile: DeviceProfile) -> tuple[float, dict[str, float]]:
    global_score, scores, _ = per_feature_jsd_evidence(points, profile)
    return global_score, scores


class OptionalXGBoostClassifier:
    """Loads a frozen XGBoost artifact when installed; otherwise uses calibrated rules."""

    def __init__(
        self,
        artifact_path: Path | None = None,
        confidence_config: dict[str, object] | None = None,
        model_version: str = "xgboost-v1",
    ) -> None:
        self._booster = None
        self._xgb = None
        self._config = confidence_config or {
            "known_min_probability": 0.70,
            "known_min_margin": 0.20,
            "normal_min_probability": 0.55,
            "normal_min_margin": 0.10,
        }
        self._model_version = model_version
        if artifact_path is None or not artifact_path.exists():
            return
        try:
            import xgboost as xgb  # type: ignore[import-not-found]

            booster = xgb.Booster()
            booster.load_model(str(artifact_path))
            self._xgb = xgb
            self._booster = booster
        except (ImportError, OSError, ValueError):
            self._booster = None
            self._xgb = None

    @property
    def backend(self) -> str:
        return "xgboost" if self._booster is not None else "calibrated-fallback"

    def predict(self, latest: TelemetryPoint, profile: DeviceProfile) -> ClassifierResult:
        backend = self.backend
        if self._booster is not None and self._xgb is not None:
            values = [[latest.value(feature) for feature in profile.feature_names]]
            prediction = self._booster.predict(self._xgb.DMatrix(values))[0]
            if hasattr(prediction, "tolist"):
                probabilities = prediction.tolist()
            else:
                probabilities = [1.0 - float(prediction), float(prediction), 0.0, 0.0]
            values_out = [float(value) for value in probabilities[: len(CLASS_LABELS)]]
        else:
            syn = sigmoid(
                (latest.syn_rate - 45.0) / 12.0
                + (latest.incomplete_ratio - 0.45) * 5.0
                + (0.55 - latest.handshake_completion_ratio) * 4.0
            )
            scan = sigmoid(
                (latest.unique_destination_ports - 14.0) / 4.0
                + (latest.rejected_connections - 7.0) / 3.0
            )
            ssh = sigmoid(
                (latest.ssh_failures - 4.0) / 1.5
                + (latest.ssh_attempts - 6.0) / 2.5
            )
            values_out = [max(0.01, 1.0 - max(syn, scan, ssh)), syn, scan, ssh]

        if len(values_out) != len(CLASS_LABELS) or not all(
            math.isfinite(value) and value >= 0.0 for value in values_out
        ) or sum(values_out) <= 0:
            values_out = [1.0, 0.0, 0.0, 0.0]
            backend = f"{backend}-invalid-output-fallback"
        total = sum(values_out)
        normalized = [value / total for value in values_out]
        probabilities_map = dict(zip(CLASS_LABELS, normalized, strict=True))
        ranking = sorted(enumerate(normalized), key=lambda item: (-item[1], item[0]))
        index, confidence = ranking[0]
        margin = confidence - ranking[1][1]
        label = CLASS_LABELS[index]
        if label == "normal":
            confident = confidence >= float(self._config["normal_min_probability"]) and margin >= float(
                self._config["normal_min_margin"]
            )
            status = "confident_normal" if confident else "inconclusive"
            known_attack_confident = False
        else:
            confident = confidence >= float(self._config["known_min_probability"]) and margin >= float(
                self._config["known_min_margin"]
            )
            known_attack_confident = confident
            status = "confident_known_attack" if confident else "inconclusive"
        return ClassifierResult(
            label, confidence, probabilities_map, margin, confident,
            known_attack_confident, status, backend, self._model_version,
        )


class OptionalTemporalVAE:
    """Runs frozen PyTorch checkpoints when available and reports its real backend."""

    def __init__(self, artifact_dir: Path | None) -> None:
        self._torch = None
        self._models: dict[str, object] = {}
        self._thresholds = {"pi": 0.18, "mock": 0.18}
        if artifact_dir is None:
            return
        calibration_path = artifact_dir / "calibration.json"
        if calibration_path.exists():
            try:
                calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
                self._thresholds.update(
                    {key: float(value) for key, value in calibration.get("vae_thresholds", {}).items()}
                )
            except (OSError, ValueError, TypeError):
                pass
        try:
            import torch  # type: ignore[import-not-found]

            from app.ml.temporal_vae import load_temporal_vae

            for source, input_size in (("pi", len(PI_FEATURES)), ("mock", len(MOCK_FEATURES))):
                checkpoint = artifact_dir / f"temporal_vae_{source}.pt"
                if checkpoint.exists():
                    self._models[source] = load_temporal_vae(checkpoint, input_size)
            self._torch = torch
        except (ImportError, OSError, RuntimeError, ValueError):
            self._models = {}
            self._torch = None

    def backend(self, source: str) -> str:
        return "pytorch-lstm-vae" if source in self._models else "calibrated-reconstruction-proxy"

    def score(
        self,
        points: list[TelemetryPoint],
        profile: DeviceProfile,
        proxy_error: float,
        proxy_attention: list[float],
    ) -> dict[str, object]:
        threshold = max(self._thresholds.get(profile.source, 0.18), 1e-6)
        model = self._models.get(profile.source)
        if model is None or self._torch is None:
            uncertainty = clamp(math.sqrt(max(proxy_error, 0.0)) / 2.0)
            risk = clamp(1.0 - math.exp(-2.4 * proxy_error))
            return {
                "raw_reconstruction_error": round(proxy_error, 6),
                "threshold": round(threshold, 6),
                "normalized_anomaly_risk": round(risk, 6),
                "is_anomalous": risk >= 0.72,
                "latent_uncertainty": round(uncertainty, 6),
                "attention_weights": proxy_attention,
                "temporal_importance": [
                    {"time_step": index - len(proxy_attention) + 1, "weight": weight}
                    for index, weight in enumerate(proxy_attention)
                ],
                "reconstructed_sequence_summary": {
                    "available": False,
                    "reason": "learned_checkpoint_unavailable_using_proxy",
                },
                "backend": self.backend(profile.source),
            }

        padded = list(points[-20:])
        while len(padded) < 20:
            padded.insert(0, padded[0])
        values = [
            [
                (point.value(feature) - profile.baseline[feature]) / max(profile.deviation[feature], 1e-6)
                for feature in profile.feature_names
            ]
            for point in padded
        ]
        tensor = self._torch.tensor([values], dtype=self._torch.float32)
        with self._torch.no_grad():
            output = model(tensor)
            reconstruction = self._torch.nn.functional.mse_loss(
                output.reconstruction, tensor, reduction="none"
            ).mean(dim=(1, 2))
            uncertainty = self._torch.exp(output.log_variance).mean(dim=1)
        error = max(0.0, float(reconstruction.item()))
        uncertainty_value = clamp(float(uncertainty.item()) / 3.0)
        risk = clamp(error / threshold)
        attention = [round(float(value), 6) for value in output.attention_weights[0].tolist()]
        observed_mean = tensor[0].mean(dim=0).tolist()
        reconstructed_mean = output.reconstruction[0].mean(dim=0).tolist()
        return {
            "raw_reconstruction_error": round(error, 6),
            "threshold": round(threshold, 6),
            "normalized_anomaly_risk": round(risk, 6),
            "is_anomalous": risk >= 0.72,
            "latent_uncertainty": round(uncertainty_value, 6),
            "attention_weights": attention,
            "temporal_importance": [
                {"time_step": index - len(attention) + 1, "weight": weight}
                for index, weight in enumerate(attention)
            ],
            "reconstructed_sequence_summary": {
                "available": True,
                "space": "baseline_standardized",
                "observed_feature_means": {
                    feature: round(float(value), 6)
                    for feature, value in zip(profile.feature_names, observed_mean, strict=True)
                },
                "reconstructed_feature_means": {
                    feature: round(float(value), 6)
                    for feature, value in zip(profile.feature_names, reconstructed_mean, strict=True)
                },
            },
            "backend": self.backend(profile.source),
        }


class HybridTrustEngine:
    """Deterministic, calibrated fusion around optional learned model artifacts."""

    def __init__(
        self,
        profiles: dict[str, DeviceProfile] | None = None,
        xgboost_artifact: Path | None = None,
        vae_artifact_dir: Path | None = None,
        rule_engine: RuleEngine | None = None,
        intelligence_config_path: Path | None = None,
    ) -> None:
        self.profiles = profiles or DEFAULT_PROFILES
        self.intelligence = load_intelligence_config(intelligence_config_path)
        self.classifier = OptionalXGBoostClassifier(
            xgboost_artifact,
            self.intelligence["classifier"],  # type: ignore[arg-type]
            "aegis-xgboost-v1",
        )
        self.temporal_vae = OptionalTemporalVAE(vae_artifact_dir)
        self.rule_engine = rule_engine
        self.trust_composer = TrustComposer(self.intelligence["trust_profiles"])  # type: ignore[arg-type]

    def profile(self, device_id: str) -> DeviceProfile:
        try:
            return self.profiles[device_id]
        except KeyError as exc:
            raise KeyError(f"unknown device: {device_id}") from exc

    def _deviations(
        self,
        points: list[TelemetryPoint],
        profile: DeviceProfile,
        unavailable_features: set[str],
    ) -> tuple[dict[str, float], dict[str, float], list[float]]:
        current = {
            feature: _mean(point.value(feature) for point in points[-5:])
            for feature in profile.feature_names
        }
        z_scores = {
            feature: (
                0.0
                if feature in unavailable_features
                else abs(current[feature] - profile.baseline[feature])
                / max(profile.deviation[feature], 1e-6)
            )
            for feature in profile.feature_names
        }
        active = [feature for feature in profile.feature_names if feature not in unavailable_features]
        energies = []
        for point in points:
            energy = _mean(
                min(
                    ((point.value(feature) - profile.baseline[feature]) / max(profile.deviation[feature], 1e-6)) ** 2,
                    100.0,
                )
                for feature in active
            )
            energies.append(energy)
        return current, z_scores, energies

    @staticmethod
    def _mock_rule(z_scores: dict[str, float]) -> tuple[float, bool]:
        elevated = sum(score >= 3.0 for score in z_scores.values())
        ordered = sorted(z_scores.values(), reverse=True)
        top_two = _mean(ordered[:2]) if ordered else 0.0
        return clamp(top_two / 6.0), elevated >= 2

    def score(
        self,
        window: TelemetryWindow,
        *,
        previous_trust: float = 98.0,
        previous_risk: float = 0.02,
        recovering: bool = False,
        recovery_clean_windows: int = 0,
        recovery_clean_windows_required: int = 3,
        raw_latest: TelemetryPoint | None = None,
        canonicalization_version: str = "none",
        supplied_sensor: str | None = None,
        canonicalization_applied: dict[str, dict[str, float | str]] | None = None,
        unavailable_features: set[str] | None = None,
    ) -> DevicePrediction:
        profile = self.profile(window.device_id)
        points = window.points[-20:]
        if not points:
            raise ValueError("telemetry window must contain at least one point")
        unavailable = unavailable_features or set(window.unavailable_features)
        current, z_scores, temporal_energy = self._deviations(points, profile, unavailable)
        proxy_attention = _softmax([min(12.0, energy / 2.0) for energy in temporal_energy])
        proxy_error = _mean(min(25.0, energy) for energy in temporal_energy) / 25.0
        temporal = self.temporal_vae.score(
            points,
            profile,
            proxy_error,
            proxy_attention,
        )
        reconstruction_error = float(temporal["raw_reconstruction_error"])
        latent_uncertainty = float(temporal["latent_uncertainty"])
        attention = list(temporal["attention_weights"])  # type: ignore[arg-type]
        vae_risk = float(temporal["normalized_anomaly_risk"])
        jsd, jsd_by_feature, feature_availability = per_feature_jsd_evidence(
            points, profile, unavailable
        )

        ordered_z = sorted(
            (score for feature, score in z_scores.items() if feature not in unavailable),
            reverse=True,
        )
        baseline_risk = clamp(_mean(ordered_z[:2]) / 6.0 if ordered_z else 0.0)
        classifier = ClassifierResult(
            "normal", 1.0, {label: 1.0 if label == "normal" else 0.0 for label in CLASS_LABELS},
            1.0, True, False, "not_applicable", "not-applicable", "not-applicable",
        )
        rule_label = "none"
        rule_payload: dict[str, object] = {
            "rule_id": None,
            "matched": False,
            "conditions": [],
            "matched_conditions": [],
            "failed_conditions": [],
        }
        matched_known_rule = False
        classifier_payload: dict[str, object]
        if profile.source == "pi":
            evaluations = self.rule_engine.evaluate(window.latest, raw_latest) if self.rule_engine else []
            selected_rule = max(evaluations, key=lambda item: (item.matched, item.risk), default=None)
            if selected_rule is not None:
                rule_payload = selected_rule.to_dict()
                rule_risk = selected_rule.risk
                matched_known_rule = selected_rule.matched
                rule_label = selected_rule.attack_type if selected_rule.matched or selected_rule.risk >= 0.35 else "none"
            else:
                rule_risk = 0.0
            classifier = self.classifier.predict(window.latest, profile)
            classifier_risk = (
                classifier.confidence if classifier.label != "normal" else 1.0 - classifier.confidence
            )
            supporting_min = float(self.intelligence["classifier"]["supporting_evidence_min"])  # type: ignore[index]
            classifier_known = classifier.known_attack_confident and max(
                vae_risk, jsd, baseline_risk
            ) >= supporting_min
            classifier_payload = classifier.to_dict()
            classifier_payload["supporting_behavioral_evidence"] = round(
                max(vae_risk, jsd, baseline_risk), 6
            )
            classifier_payload["supporting_evidence_min"] = round(supporting_min, 6)
            classifier_payload["accepted_as_known_attack"] = classifier_known
            known_confirmed = matched_known_rule or classifier_known
            known_attack_risk = max(rule_risk, classifier_risk if classifier_known else 0.0)
            detector_risks = {
                "rule": rule_risk,
                "classifier": classifier_risk,
                "vae": vae_risk,
                "jsd": jsd,
            }
        else:
            rule_risk, matched_known_rule = self._mock_rule(z_scores)
            classifier_risk = 0.0
            known_confirmed = matched_known_rule
            known_attack_risk = rule_risk
            detector_risks = {"baseline": baseline_risk, "vae": vae_risk, "jsd": jsd}
            classifier_payload = classifier.to_dict()

        unknown_config = self.intelligence["unknown_anomaly"]  # type: ignore[assignment]
        unknown_weights = unknown_config["weights"]  # type: ignore[index]
        unknown_score = clamp(
            float(unknown_weights["temporal"]) * vae_risk
            + float(unknown_weights["jsd"]) * jsd
            + float(unknown_weights["baseline"]) * baseline_risk
        )
        unknown_eligible = not matched_known_rule and not classifier.known_attack_confident
        unknown_confirmed = unknown_eligible and unknown_score >= float(unknown_config["attack_threshold"])  # type: ignore[index]

        stale = window.stale or window.latest.capture_loss >= 0.25
        clean = (
            not stale
            and not known_confirmed
            and not unknown_confirmed
            and unknown_score < float(unknown_config["suspicious_threshold"])  # type: ignore[index]
            and baseline_risk < 0.28
            and rule_risk < 0.25
            and window.service_healthy
        )
        trust_result = self.trust_composer.compose(
            profile=profile.source,
            detector_risks=detector_risks,
            unknown_anomaly_score=unknown_score,
            unknown_eligible=unknown_eligible,
            known_confirmed=known_confirmed,
            unknown_confirmed=unknown_confirmed,
            clean=clean,
            stale=stale,
            recovering=recovering,
            recovery_clean_windows=recovery_clean_windows,
            recovery_clean_windows_required=recovery_clean_windows_required,
            previous_trust=previous_trust,
            previous_risk=previous_risk,
        )
        state, trust, smoothed_risk = trust_result.state, trust_result.trust, trust_result.risk
        telemetry_quality = "stale" if window.stale else "capture-loss" if stale else "good"

        if unknown_confirmed:
            attack_type = "unknown_behavioral_anomaly"
            detection_mode = "unknown_anomaly"
        elif known_confirmed:
            attack_type = (
                rule_label if rule_label != "none" else
                "behavioral_drift" if profile.source == "mock" else classifier.label
            )
            detection_mode = "known_attack"
        elif state == "SUSPICIOUS":
            attack_type = "behavioral_anomaly"
            detection_mode = "suspicious"
        else:
            attack_type = "none"
            detection_mode = "normal" if state == "HEALTHY" else state.lower()

        contributions = []
        for feature, score in z_scores.items():
            delta = current[feature] - profile.baseline[feature]
            direction = "high" if delta > 0 else "low" if delta < 0 else "stable"
            combined_score = clamp(0.75 * (score / 6.0) + 0.25 * jsd_by_feature.get(feature, 0.0))
            if feature not in unavailable:
                severity = "critical" if combined_score >= 0.8 else "high" if combined_score >= 0.6 else "medium" if combined_score >= 0.3 else "low"
                contributions.append(SignalContribution(feature, round(combined_score, 4), direction, severity))
        contributions.sort(key=lambda item: (-item.score, item.feature))

        confidence = max(
            classifier.confidence if classifier.label != "normal" else 0.0,
            rule_risk,
            unknown_score if unknown_confirmed else 0.0,
            smoothed_risk if state == "ATTACK" else 1.0 - smoothed_risk,
        )
        raw_point = raw_latest or window.latest
        deviations: dict[str, dict[str, float | str | bool | None]] = {}
        for feature in profile.feature_names:
            available = feature not in unavailable
            canonical_delta = current[feature] - profile.baseline[feature]
            raw_observed = raw_point.value(feature)
            direction = "high" if canonical_delta > 0 else "low" if canonical_delta < 0 else "stable"
            normalized = z_scores[feature] if available else 0.0
            severity = "unavailable" if not available else "critical" if normalized >= 6 else "high" if normalized >= 4 else "medium" if normalized >= 2 else "low"
            deviations[feature] = {
                "baseline": round(profile.baseline[feature], 6),
                "raw_observed": round(raw_observed, 6),
                "canonical_observed": round(window.latest.value(feature), 6),
                "current_window_mean": round(current[feature], 6),
                "raw_delta": round(raw_observed - profile.baseline[feature], 6),
                "canonical_delta": round(canonical_delta, 6),
                "absolute_delta": round(abs(canonical_delta), 6),
                "normalized_deviation": round(normalized, 6),
                "direction": direction,
                "severity": severity,
                "available": available,
            }
        mitre = rule_payload.get("mitre") if known_confirmed and rule_payload.get("matched") else None
        if known_confirmed and not mitre and profile.source == "pi":
            classifier_mitre = {
                "syn_flood": {"technique_id": "T1498.001", "technique_name": "Direct Network Flood", "tactic": "Impact"},
                "port_scan": {"technique_id": "T1046", "technique_name": "Network Service Discovery", "tactic": "Discovery"},
                "ssh_bruteforce": {"technique_id": "T1110.001", "technique_name": "Password Guessing", "tactic": "Credential Access"},
            }
            mitre = classifier_mitre.get(classifier.label)
        classification = {
            "type": attack_type,
            "known": detection_mode == "known_attack",
            "confidence": round(clamp(confidence), 6),
            "mitre_status": "mapped" if mitre else "unmapped",
            "mitre": mitre,
        }
        source_mode = normalize_source_mode(window.source)
        return DevicePrediction(
            device_id=window.device_id,
            source=window.source,
            trust=round(trust, 2),
            state=state,  # type: ignore[arg-type]
            attack_type=attack_type if state in {"ATTACK", "SUSPICIOUS"} else "none",
            confidence=round(clamp(confidence), 4),
            risk=round(clamp(smoothed_risk), 4),
            reconstruction_error=round(reconstruction_error, 6),
            latent_uncertainty=round(latent_uncertainty, 6),
            jsd=round(jsd, 6),
            rule_risk=round(rule_risk, 6),
            classifier_risk=round(classifier_risk, 6),
            vae_risk=round(vae_risk, 6),
            baseline_risk=round(baseline_risk, 6),
            attention_weights=attention,
            top_anomalies=contributions[:4],
            current_features={feature: round(value, 6) for feature, value in current.items()},
            baseline_features=profile.baseline.copy(),
            timestamp=window.timestamp,
            telemetry_quality=telemetry_quality,
            model_backends={
                "vae": self.temporal_vae.backend(profile.source),
                "classifier": self.classifier.backend if profile.source == "pi" else "not-applicable",
                "drift": "per-feature-jsd",
                "rules": (
                    self.rule_engine.ruleset_version
                    if profile.source == "pi" and self.rule_engine
                    else "mock-multifeature-policy-v1"
                ),
            },
            source_mode=source_mode,
            sensor=sensor_name(source_mode, supplied_sensor or window.sensor),
            raw_features=(raw_latest or window.latest).to_dict(),
            canonical_features=window.latest.to_dict(),
            feature_deviations=deviations,
            rule=rule_payload,
            jsd_by_feature={key: round(value, 6) for key, value in jsd_by_feature.items()},
            canonicalization_version=canonicalization_version,
            canonicalization_applied=canonicalization_applied or {},
            feature_availability=feature_availability,
            classifier=classifier_payload,
            temporal=temporal,
            detectors={
                **{key: round(clamp(value), 6) for key, value in detector_risks.items()},
                "known_attack": round(clamp(known_attack_risk), 6),
                "unknown_anomaly": round(unknown_score, 6),
            },
            trust_calculation=trust_result.calculation,
            detection_mode=detection_mode,
            known_attack_risk=round(clamp(known_attack_risk), 6),
            unknown_anomaly_score=round(unknown_score, 6),
            classification=classification,
        )


def load_profiles(path: Path) -> dict[str, DeviceProfile]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    profiles: dict[str, DeviceProfile] = {}
    for item in payload["devices"]:
        profiles[item["device_id"]] = DeviceProfile(
            device_id=item["device_id"],
            name=item["name"],
            sector=item["sector"],
            source=item["source"],
            baseline={key: float(value) for key, value in item["baseline"].items()},
            deviation={key: float(value) for key, value in item["deviation"].items()},
            feature_names=tuple(item["feature_names"]),
        )
    return profiles
