"""Workspace management service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class WorkspaceService:
    """Manages workspaces, membership, and chain-of-custody audit logging.

    Parameters
    ----------
    db_session:
        SQLAlchemy session. Pass ``None`` for in-memory operation (testing).
    """

    def __init__(self, db_session: Any = None) -> None:
        self._db = db_session
        # In-memory fallback for single-user / test mode
        self._workspaces: dict[str, dict] = {}
        self._members: list[dict] = []
        self._log: list[dict] = []

    # ------------------------------------------------------------------
    # Workspaces
    # ------------------------------------------------------------------

    def create_workspace(
        self,
        name: str,
        created_by: str,
        jurisdiction: str | None = None,
    ) -> dict[str, Any]:
        """Create a new workspace and add the creator as admin.

        Returns the workspace dict.
        """
        ws_id = str(uuid.uuid4())
        ws = {
            "id": ws_id,
            "name": name,
            "jurisdiction": jurisdiction,
            "created_by": created_by,
            "created_at": datetime.now(UTC).isoformat(),
        }

        if self._db is not None:
            from .workspace_models import Workspace

            obj = Workspace(
                id=ws_id,
                name=name,
                jurisdiction=jurisdiction,
                created_by=created_by,
            )
            self._db.add(obj)
            self._db.commit()
        else:
            self._workspaces[ws_id] = ws

        # Auto-add creator as admin member
        self.add_member(ws_id, created_by, "admin")
        return ws

    def get_workspace(self, workspace_id: str) -> dict[str, Any] | None:
        """Return workspace dict or None."""
        if self._db is not None:
            from .workspace_models import Workspace

            obj = self._db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if obj:
                return {
                    "id": obj.id,
                    "name": obj.name,
                    "jurisdiction": obj.jurisdiction,
                    "created_by": obj.created_by,
                    "created_at": (
                        obj.created_at.isoformat() if obj.created_at else None
                    ),
                }
        return self._workspaces.get(workspace_id)

    def list_workspaces(self, user_id: str) -> list[dict[str, Any]]:
        """Return all workspaces the user is a member of."""
        member_ws_ids = {
            m["workspace_id"] for m in self._members if m["user_id"] == user_id
        }
        if self._db is not None:
            from .workspace_models import WorkspaceMember

            ids = [
                row.workspace_id
                for row in self._db.query(WorkspaceMember)
                .filter(WorkspaceMember.user_id == user_id)
                .all()
            ]
            result = []
            for ws_id in ids:
                ws = self.get_workspace(ws_id)
                if ws:
                    result.append(ws)
            return result
        return [
            self._workspaces[wid] for wid in member_ws_ids if wid in self._workspaces
        ]

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------

    def add_member(
        self, workspace_id: str, user_id: str, role: str = "auditor"
    ) -> dict[str, Any]:
        """Add a user to a workspace with the given role."""
        member_id = str(uuid.uuid4())
        member = {
            "id": member_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "role": role,
            "added_at": datetime.now(UTC).isoformat(),
        }

        if self._db is not None:
            from .workspace_models import WorkspaceMember

            obj = WorkspaceMember(
                id=member_id,
                workspace_id=workspace_id,
                user_id=user_id,
                role=role,
            )
            self._db.add(obj)
            self._db.commit()
        else:
            self._members.append(member)

        return member

    def get_members(self, workspace_id: str) -> list[dict[str, Any]]:
        """Return all members of a workspace."""
        if self._db is not None:
            from .workspace_models import WorkspaceMember

            return [
                {
                    "id": m.id,
                    "workspace_id": m.workspace_id,
                    "user_id": m.user_id,
                    "role": m.role,
                    "added_at": m.added_at.isoformat() if m.added_at else None,
                }
                for m in self._db.query(WorkspaceMember)
                .filter(WorkspaceMember.workspace_id == workspace_id)
                .all()
            ]
        return [m for m in self._members if m["workspace_id"] == workspace_id]

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def log_action(
        self,
        workspace_id: str,
        user_id: str,
        action: str,
        detail: str | None = None,
        user_email: str | None = None,
    ) -> dict[str, Any]:
        """Append an immutable log entry for a workspace action."""
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "user_email": user_email,
            "action": action,
            "detail": detail,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if self._db is not None:
            from .workspace_models import AuditLog

            obj = AuditLog(
                id=entry_id,
                workspace_id=workspace_id,
                user_id=user_id,
                user_email=user_email,
                action=action,
                detail=detail,
            )
            self._db.add(obj)
            self._db.commit()
        else:
            self._log.append(entry)

        return entry

    def get_audit_log(
        self, workspace_id: str, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Return chronological audit log for a workspace (most recent first)."""
        if self._db is not None:
            from .workspace_models import AuditLog

            rows = (
                self._db.query(AuditLog)
                .filter(AuditLog.workspace_id == workspace_id)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "workspace_id": r.workspace_id,
                    "user_id": r.user_id,
                    "user_email": r.user_email,
                    "action": r.action,
                    "detail": r.detail,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                }
                for r in rows
            ]
        entries = [e for e in self._log if e["workspace_id"] == workspace_id]
        return sorted(entries, key=lambda e: e["timestamp"], reverse=True)[:limit]
