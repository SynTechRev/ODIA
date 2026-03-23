"""FastAPI routes for workspace management.

Endpoints:
  POST /api/v1/workspaces              Create workspace
  GET  /api/v1/workspaces              List user's workspaces
  GET  /api/v1/workspaces/{id}         Get workspace details
  POST /api/v1/workspaces/{id}/members Add member
  GET  /api/v1/workspaces/{id}/members List members
  GET  /api/v1/workspaces/{id}/log     Get audit log
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, Depends, HTTPException
    from fastapi.security import OAuth2PasswordBearer
    from pydantic import BaseModel

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment, misc]


class _CreateWorkspaceRequest(BaseModel):  # type: ignore[misc]
    name: str
    jurisdiction: str | None = None


class _AddMemberRequest(BaseModel):  # type: ignore[misc]
    user_id: str
    role: str = "auditor"


# Singleton service
_workspace_service: Any = None


def _get_workspace_service() -> Any:
    global _workspace_service
    if _workspace_service is None:
        from oraculus_di_auditor.workspace.workspace_service import WorkspaceService

        _workspace_service = WorkspaceService()
    return _workspace_service


def register_workspace_routes(app: Any) -> None:
    if not _FASTAPI_AVAILABLE:
        return

    from oraculus_di_auditor.auth.auth_middleware import get_current_user

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
    router = APIRouter(tags=["workspaces"])

    def _current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
        return get_current_user(token)

    @router.post("/api/v1/workspaces")
    async def create_workspace(
        request: _CreateWorkspaceRequest,
        user: dict = Depends(_current_user),
    ) -> dict[str, Any]:
        """Create a new workspace. Creator is added as admin member."""
        service = _get_workspace_service()
        ws = service.create_workspace(
            name=request.name,
            created_by=user["id"],
            jurisdiction=request.jurisdiction,
        )
        service.log_action(
            ws["id"], user["id"], "workspace.create",
            detail=f"Created workspace '{request.name}'",
            user_email=user.get("email"),
        )
        return ws

    @router.get("/api/v1/workspaces")
    async def list_workspaces(user: dict = Depends(_current_user)) -> dict[str, Any]:
        """List all workspaces the current user is a member of."""
        service = _get_workspace_service()
        workspaces = service.list_workspaces(user["id"])
        return {"workspaces": workspaces, "count": len(workspaces)}

    @router.get("/api/v1/workspaces/{workspace_id}")
    async def get_workspace(
        workspace_id: str, user: dict = Depends(_current_user)
    ) -> dict[str, Any]:
        service = _get_workspace_service()
        ws = service.get_workspace(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")
        return ws

    @router.post("/api/v1/workspaces/{workspace_id}/members")
    async def add_member(
        workspace_id: str,
        request: _AddMemberRequest,
        user: dict = Depends(_current_user),
    ) -> dict[str, Any]:
        service = _get_workspace_service()
        ws = service.get_workspace(workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found")
        member = service.add_member(workspace_id, request.user_id, request.role)
        service.log_action(
            workspace_id, user["id"], "member.add",
            detail=f"Added user {request.user_id} as {request.role}",
            user_email=user.get("email"),
        )
        return member

    @router.get("/api/v1/workspaces/{workspace_id}/members")
    async def list_members(
        workspace_id: str, user: dict = Depends(_current_user)
    ) -> dict[str, Any]:
        service = _get_workspace_service()
        members = service.get_members(workspace_id)
        return {"members": members, "count": len(members)}

    @router.get("/api/v1/workspaces/{workspace_id}/log")
    async def get_audit_log(
        workspace_id: str,
        limit: int = 100,
        user: dict = Depends(_current_user),
    ) -> dict[str, Any]:
        """Get chronological audit log for a workspace."""
        service = _get_workspace_service()
        log = service.get_audit_log(workspace_id, limit=limit)
        return {"log": log, "count": len(log), "workspace_id": workspace_id}

    app.include_router(router)
