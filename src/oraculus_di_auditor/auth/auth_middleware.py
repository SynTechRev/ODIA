"""FastAPI middleware and dependencies for optional JWT authentication.

Auth is enforced only when at least one user exists. In single-user mode
(no users registered), all requests are allowed as anonymous admin.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import OAuth2PasswordBearer

    _oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl="/api/v1/auth/login", auto_error=False
    )
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    _oauth2_scheme = None


# Singleton AuthService (no DB for now — uses in-memory store)
_auth_service: Any = None


def _get_auth_service() -> Any:
    global _auth_service
    if _auth_service is None:
        from .auth_service import AuthService

        _auth_service = AuthService()
    return _auth_service


ANONYMOUS_USER = {
    "id": "anonymous",
    "email": "anonymous@localhost",
    "name": "Anonymous",
    "role": "admin",
}


def get_current_user(token: str | None = None) -> dict[str, Any]:
    """FastAPI dependency: extract and validate JWT from Authorization header.

    In single-user mode (no users registered), returns ANONYMOUS_USER.
    Raises HTTP 401 if auth is enabled and token is invalid/missing.
    """
    service = _get_auth_service()

    if not service.auth_enabled():
        return ANONYMOUS_USER

    if not token:
        if _FASTAPI_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return ANONYMOUS_USER

    try:

        return service.verify_token(token)
    except Exception as exc:
        if _FASTAPI_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            )
        return ANONYMOUS_USER


def require_role(required_role: str):
    """Return a FastAPI dependency that enforces a minimum role level."""
    _role_order = {"viewer": 0, "auditor": 1, "admin": 2}

    def _check(user: dict = None) -> dict:
        if user is None:
            user = get_current_user()
        user_role = user.get("role", "viewer")
        if _role_order.get(user_role, 0) < _role_order.get(required_role, 99):
            if _FASTAPI_AVAILABLE:
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{required_role}' required, you have '{user_role}'",
                )
        return user

    return _check
