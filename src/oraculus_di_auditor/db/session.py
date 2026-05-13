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

    # v2.9.3 Track A.2 — additive idempotent column migration. SQLAlchemy's
    # create_all() skips tables that already exist, which means new
    # columns added to existing models never reach a previously-created
    # database. Running ALTER TABLE ADD COLUMN here keeps long-lived
    # SQLite installs in sync with the model. Postgres + other backends
    # fall through silently — production installs use proper migrations
    # there; only the single-user SQLite path needs this autoamigration.
    if url.startswith("sqlite"):
        _migrate_seen_hash_extraction_columns()

    # v3.0 — Sweep zombie EXECUTING mesh-job rows.
    # MeshExecutionJob rows are written by upload._execute_audit_job to
    # track audit progress. If the backend process dies mid-audit (the
    # user closes the desktop app, uvicorn crashes, SIGTERM during a
    # reload, etc.) the row stays at status="executing" forever — the
    # transition to "completed" / "failed" lives inside the audit
    # thread, which is gone. On the next startup we reconcile: any
    # "executing" row older than the threshold is marked "failed" with
    # a generic message so the Orchestrator timeline shows accurate
    # state instead of permanent zombies.
    _reconcile_stale_mesh_jobs()


def _migrate_seen_hash_extraction_columns() -> None:
    """Add `text_extraction_method` and `text_char_count` to seen_hashes if absent.

    Idempotent and SQLite-only. Uses ``PRAGMA table_info`` to discover
    existing columns, then issues ``ALTER TABLE`` for the missing ones.
    Failures are logged but never raised so DB introspection trouble
    can't block startup.
    """
    if _engine is None:
        return
    try:
        from sqlalchemy import text as _sql_text

        with _engine.begin() as conn:
            cols_result = conn.execute(_sql_text("PRAGMA table_info('seen_hashes')"))
            existing = {row[1] for row in cols_result}  # row[1] = column name
            if not existing:
                # Table doesn't exist yet — create_all handled (or skipped)
                # it; nothing to migrate.
                return
            if "text_extraction_method" not in existing:
                conn.execute(
                    _sql_text(
                        "ALTER TABLE seen_hashes ADD COLUMN "
                        "text_extraction_method VARCHAR(32)"
                    )
                )
            if "text_char_count" not in existing:
                conn.execute(
                    _sql_text(
                        "ALTER TABLE seen_hashes ADD COLUMN " "text_char_count INTEGER"
                    )
                )
    except Exception:  # noqa: BLE001 — schema migration is advisory
        import logging

        logging.getLogger(__name__).warning(
            "seen_hashes column migration skipped (likely fresh DB or "
            "non-SQLite backend)",
            exc_info=True,
        )


def _reconcile_stale_mesh_jobs() -> None:
    """Mark zombie EXECUTING mesh-job rows as failed at startup (v3.0).

    Backend restarts orphan any audit thread that was running at the
    time of shutdown — the in-process state machine that would have
    transitioned the row from ``executing`` to ``completed`` no longer
    exists. Sweeping at startup keeps the Orchestrator's "Recent Mesh
    Jobs" panel honest.

    Conservative threshold: anything claiming to be still executing
    when the process boots is clearly orphaned (a real audit running
    at startup is impossible — the process wasn't here yet). No time
    window needed; this is a clean reconciliation point.

    Failures are logged but never raised — startup must not depend on
    DB introspection succeeding. If the MeshExecutionJob table doesn't
    exist yet (fresh install with old model snapshot), the query
    raises and we silently skip.
    """
    if _SessionFactory is None:
        return
    try:
        from datetime import UTC, datetime

        from .models import MeshExecutionJob

        session = _SessionFactory()
        try:
            stale = (
                session.query(MeshExecutionJob)
                .filter(MeshExecutionJob.status == "executing")
                .all()
            )
            if not stale:
                return
            import json
            import logging

            now = datetime.now(UTC)
            for row in stale:
                row.status = "failed"
                row.completed_at = now
                try:
                    meta = json.loads(row.metadata_json or "{}")
                except Exception:
                    meta = {}
                meta["reconciliation"] = (
                    "marked failed at startup — process exited mid-audit"
                )
                row.metadata_json = json.dumps(meta)
            session.commit()
            logging.getLogger(__name__).info(
                "Reconciled %d zombie mesh-job row(s) to status=failed",
                len(stale),
            )
        finally:
            session.close()
    except Exception:  # noqa: BLE001 — reconciliation is advisory
        import logging

        logging.getLogger(__name__).warning(
            "Mesh-job reconciliation skipped (table may not exist yet)",
            exc_info=False,
        )


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
