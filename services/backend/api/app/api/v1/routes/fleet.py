from fastapi import APIRouter

router = APIRouter()


@router.get(
    "",
    summary="List fleet devices",
    description="Returns the current fleet overview for the dashboard and operator UI.",
)
def list_fleet() -> list[dict[str, object]]:
    return [
        {"id": "DEV-001", "name": "Sensor Node 1", "sector": "Alpha", "status": "Healthy", "trust": 94},
        {"id": "DEV-002", "name": "Sensor Node 2", "sector": "Beta", "status": "Healthy", "trust": 87},
        {"id": "DEV-003", "name": "Sensor Node 3", "sector": "Gamma", "status": "Monitoring", "trust": 73},
        {"id": "DEV-004", "name": "Sensor Node 4", "sector": "Alpha", "status": "Compromised", "trust": 39},
    ]
