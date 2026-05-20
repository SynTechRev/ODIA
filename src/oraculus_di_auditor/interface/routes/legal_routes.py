"""FastAPI routes for the legal-corpus subsystem (v3.3.0).

Exposes:
  GET /api/v1/legal/status   — installed corpora + per-corpus stats

The status endpoint is the operator-visible signal that the USC
submodule loaded correctly and that future resolve() calls will hit
real text. n8n workflows + the dashboard 'Legal corpus' card consume
this same payload.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_legal_routes(app: Any) -> None:
    """Register legal-corpus endpoints on *app*.

    Safe to call when FastAPI or the resolver are unavailable —
    silently does nothing (matches the pattern used by every other
    register_*_routes function in this package).
    """
    try:
        from fastapi import APIRouter, HTTPException
    except ImportError:
        return

    router = APIRouter(tags=["legal"])

    @router.get("/api/v1/legal/status")
    async def legal_status() -> dict[str, Any]:
        """Report on installed legal corpora and their state.

        Returns:
            {
              "status": "ok",
              "corpora": {
                "us-code": {"titles_indexed": 53, "sections_indexed": 52586, ...}
              }
            }
        """
        try:
            from oraculus_di_auditor.legal.legal_resolver import get_resolver

            resolver = get_resolver()
            return {"status": "ok", "corpora": resolver.statistics()}
        except Exception as exc:  # noqa: BLE001
            # Resolver should be the soft-failure path, not a 500.
            logger.warning("legal_status: %s", exc)
            raise HTTPException(
                status_code=503, detail=f"legal resolver unavailable: {exc}"
            ) from exc

    app.include_router(router)
    logger.info("Legal routes registered (/api/v1/legal/*)")
