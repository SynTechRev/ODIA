"""SQLAlchemy ORM models for workspaces and audit logging."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase


class _Base(DeclarativeBase):
    pass


class Workspace(_Base):
    """A shared audit workspace for a team."""

    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    jurisdiction = Column(String(255), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"<Workspace {self.name!r} by={self.created_by}>"


class WorkspaceMember(_Base):
    """Association between a user and a workspace, with a role."""

    __tablename__ = "workspace_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    role = Column(String(64), nullable=False, default="auditor")
    added_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class AuditLog(_Base):
    """Immutable chain-of-custody log for all workspace actions.

    Every upload, analysis run, export, and config change in a workspace is
    recorded here with the acting user's identity and a timestamp. This
    provides the evidence integrity trail required for legal use.
    """

    __tablename__ = "workspace_audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False)
    user_email = Column(String(255), nullable=True)
    action = Column(String(255), nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action!r} by={self.user_id}>"
