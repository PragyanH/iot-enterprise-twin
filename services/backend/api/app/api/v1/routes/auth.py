from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.api.dependencies.auth import admin_user, bearer, current_user, token_credentials
from app.core.runtime import auth_service

router = APIRouter()


class RegisterPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["ADMIN", "ASSET_OWNER", "SME_VENDOR"] = "ASSET_OWNER"
    organization: str | None = Field(default=None, max_length=120)
    team: str | None = Field(default=None, max_length=120)


class LoginPayload(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


@router.post("/register", status_code=201, summary="Register a basic Aegis user")
def register(
    payload: RegisterPayload,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, object]:
    # The first account is an explicit local ADMIN bootstrap. After that,
    # all account creation is an administrator operation, preventing public
    # role selection from becoming a privilege-escalation path.
    count = auth_service.user_count()
    if count == 0 and payload.role != "ADMIN":
        raise HTTPException(status_code=422, detail="the first account must use the ADMIN role")
    if count > 0:
        user = auth_service.current_user(credentials.credentials) if credentials else None
        if user is None:
            raise HTTPException(status_code=401, detail="administrator authentication required")
        if user["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="administrator role required")
    try:
        return auth_service.register(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=409 if "already registered" in str(exc) else 422, detail=str(exc)) from exc


@router.post("/login", summary="Authenticate and issue a revocable bearer token")
def login(payload: LoginPayload) -> dict[str, object]:
    try:
        return auth_service.login(payload.email, payload.password)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout", summary="Revoke the current bearer token")
def logout(credentials: HTTPAuthorizationCredentials = Depends(token_credentials)) -> dict[str, object]:
    if not auth_service.logout(credentials.credentials):
        raise HTTPException(status_code=401, detail="session is already invalid")
    return {"logged_out": True}


@router.get("/me", summary="Get the current authenticated user")
def me(user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    return user


@router.get("/users", summary="List assignable users")
def users(_: dict[str, object] = Depends(admin_user)) -> dict[str, object]:
    values = auth_service.list_users()
    return {"count": len(values), "users": values}
