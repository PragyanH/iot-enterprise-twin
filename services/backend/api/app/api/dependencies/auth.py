from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.runtime import auth_service


bearer = HTTPBearer(auto_error=False)


def token_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> HTTPAuthorizationCredentials:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="bearer authentication required")
    return credentials


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(token_credentials),
) -> dict[str, object]:
    user = auth_service.current_user(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid, expired, revoked, or inactive token")
    return user


def admin_user(user: dict[str, object] = Depends(current_user)) -> dict[str, object]:
    if user["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="administrator role required")
    return user
