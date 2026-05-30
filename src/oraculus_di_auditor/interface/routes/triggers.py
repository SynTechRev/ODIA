"""Manual-trigger routes for the Automation page (v2.7.4 W1).

The Automation page's "Manual Triggers" panel previously POSTed to
``/api/v1/automation/workflows/{id}/run`` which proxies to n8n. With
n8n offline (the default for fresh installs without the optional
docker-compose stack) those buttons silently failed. These routes
expose the same functionality through ODIA-native endpoints — no
n8n, no ``ODIA_WEBHOOK_TOKEN`` — so the buttons work out of the box.

Endpoints
---------
    GET  /api/v1/triggers/cpra-deadlines/{window}
        Thin re-export of the existing ``/api/v1/cpra/deadlines-
        within/{window}`` route. Provided for symmetry so the UI can
        treat all three triggers uniformly.

    POST /api/v1/triggers/raia-synthesize-all
        Discovers jurisdictions via
        ``config.jurisdiction_loader.discover_jurisdictions()`` and
        runs ``RAIAService.synthesize()`` across all of them. Returns
        the full ``RAIAResult`` plus rendered markdown. Bypasses the
        webhook token requirement on the equivalent
        ``/api/v1/webhook/synthesize`` endpoint.

    POST /api/v1/triggers/provenance-chain-export
        Stub that returns 501 with a helpful explanation — the
        Provenance Chain Export (n8n WF-014) joins ODIA findings to
        n8n execution-history rows and requires the n8n container
        to be online. This endpoint exists so the UI gets a clean
        explanatory response rather than a generic 404.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore
    HTTPException = None  # type: ignore


_VALID_CPRA_WINDOWS = ("72h", "7d", "30d")


def register_trigger_routes(app: Any) -> None:
    """Attach manual-trigger routes to a FastAPI app."""
    if not _FASTAPI_AVAILABLE:
        logger.warning("FastAPI not installed — trigger routes will not be registered.")
        return

    router = APIRouter(tags=["triggers"])

    # ---- CPRA deadlines (re-export) ---------------------------------------
    @router.get("/api/v1/triggers/cpra-deadlines/{window}")
    async def trigger_cpra_deadlines(window: str) -> dict[str, Any]:
        """Returns CPRA requests with a deadline within ``window``.

        Window values: ``72h`` / ``7d`` / ``30d`` (matches the upstream
        CPRA route's vocabulary). Re-exported under ``/triggers/`` so
        the Automation UI's manual-trigger panel can call all three
        triggers via a uniform URL prefix.
        """
        if window not in _VALID_CPRA_WINDOWS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"invalid window '{window}'; "
                    f"must be one of {list(_VALID_CPRA_WINDOWS)}"
                ),
            )
        try:
            from datetime import UTC, datetime, timedelta

            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"DB layer unavailable: {exc}",
            ) from exc

        # Window → timedelta
        if window == "72h":
            delta = timedelta(hours=72)
        elif window == "7d":
            delta = timedelta(days=7)
        else:  # 30d
            delta = timedelta(days=30)

        now = datetime.now(UTC).replace(tzinfo=None)
        cutoff = now + delta
        watchable = ("open", "extended")
        try:
            with get_db() as session:
                rows = (
                    session.query(db_models.CPRARequest)
                    .filter(
                        db_models.CPRARequest.statutory_deadline >= now,
                        db_models.CPRARequest.statutory_deadline <= cutoff,
                        db_models.CPRARequest.status.in_(watchable),
                    )
                    .order_by(db_models.CPRARequest.statutory_deadline.asc())
                    .all()
                )
                items = [
                    {
                        "id": r.id,
                        "jurisdiction_id": r.jurisdiction_id,
                        "statutory_deadline": (
                            r.statutory_deadline.isoformat()
                            if r.statutory_deadline
                            else None
                        ),
                        "status": r.status,
                        "description": r.description,
                    }
                    for r in rows
                ]
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=503,
                detail=f"CPRA query failed: {exc}",
            ) from exc
        return {
            "window": window,
            "count": len(items),
            "items": items,
        }

    # ---- RAIA synthesis (across all discovered jurisdictions) -------------
    @router.post("/api/v1/triggers/raia-synthesize-all")
    async def trigger_raia_synthesize_all(
        include_tier3: bool = False,
        render_markdown: bool = True,
    ) -> dict[str, Any]:
        """Discover every jurisdiction and run RAIAService across them.

        Bypasses the webhook token gate on /webhook/synthesize so the
        Automation UI's "Run RAIA Synthesis" button works on a desktop
        install that hasn't configured ``ODIA_WEBHOOK_TOKEN``.
        """
        try:
            from oraculus_di_auditor.config.jurisdiction_loader import (
                discover_jurisdictions,
            )
            from oraculus_di_auditor.raia import (
                RAIAService,
                render_markdown_template,
            )
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"RAIA service unavailable: {exc}",
            ) from exc

        # Prefer DB jurisdictions (documents table) over file-system discovery
        # so the Synthesis button works for upload-audited and webhook-ingested
        # documents even when config/multi_jurisdiction/ has only example stubs.
        jurisdictions: list[str] = []
        try:
            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db

            with get_db() as session:
                rows = (
                    session.query(db_models.Document.jurisdiction)
                    .filter(db_models.Document.jurisdiction.isnot(None))
                    .distinct()
                    .all()
                )
                jurisdictions = [r[0] for r in rows if r[0]]
        except Exception:  # noqa: BLE001
            pass

        if not jurisdictions:
            jurisdictions = list(discover_jurisdictions().keys())

        if not jurisdictions:
            return {
                "status": "no_jurisdictions",
                "message": (
                    "No jurisdictions found in the database or config/multi_jurisdiction/. "
                    "Run at least one audit with a jurisdiction set before running synthesis."
                ),
                "result": None,
                "markdown": None,
            }

        try:
            svc = RAIAService()
            result = svc.synthesize(jurisdictions, include_tier3=include_tier3)
        except Exception as exc:  # noqa: BLE001
            logger.exception("triggers.raia-synthesize-all failed")
            raise HTTPException(
                status_code=500,
                detail=f"RAIA synthesis failed: {exc}",
            ) from exc

        markdown = render_markdown_template(result) if render_markdown else None
        return {
            "status": "ok",
            "jurisdictions": jurisdictions,
            "include_tier3": include_tier3,
            "result": result.to_dict(),
            "markdown": markdown,
        }

    # ---- Provenance Chain Export (stub) -----------------------------------
    @router.post("/api/v1/triggers/provenance-chain-export")
    async def trigger_provenance_chain_export() -> dict[str, Any]:
        """Stub — Provenance Chain Export requires the n8n container.

        Provenance Chain Export (n8n WF-014) joins ODIA's
        ``WebhookAuditLog`` rows with n8n's ``executions`` history
        and emits a litigation-grade DOCX. The join half lives in n8n,
        so this trigger needs the container running. We return 501
        with a helpful message so the UI can render a clear error
        rather than a generic network failure.
        """
        raise HTTPException(
            status_code=501,
            detail=(
                "Provenance Chain Export requires the n8n container "
                "(workflow WF-014). Bring it up with: "
                "`docker compose -f docker-compose.yml -f "
                "docker-compose.n8n.yml up -d n8n`, then retry."
            ),
        )

    app.include_router(router)
    logger.info("Manual-trigger routes registered at /api/v1/triggers/*")


__all__ = ["register_trigger_routes"]
