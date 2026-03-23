"""FastAPI routes for user authentication.

Endpoints:
  POST /api/v1/auth/register    Register a new user
  POST /api/v1/auth/login       Login (returns JWT)
  POST /api/v1/auth/logout      Invalidate session
  GET  /api/v1/auth/me          Get current user info
  GET  /api/v1/auth/status      Whether auth is enabled
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, Depends, HTTPException
    from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
    from pydantic import BaseModel, EmailStr

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment, misc]


class _RegisterRequest(BaseModel):  # type: ignore[misc]
    email: str
    password: str
    name: str
    role: str = "auditor"


def register_auth_routes(app: Any) -> None:
    if not _FASTAPI_AVAILABLE:
        return

    from oraculus_di_auditor.auth.auth_middleware import (
        ANONYMOUS_USER,
        _get_auth_service,
    )
    from oraculus_di_auditor.auth.auth_service import AuthError

    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="/api/v1/auth/login", auto_error=False
    )
    router = APIRouter(tags=["auth"])

    @router.get("/api/v1/auth/status")
    async def auth_status() -> dict[str, Any]:
        """Return whether authentication is currently enforced."""
        service = _get_auth_service()
        return {
            "auth_enabled": service.auth_enabled(),
            "user_count": service.user_count(),
        }

    @router.post("/api/v1/auth/register")
    async def register(request: _RegisterRequest) -> dict[str, Any]:
        """Register a new user. First user becomes admin."""
        service = _get_auth_service()
        try:
            user = service.register(
                email=request.email,
                password=request.password,
                name=request.name,
                role=request.role,
            )
            return {"status": "registered", "user": user}
        except AuthError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/v1/auth/login")
    async def login(form: OAuth2PasswordRequestForm = Depends()) -> dict[str, Any]:
        """Login with email/password, returns JWT bearer token."""
        service = _get_auth_service()
        try:
            result = service.login(form.username, form.password)
            return {
                "access_token": result["token"],
                "token_type": result["token_type"],
                "expires_at": result["expires_at"],
                "user": result["user"],
            }
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @router.post("/api/v1/auth/logout")
    async def logout(token: str | None = Depends(oauth2_scheme)) -> dict[str, str]:
        """Invalidate the current session token."""
        if token:
            service = _get_auth_service()
            service.logout(token)
        return {"status": "logged_out"}

    @router.get("/api/v1/auth/me")
    async def me(token: str | None = Depends(oauth2_scheme)) -> dict[str, Any]:
        """Return current user info. Returns anonymous user if auth is disabled."""
        if token:
            service = _get_auth_service()
            try:
                return service.verify_token(token)
            except Exception:
                pass
        return ANONYMOUS_USER

    app.include_router(router)
