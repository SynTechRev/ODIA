"""Dashboard summary route (v2.7.6 X1).

Aggregates persisted Document/Analysis/Anomaly rows for the Dashboard
home's Analysis Summary card. Pre-X1, the card read from a Zustand
store that only the legacy paste-text UploadPanel ever wrote to —
production audits go through `/api/v1/audit/run` and never populated
it, so the card was structurally guaranteed to show "No analyses yet".

Endpoint
--------
    GET /api/v1/dashboard/summary
        Returns headline counts + severity distribution + last-audit
        timestamp. All values are point-in-time aggregates over the
        persisted rows; the card polls this on mount.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]


def register_dashboard_routes(app: Any) -> None:
    """Attach dashboard-summary routes to a FastAPI app."""
    if not _FASTAPI_AVAILABLE:
        logger.warning(
            "FastAPI not installed — dashboard routes will not be registered."
        )
        return

    router = APIRouter(tags=["dashboard"])

    @router.get("/api/v1/dashboard/summary")
    async def dashboard_summary() -> dict[str, Any]:
        """Aggregate persisted analyses for the Dashboard home card.

        Response shape (stable contract for AnalysisSummaryCard):
            {
              "available": bool,
              "analyses": int,           # count of Analysis rows
              "documents": int,          # count of Document rows
              "findings": int,           # count of Anomaly rows
              "by_severity": {           # always present, all four keys
                  "critical": int,
                  "high": int,
                  "medium": int,
                  "low": int,
              },
              "avg_severity_score": float,   # mean of Analysis.severity_score
              "last_audit_at": str | None,   # ISO-8601 of newest analysis
            }

        Failing open: when the DB layer is unavailable we return
        ``available=false`` with zeroed counters so the UI can render
        a clean degraded state rather than crash. The card surfaces
        the ``available`` flag as a "backend offline" pill.
        """
        empty = {
            "available": False,
            "analyses": 0,
            "documents": 0,
            "findings": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "avg_severity_score": 0.0,
            "last_audit_at": None,
        }

        try:
            from sqlalchemy import func

            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError as exc:
            logger.warning("dashboard.summary: DB layer unavailable (%s)", exc)
            return empty

        try:
            with get_db() as session:
                analyses = (
                    session.query(func.count(db_models.Analysis.id)).scalar() or 0
                )
                documents = (
                    session.query(func.count(db_models.Document.id)).scalar() or 0
                )
                findings = session.query(func.count(db_models.Anomaly.id)).scalar() or 0

                severity_rows = (
                    session.query(
                        db_models.Anomaly.severity,
                        func.count(db_models.Anomaly.id),
                    )
                    .group_by(db_models.Anomaly.severity)
                    .all()
                )
                by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                for sev, count in severity_rows:
                    key = (sev or "").lower()
                    if key in by_sev:
                        by_sev[key] = int(count)

                avg = (
                    session.query(func.avg(db_models.Analysis.severity_score)).scalar()
                    or 0.0
                )

                last = (
                    session.query(db_models.Analysis.analysis_timestamp)
                    .order_by(db_models.Analysis.analysis_timestamp.desc())
                    .limit(1)
                    .scalar()
                )
                last_iso = last.isoformat() if last else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("dashboard.summary: query failed (%s)", exc)
            return empty

        return {
            "available": True,
            "analyses": int(analyses),
            "documents": int(documents),
            "findings": int(findings),
            "by_severity": by_sev,
            "avg_severity_score": float(avg),
            "last_audit_at": last_iso,
        }

    @router.post("/api/v1/dashboard/seed-jurisdictions")
    async def seed_jurisdictions(force: bool = False) -> dict[str, Any]:
        """Copy bundled example jurisdictions into the user-writable dir
        (v2.7.6 X2).

        On a fresh desktop install ``$ODIA_JURISDICTIONS_DIR`` is unset,
        the user-writable seed dir is empty, and the only jurisdictions
        available are the read-only bundled examples. Calling this
        endpoint copies them out so the user can edit + add to them
        without rebuilding the installer.

        Idempotent: skips subdirectories that already exist in the
        target unless ``force=True`` (in which case existing copies are
        overwritten — used for "reset to defaults" UX, not exposed in
        the UI button).
        """
        import shutil

        from oraculus_di_auditor.config.jurisdiction_loader import (
            bundled_multi_jurisdiction_root,
            user_multi_jurisdiction_root,
        )

        bundled = bundled_multi_jurisdiction_root()
        if bundled is None or not bundled.exists():
            return {
                "status": "no_bundle",
                "message": (
                    "No bundled examples found. This is unexpected on a "
                    "desktop install — try reinstalling."
                ),
                "copied": [],
                "skipped": [],
                "target": None,
            }

        target = user_multi_jurisdiction_root()
        target.mkdir(parents=True, exist_ok=True)

        copied: list[str] = []
        skipped: list[str] = []
        for child in sorted(bundled.iterdir()):
            if not child.is_dir():
                continue
            dst = target / child.name
            if dst.exists() and not force:
                skipped.append(child.name)
                continue
            if dst.exists() and force:
                shutil.rmtree(dst)
            shutil.copytree(child, dst)
            copied.append(child.name)

        return {
            "status": "ok",
            "copied": copied,
            "skipped": skipped,
            "target": str(target),
            "force": force,
        }

    app.include_router(router)
    logger.info("Dashboard summary route registered at /api/v1/dashboard/summary")


__all__ = ["register_dashboard_routes"]
