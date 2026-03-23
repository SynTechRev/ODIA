"""SQLAlchemy ORM models for authentication."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase


class _Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    admin = "admin"
    auditor = "auditor"
    viewer = "viewer"


class User(_Base):
    """Application user."""

    __tablename__ = "auth_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(Text, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.auditor)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


class Session(_Base):
    """Authentication session (JWT token tracking for invalidation)."""

    __tablename__ = "auth_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    token_jti = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Session user={self.user_id} active={self.is_active}>"
