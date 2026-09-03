from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


State = Literal["BOOTSTRAP", "HEALTHY", "SUSPICIOUS", "ATTACK", "RECOVERING", "STALE"]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True, slots=True)
class TrustResult:
    trust: float
    risk: float
    state: State
    calculation: dict[str, object]


class TrustComposer:
    """The single state/trust authority used by live, replay, mock and XAI."""

    def __init__(self, profiles: dict[str, dict[str, float]]) -> None:
        self.profiles = profiles

    def compose(
        self,
        *,
        profile: str,
        detector_risks: dict[str, float],
        unknown_anomaly_score: float,
        unknown_eligible: bool,
        known_confirmed: bool,
        unknown_confirmed: bool,
        clean: bool,
        stale: bool,
        recovering: bool,
        recovery_clean_windows: int,
        recovery_clean_windows_required: int,
        previous_trust: float,
        previous_risk: float,
    ) -> TrustResult:
        weights = self.profiles[profile]
        components = []
        profile_risk = 0.0
        for name, weight in weights.items():
            risk = clamp(detector_risks.get(name, 0.0))
            contribution = risk * weight
            profile_risk += contribution
            components.append(
                {
                    "name": name,
                    "risk": round(risk, 6),
                    "weight": round(weight, 6),
                    "contribution": round(contribution, 6),
                }
            )
        profile_risk = clamp(profile_risk)
        decision_risk = max(
            profile_risk,
            clamp(unknown_anomaly_score) if unknown_eligible else 0.0,
        )
        smoothing_bypassed = known_confirmed or unknown_confirmed

        if stale:
            state: State = "STALE"
            effective_risk = clamp(previous_risk)
            trust = float(previous_trust)
            formula = "freeze_previous_trust"
            constraint = "STALE_FREEZE"
        elif known_confirmed or unknown_confirmed:
            state = "ATTACK"
            effective_risk = max(decision_risk, 0.75)
            trust = max(5.0, min(25.0, 100.0 * (1.0 - effective_risk)))
            formula = "max(5,min(25,100*(1-effective_risk)))"
            constraint = "ATTACK_CAP_25"
        elif recovering and clean:
            effective_risk = clamp(0.65 * previous_risk + 0.35 * decision_risk)
            # The current clean observation is scored before the service increments
            # its counter, hence required-1 completes the configured sequence.
            if recovery_clean_windows >= max(0, recovery_clean_windows_required - 1):
                state = "HEALTHY"
                trust = 97.0
                formula = "verified_recovery_target"
                constraint = "RECOVERY_VERIFIED_97"
            else:
                state = "RECOVERING"
                trust = min(97.0, max(80.0, previous_trust + 24.0))
                formula = "min(97,max(80,previous_trust+24))"
                constraint = "RECOVERING_80_97"
        else:
            effective_risk = clamp(0.65 * previous_risk + 0.35 * decision_risk)
            if clean:
                state = "HEALTHY"
                trust = max(96.0, min(99.0, 99.0 - 16.0 * effective_risk))
                formula = "max(96,min(99,99-16*effective_risk))"
                constraint = "HEALTHY_96_99"
            else:
                state = "SUSPICIOUS"
                trust = max(35.0, min(75.0, 75.0 - 55.0 * effective_risk))
                formula = "max(35,min(75,75-55*effective_risk))"
                constraint = "SUSPICIOUS_35_75"

        calculation: dict[str, object] = {
            "formula_id": "aegis-trust-composer-v1",
            "starting_trust": 100.0,
            "profile": profile,
            "components": components,
            "profile_risk": round(profile_risk, 6),
            "unknown_anomaly_score": round(clamp(unknown_anomaly_score), 6),
            "unknown_eligible": unknown_eligible,
            "selected_decision_risk": round(decision_risk, 6),
            "previous_risk": round(clamp(previous_risk), 6),
            "ewma": {"previous_weight": 0.65, "current_weight": 0.35},
            "smoothing_bypassed": smoothing_bypassed,
            "effective_risk": round(effective_risk, 6),
            "state_constraint": constraint,
            "trust_formula": formula,
            "final_trust": round(trust, 2),
        }
        return TrustResult(round(trust, 2), round(effective_risk, 6), state, calculation)
