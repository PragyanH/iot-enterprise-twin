from __future__ import annotations

import math
import operator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from app.domain.telemetry import FEATURE_NAMES, TelemetryPoint


OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
}


@dataclass(frozen=True, slots=True)
class RuleConditionResult:
    feature: str
    operator: str
    threshold: float
    observed: float
    raw_observed: float
    passed: bool


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    rule_id: str
    name: str
    attack_type: str
    severity: str
    matched: bool
    risk: float
    conditions: tuple[RuleConditionResult, ...]
    required_conditions: int
    mitre: dict[str, str]
    response: dict[str, str]
    explanation: str
    version: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "attack_type": self.attack_type,
            "severity": self.severity,
            "matched": self.matched,
            "risk": round(self.risk, 6),
            "conditions": [asdict(condition) for condition in self.conditions],
            "matched_conditions": [asdict(item) for item in self.conditions if item.passed],
            "failed_conditions": [asdict(item) for item in self.conditions if not item.passed],
            "required_conditions": self.required_conditions,
            "mitre": self.mitre,
            "response": self.response,
            "explanation": self.explanation,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class RuleDefinition:
    rule_id: str
    name: str
    attack_type: str
    severity: str
    conditions: tuple[tuple[str, str, float], ...]
    required_conditions: int
    mitre: dict[str, str]
    response: dict[str, str]
    explanation: str
    version: str


class RuleEngine:
    def __init__(self, rules: tuple[RuleDefinition, ...], ruleset_version: str) -> None:
        if not rules:
            raise ValueError("rule set must contain at least one rule")
        self.rules = rules
        self.ruleset_version = ruleset_version

    def evaluate(self, canonical: TelemetryPoint, raw: TelemetryPoint | None = None) -> list[RuleEvaluation]:
        raw = raw or canonical
        results: list[RuleEvaluation] = []
        for rule in self.rules:
            conditions = []
            severities = []
            for feature, operation, threshold in rule.conditions:
                observed = canonical.value(feature)
                raw_observed = raw.value(feature)
                passed = OPERATORS[operation](observed, threshold)
                conditions.append(
                    RuleConditionResult(feature, operation, threshold, observed, raw_observed, passed)
                )
                if operation in {">=", ">"}:
                    severities.append(min(1.0, observed / max(threshold, 1e-9)))
                elif operation in {"<=", "<"}:
                    severities.append(min(1.0, max(0.0, (1.0 - observed) / max(1.0 - threshold, 1e-9))))
                else:
                    severities.append(1.0 if passed else 0.0)
            passed_count = sum(item.passed for item in conditions)
            matched = passed_count >= rule.required_conditions
            risk = sum(severities) / len(severities) if severities else 0.0
            results.append(
                RuleEvaluation(
                    rule.rule_id,
                    rule.name,
                    rule.attack_type,
                    rule.severity,
                    matched,
                    risk,
                    tuple(conditions),
                    rule.required_conditions,
                    rule.mitre,
                    rule.response,
                    rule.explanation,
                    rule.version,
                )
            )
        return results


def _require_mapping(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be a mapping")
    return value


def load_rule_engine(path: Path) -> RuleEngine:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"unable to load rule YAML {path}: {exc}") from exc
    root = _require_mapping(payload, "rules document")
    ruleset_version = str(root.get("ruleset_version", "")).strip()
    if not ruleset_version:
        raise ValueError("ruleset_version is required")
    raw_rules = root.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ValueError("rules must be a non-empty list")
    definitions: list[RuleDefinition] = []
    seen: set[str] = set()
    for index, raw_rule in enumerate(raw_rules):
        rule = _require_mapping(raw_rule, f"rules[{index}]")
        rule_id = str(rule.get("id", "")).strip()
        if not rule_id or rule_id in seen:
            raise ValueError(f"rules[{index}].id must be unique and non-empty")
        seen.add(rule_id)
        raw_conditions = rule.get("conditions")
        if not isinstance(raw_conditions, list) or not raw_conditions:
            raise ValueError(f"rule {rule_id} must define conditions")
        conditions: list[tuple[str, str, float]] = []
        for condition_index, raw_condition in enumerate(raw_conditions):
            condition = _require_mapping(raw_condition, f"rule {rule_id} condition {condition_index}")
            feature = str(condition.get("feature", ""))
            operation = str(condition.get("operator", ""))
            if feature not in FEATURE_NAMES:
                raise ValueError(f"rule {rule_id} uses unknown feature {feature!r}")
            if operation not in OPERATORS:
                raise ValueError(f"rule {rule_id} uses unsupported operator {operation!r}")
            try:
                threshold = float(condition.get("threshold"))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"rule {rule_id} has an invalid threshold") from exc
            if not math.isfinite(threshold):
                raise ValueError(f"rule {rule_id} has non-finite threshold")
            conditions.append((feature, operation, threshold))
        try:
            required = int(rule.get("required_conditions", len(conditions)))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"rule {rule_id} required_conditions must be an integer") from exc
        if required < 1 or required > len(conditions):
            raise ValueError(f"rule {rule_id} required_conditions is out of range")
        mitre = {str(key): str(value) for key, value in _require_mapping(rule.get("mitre"), f"rule {rule_id}.mitre").items()}
        response = {str(key): str(value) for key, value in _require_mapping(rule.get("response"), f"rule {rule_id}.response").items()}
        required_text = ("name", "attack_type", "severity", "explanation", "version")
        if any(not str(rule.get(key, "")).strip() for key in required_text):
            raise ValueError(f"rule {rule_id} is missing required descriptive fields")
        definitions.append(
            RuleDefinition(
                rule_id,
                str(rule["name"]),
                str(rule["attack_type"]),
                str(rule["severity"]),
                tuple(conditions),
                required,
                mitre,
                response,
                str(rule["explanation"]),
                str(rule["version"]),
            )
        )
    return RuleEngine(tuple(definitions), ruleset_version)
