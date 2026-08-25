from fastapi import APIRouter

router = APIRouter()


@router.post(
    "/login",
    summary="Authenticate a user",
    description="Placeholder authentication endpoint for the Next.js frontend to call once the legacy auth service is fully ported.",
)
def login() -> dict[str, str]:
    return {"message": "Authentication is handled by the existing Python auth service logic."}
