from fastapi import APIRouter

from app.core.runtime import trust_service

router = APIRouter()


@router.get(
    "",
    summary="List fleet devices",
    description="Returns the current fleet overview for the dashboard and operator UI.",
)
def list_fleet() -> list[dict[str, object]]:
    return trust_service.fleet()
