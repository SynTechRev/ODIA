"""Field-verification routes (Flock / Axon / UAS deployment observations).

v2.7.1 Track C/C4. Operator-submitted confirmations that a surveillance
deployment does — or does not — exist where vendor contracts / press
releases say it should.

Endpoints
---------
    POST /api/v1/field/flock-observation
        Record a new field observation. Key signal on the payload is
        `exclusion_zone`: when True, the operator is asserting this
        device is inside a contractually-forbidden zone (park, school,
        exempted residential street, outside jurisdiction boundary).
        Rows with exclusion_zone=True get promoted into the MAS report's
        "Field-Verified Placement" section as evidence.

    GET  /api/v1/field/observations
        Paginated list for the operator UI. Filters by jurisdiction_id,
        verification_type, exclusion_zone.

    GET  /api/v1/field/exclusion-zones
        Shortcut — returns only the exclusion_zone=true rows, ordered
        newest-first. What the MAS generator consumes when rolling up
        a report.

Schema alignment
----------------
`verification_type` is a short enum: photo, pass_by, deflock_cross_ref.
The DeFlock cheatsheet (deflock.me) is the reference for the third
type — community-verified device listings. Photo = operator took a
photo with a landmark vantage. Pass_by = operator drove past and
confirmed visually without recording.

Like the CPRA routes, these are NOT token-gated. Field submissions
come from trusted operator devices on the LAN or over VPN; the
authentication mechanism is the workspace auth middleware, not a
shared secret.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException, Query

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore
    HTTPException = None  # type: ignore
    Query = None  # type: ignore


_VALID_VERIFICATION_TYPES = frozenset(
    {"photo", "pass_by", "deflock_cross_ref"}
)


def _parse_iso_utc(raw: Any) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _validate_coords(lat: Any, lng: Any) -> tuple[float, float]:
    """Coerce + validate latitude / longitude. Raise HTTPException on failure."""
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400, detail="lat and lng must be numbers"
        ) from exc
    if not (-90.0 <= lat_f <= 90.0):
        raise HTTPException(
            status_code=400, detail="lat must be in [-90, 90]"
        )
    if not (-180.0 <= lng_f <= 180.0):
        raise HTTPException(
            status_code=400, detail="lng must be in [-180, 180]"
        )
    return lat_f, lng_f


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "jurisdiction_id": row.jurisdiction_id,
        "observed_at": row.observed_at.isoformat() if row.observed_at else None,
        "lat": row.lat,
        "lng": row.lng,
        "verification_type": row.verification_type,
        "notes": row.notes,
        "exclusion_zone": row.exclusion_zone,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def register_field_routes(app: Any) -> None:
    """Attach field-observation routes to a FastAPI app."""
    if not _FASTAPI_AVAILABLE:
        logger.warning(
            "FastAPI not installed — field routes will not be registered."
        )
        return

    router = APIRouter(tags=["field"])

    def _db_layer():
        try:
            from oraculus_di_auditor.db.session import get_db
            from oraculus_di_auditor.db import models as db_models
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Field DB layer unavailable: {exc}",
            ) from exc
        if not hasattr(db_models, "FieldObservation"):
            raise HTTPException(
                status_code=503,
                detail="FieldObservation model not available — run init_db()",
            )
        return get_db, db_models

    # ---- Create ----------------------------------------------------------
    @router.post("/api/v1/field/flock-observation")
    async def create_observation(payload: dict[str, Any]) -> dict[str, Any]:
        jurisdiction_id = payload.get("jurisdiction_id")
        verification_type = payload.get("verification_type")
        if not jurisdiction_id:
            raise HTTPException(
                status_code=400, detail="jurisdiction_id is required"
            )
        if verification_type not in _VALID_VERIFICATION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"verification_type must be one of "
                    f"{sorted(_VALID_VERIFICATION_TYPES)}"
                ),
            )

        lat, lng = _validate_coords(payload.get("lat"), payload.get("lng"))
        observed = _parse_iso_utc(payload.get("observed_at")) or datetime.now(UTC)
        notes = payload.get("notes")
        exclusion = bool(payload.get("exclusion_zone", False))

        get_db, db_models = _db_layer()
        try:
            with get_db() as session:
                row = db_models.FieldObservation(
                    jurisdiction_id=jurisdiction_id,
                    observed_at=observed.replace(tzinfo=None),
                    lat=lat,
                    lng=lng,
                    verification_type=verification_type,
                    notes=notes,
                    exclusion_zone=exclusion,
                )
                session.add(row)
                session.flush()
                session.refresh(row)
                out = _row_to_dict(row)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Field observation create failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return out

    # ---- List ------------------------------------------------------------
    @router.get("/api/v1/field/observations")
    async def list_observations(
        jurisdiction_id: str | None = Query(default=None),
        verification_type: str | None = Query(default=None),
        exclusion_zone: bool | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        if verification_type is not None and verification_type not in _VALID_VERIFICATION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"verification_type must be one of "
                    f"{sorted(_VALID_VERIFICATION_TYPES)}"
                ),
            )
        get_db, db_models = _db_layer()
        try:
            with get_db() as session:
                query = session.query(db_models.FieldObservation)
                if jurisdiction_id:
                    query = query.filter_by(jurisdiction_id=jurisdiction_id)
                if verification_type:
                    query = query.filter_by(verification_type=verification_type)
                if exclusion_zone is not None:
                    query = query.filter_by(exclusion_zone=exclusion_zone)
                total = query.count()
                rows = (
                    query.order_by(db_models.FieldObservation.observed_at.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )
                items = [_row_to_dict(r) for r in rows]
        except Exception as exc:  # noqa: BLE001
            logger.exception("Field list query failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return {"total": total, "limit": limit, "offset": offset, "items": items}

    # ---- Exclusion-zone shortcut -----------------------------------------
    @router.get("/api/v1/field/exclusion-zones")
    async def list_exclusion_zones(
        jurisdiction_id: str | None = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        """Exclusion-zone rows only — what the MAS generator consumes."""
        get_db, db_models = _db_layer()
        try:
            with get_db() as session:
                query = session.query(db_models.FieldObservation).filter_by(
                    exclusion_zone=True
                )
                if jurisdiction_id:
                    query = query.filter_by(jurisdiction_id=jurisdiction_id)
                rows = (
                    query.order_by(db_models.FieldObservation.observed_at.desc())
                    .limit(limit)
                    .all()
                )
                items = [_row_to_dict(r) for r in rows]
        except Exception as exc:  # noqa: BLE001
            logger.exception("Field exclusion-zone query failed")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return {"count": len(items), "items": items}

    app.include_router(router)
    logger.info(
        "Field-verification routes registered at /api/v1/field/*"
    )
