from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.runtime import intelligence_service, trust_service


router = APIRouter()


@router.get("/devices/{device_id}/explainability", summary="Get current detector and trust evidence")
def explainability(device_id: str) -> dict[str, object]:
    try:
        state = trust_service.state(device_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "schema_version": "aegis-explainability-v1",
        "device_id": device_id,
        "prediction": state,
        "evidence": {
            "feature_deviations": state["feature_deviations"],
            "classifier": state["classifier"],
            "temporal": state["temporal"],
            "jsd": {"global": state["jsd"], "per_feature": state["jsd_by_feature"]},
            "top_anomalies": state["top_anomalies"],
            "trust_calculation": state["trust_calculation"],
        },
    }


@router.get("/model/metrics", summary="Get frozen validation metrics and their scope")
def model_metrics() -> dict[str, object]:
    return intelligence_service.metrics()


@router.get("/mitre/scenarios", summary="List the eight configured ATT&CK demo scenarios")
def mitre_scenarios() -> dict[str, object]:
    return intelligence_service.mitre_scenarios()


@router.post("/xai/scenarios/{scenario}", summary="Run a deterministic scenario through the live trust pipeline")
def run_xai_scenario(
    scenario: str,
    technique_id: str | None = Query(default=None),
) -> dict[str, object]:
    try:
        return intelligence_service.run_xai(scenario, technique_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
