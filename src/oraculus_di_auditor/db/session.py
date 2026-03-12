"""SQLAlchemy session management for Oraculus-DI-Auditor.

Provides database connection and session factory.
Uses SQLite by default, configurable via DATABASE_URL environment variable.

Example:
    export DATABASE_URL="sqlite:///./oraculus.db"
    export DATABASE_URL="postgresql://user:pass@localhost/oraculus"
"""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    create_engine = None  # type: ignore
    sessionmaker = None  # type: ignore
    Session = None  # type: ignore

# Default to SQLite in the project root
DEFAULT_DATABASE_URL = "sqlite:///./oraculus_audit.db"

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Global engine and session factory
_engine = None
_SessionFactory = None


def init_db(database_url: str | None = None) -> None:
    """Initialize database connection and create tables.

    Args:
        database_url: Optional database URL, defaults to DATABASE_URL env var
                      or DEFAULT_DATABASE_URL

    Raises:
        ImportError: If SQLAlchemy is not installed
    """
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError(
            "SQLAlchemy is required for database functionality. "
            "Install with: pip install SQLAlchemy"
        )

    global _engine, _SessionFactory

    from .models import Base

    url = database_url or DATABASE_URL
    _engine = create_engine(
        url,
        # SQLite-specific settings for better concurrency
        connect_args=({"check_same_thread": False} if url.startswith("sqlite") else {}),
    )
    _SessionFactory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

    # Create all tables
    Base.metadata.create_all(bind=_engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session context manager.

    Yields:
        SQLAlchemy Session instance

    Example:
        with get_db() as db:
            document = db.query(Document).filter_by(document_id="doc-1").first()

    Raises:
        RuntimeError: If database has not been initialized
    """
    if _SessionFactory is None:
        raise RuntimeError(
            "Database not initialized. Call init_db() first or set DATABASE_URL."
        )

    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_engine():
    """Get the SQLAlchemy engine instance.

    Returns:
        SQLAlchemy Engine or None if not initialized
    """
    return _engine


__all__ = ["init_db", "get_db", "get_engine", "DATABASE_URL"]
