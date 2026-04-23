"""CPRA (California Public Records Act) deadline-watcher routes.

v2.7.1 Track C/C3. Exposes the server side of n8n WF-005 — a CRON
workflow that wakes every morning, asks the backend "which CPRA
requests are coming due in the next {window}", and fans the list out
to Gmail / Slack / Drive sinks per operator preference.

Endpoints
---------
    GET    /api/v1/cpra/deadlines-within/{window}
        List CPRA requests whose statutory_deadline falls within the
        given look-ahead window. `window` is one of: 72h, 7d, 30d.
        Returns `open` and `extended` status rows only (not responded,
        withdrawn, or already-overdue — those get their own queries).

    GET    /api/v1/cpra/requests
        Paginated list of CPRA requests filtered by status +
        jurisdiction_id. For the operator UI, not n8n.

    POST   /api/v1/cpra/requests
        Create a new tracked CPRA request. Body:
            jurisdiction_id, requested_at (ISO, defaults to now),
            statutory_deadline (ISO, required — 10 cal days per
            Gov Code § 7922.535 is the common default but the caller
            computes it), status (defaults to "open"), description.

    PATCH  /api/v1/cpra/requests/{id}
        Update status / deadline. Used when an agency invokes the
        § 7922.535(b) 14-day extension clause.

The DB layer uses db.models.CPRARequest. Unlike the webhook routes,
the CPRA endpoints are NOT token-gated — they're called from the
trusted LAN (n8n on the same docker network) and from the frontend.
Guard with network policy, not a shared secret.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# FastAPI imports at module scope — see webhook.py for the `from __future__
# import annotations` rationale. Same story: lazy string annotations
# resolved against module globals at route-registration time.
try:
    from fastapi import APIRouter, HTTPException, Query

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore
    HTTPException = None  # type: ignore
    Query = None  # type: ignore


# Valid window tokens recognised by /deadlines-within/{window}. Keep this
# tight — n8n's workflow config is the source of truth for which windows
# operators actually run, and widening this arbitrarily invites
# unbounded query ranges.
_WINDOW_MAP: dict[str, timedelta] = {
    "72h": timedelta(hours=72),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

# Statuses that count as "still ours to track" for the deadline watcher.
# 'responded', 'withdrawn', and 'overdue' are terminal or need separate
# escalation paths.
_WATCHABLE_STATUSES = frozenset({"open", "extended"})


def _parse_iso_utc(raw: Any) -> datetime | None:
    """Parse an ISO-8601 string as UTC. Return None if falsy or invalid."""
    if not raw:
        return None
    if isinstance(raw, datetime):
        # Normalise to UTC — the DB column is timezone-naive but stores UTC.
        if raw.tzinfo is None:
            return raw.replace(tzinfo=UTC)
        return raw.astimezone(UTC)
    try:
        # Python 3.11+ handles "Z" suffix natively via fromisoformat.
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Serialise a CPRARequest ORM row to a JSON-friendly dict."""
    return {
        "id": row.id,
        "jurisdiction_id": row.jurisdiction_id,
        "requested_at": row.requested_at.isoformat() if row.requested_at else None,
        "statutory_deadline": (
            row.statutory_deadline.isoformat() if row.statutory_deadline else None
        ),
        "status": row.status,
        "description": row.description,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def register_cpra_routes(app: Any) -> None:
    """Attach CPRA deadline-watcher routes to a FastAPI app.

    Mirrors register_*_routes in the other route modules. Safe to call
    when FastAPI is missing (logs + returns) or when the DB models aren't
    available (per-route checks bail with 503).
    """
    if not _FASTAPI_AVAILABLE:
        logger.warning(
            "FastAPI not installed — CPRA routes will not be registered."
        )
        return

    router = APIRouter(tags=["cpra"])

    # Lazy-import DB models at route-call time so this module stays
    # importable when SQLAlchemy is absent; the handler 503s gracefully
    # rather than crashing the whole app factory.
    def _db_layer():
        try:
            from oraculus_di_auditor.db.session import get_db
            from oraculus_di_auditor.db import models as db_models
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"CPRA DB layer unavailable: {exc}",
            ) from exc
        if not hasattr(db_models, "CPRARequest"):
            raise HTTPException(
                status_code=503,
                detail="CPRARequest model not available — run init_db()",
            )
        return get_db, db_models

    # ---- Deadline watcher -------------------------------------------------
    @router.get("/api/v1/cpra/deadlines-within/{window}")
    async def deadlines_within(
        window: str,
        jurisdiction_id: str | None = Query(default=None),
    ) -> dict[str, Any]:
        """Return CPRA requests with statutory_deadline between now
        and now + window. n8n WF-005 CRON trigger consumes this."""
        delta = _WINDOW_MAP.get(window)
        if delta is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"invalid window '{window}' — must be one of "
                    f"{sorted(_WINDOW_MAP.keys())}"
                ),
            )

        get_db, db_models = _db_layer()
        now = datetime.now(UTC).replace(tzinfo=None)
        cutoff = now + delta

        try:
            with get_db() as session:
                query = session.query(db_models.CPRARequest).filter(
                    db_models.CPRARequest.status.in_(_WATCHABLE_STATUSES),
                    db_models.CPRARequest.statutory_deadline >= now,
                    db_models.CPRARequest.statutory_deadline <= cutoff,
                )
                if jurisdiction_id:
                    query = query.filter_by(jurisdiction_id=jurisdiction_id)
                rows = query.order_by(
                    db_models.CPRARequest.statutory_deadline.asc()
                ).all()
                items = [_row_to_dict(r) for r in rows]
        except Exception as exc:  # noqa: BLE001
            logger.exception("CPRA deadlines-within query failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return {
            "window": window,
            "now": now.isoformat() + "Z",
            "cutoff": cutoff.isoformat() + "Z",
            "count": len(items),
            "items": items,
        }

    # ---- Paginated list --------------------------------------------------
    @router.get("/api/v1/cpra/requests")
    async def list_requests(
        jurisdiction_id: str | None = Query(default=None),
        status: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        get_db, db_models = _db_layer()
        try:
            with get_db() as session:
                query = session.query(db_models.CPRARequest)
                if jurisdiction_id:
                    query = query.filter_by(jurisdiction_id=jurisdiction_id)
                if status:
                    query = query.filter_by(status=status)
                total = query.count()
                rows = (
                    query.order_by(db_models.CPRARequest.statutory_deadline.asc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )
                items = [_row_to_dict(r) for r in rows]
        except Exception as exc:  # noqa: BLE001
            logger.exception("CPRA list query failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items,
        }

    # ---- Create ----------------------------------------------------------
    @router.post("/api/v1/cpra/requests")
    async def create_request(payload: dict[str, Any]) -> dict[str, Any]:
        jurisdiction_id = payload.get("jurisdiction_id")
        deadline_raw = payload.get("statutory_deadline")
        if not jurisdiction_id:
            raise HTTPException(
                status_code=400, detail="jurisdiction_id is required"
            )
        deadline = _parse_iso_utc(deadline_raw)
        if deadline is None:
            raise HTTPException(
                status_code=400,
                detail="statutory_deadline is required (ISO-8601 timestamp)",
            )

        requested = _parse_iso_utc(payload.get("requested_at")) or datetime.now(UTC)
        status = payload.get("status") or "open"
        description = payload.get("description")

        get_db, db_models = _db_layer()
        try:
            with get_db() as session:
                row = db_models.CPRARequest(
                    jurisdiction_id=jurisdiction_id,
                    requested_at=requested.replace(tzinfo=None),
                    statutory_deadline=deadline.replace(tzinfo=None),
                    status=status,
                    description=description,
                )
                session.add(row)
                session.flush()
                session.refresh(row)
                out = _row_to_dict(row)
        except Exception as exc:  # noqa: BLE001
            logger.exception("CPRA create failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return out

    # ---- Update ----------------------------------------------------------
    @router.patch("/api/v1/cpra/requests/{request_id}")
    async def update_request(
        request_id: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        get_db, db_models = _db_layer()
        try:
            with get_db() as session:
                row = session.get(db_models.CPRARequest, request_id)
                if row is None:
                    raise HTTPException(status_code=404, detail="request not found")
                if "status" in payload and payload["status"]:
                    row.status = payload["status"]
                if "description" in payload:
                    row.description = payload["description"]
                if "statutory_deadline" in payload:
                    new_deadline = _parse_iso_utc(payload["statutory_deadline"])
                    if new_deadline is None:
                        raise HTTPException(
                            status_code=400,
                            detail="statutory_deadline must be ISO-8601",
                        )
                    row.statutory_deadline = new_deadline.replace(tzinfo=None)
                session.flush()
                session.refresh(row)
                out = _row_to_dict(row)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("CPRA update failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return out

    app.include_router(router)
    logger.info("CPRA deadline-watcher routes registered at /api/v1/cpra/*")
