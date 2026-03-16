"""FastAPI routes for temporal contract evolution analysis.

Provides:
- POST /temporal/analyze        — build lineages, detect patterns, return timeline
- GET  /temporal/patterns       — list all supported pattern types with descriptions
- POST /temporal/lineage/{vendor} — get lineage for a specific vendor
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False
    BaseModel = object  # type: ignore[assignment,misc]
    Field = lambda *a, **kw: None  # type: ignore[assignment]  # noqa: E731

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class TemporalAnalyzeRequest(BaseModel):  # type: ignore[misc]
    """Request body for POST /temporal/analyze."""

    documents: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Documents to analyze (each may include vendor, date, amount, etc.)"
        ),
    )
    jurisdiction: str | None = Field(
        default=None, description="Jurisdiction name (optional metadata)"
    )


class VendorLineageRequest(BaseModel):  # type: ignore[misc]
    """Request body for POST /temporal/lineage/{vendor}."""

    documents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Documents to search for this vendor's lineage",
    )


# ---------------------------------------------------------------------------
# Pattern type registry
# ---------------------------------------------------------------------------

_PATTERN_TYPES = [
    {
        "pattern_type": "scope_creep",
        "description": (
            "Gradual scope expansion through successive amendments. "
            "Triggered when total growth exceeds 200% across 3+ amendments."
        ),
        "severity_range": "high–critical",
    },
    {
        "pattern_type": "vendor_lock_in",
        "description": (
            "Sustained sole-source procurement over 3+ years with no competitive "
            "bidding. Triggered when 3+ events span 3+ years with no "
            "competitive_bid authorization."
        ),
        "severity_range": "high–critical",
    },
    {
        "pattern_type": "capability_embedding",
        "description": (
            "New technology capabilities added inside existing contracts without "
            "separate authorization. Detected via technology keyword analysis."
        ),
        "severity_range": "high",
    },
    {
        "pattern_type": "authorization_erosion",
        "description": (
            "Declining authorization rigor over time — early events with council "
            "votes, later events on consent calendar or with no authorization."
        ),
        "severity_range": "high",
    },
    {
        "pattern_type": "payment_acceleration",
        "description": (
            "Payment amounts increasing year-over-year faster than expected. "
            "Triggered when average YoY growth exceeds 50% across 3+ events."
        ),
        "severity_range": "medium–critical",
    },
    {
        "pattern_type": "parallel_expansion",
        "description": (
            "Same vendor expanding across multiple simultaneous lineages, "
            "suggesting coordinated vendor strategy or contract splitting."
        ),
        "severity_range": "high",
    },
]


# ---------------------------------------------------------------------------
# Route factory
# ---------------------------------------------------------------------------


def register_temporal_routes(app: Any) -> None:
    """Register temporal analysis routes on the FastAPI app."""
    if not _FASTAPI_AVAILABLE:  # pragma: no cover
        logger.warning("FastAPI not available; temporal routes not registered")
        return

    router = APIRouter(prefix="/temporal", tags=["temporal"])

    @router.post("/analyze")
    async def temporal_analyze(
        request: TemporalAnalyzeRequest,
    ) -> dict[str, Any]:
        """Build contract lineages, detect evolution patterns, and return timeline.

        Accepts a list of documents (each with vendor, date, amount metadata),
        groups them into contract lineages, runs all six pattern detectors,
        and returns a complete timeline visualization.
        """
        from oraculus_di_auditor.temporal.evolution_detector import (
            EvolutionPatternDetector,
        )
        from oraculus_di_auditor.temporal.lineage_builder import LineageBuilder
        from oraculus_di_auditor.temporal.timeline_generator import TimelineGenerator

        builder = LineageBuilder()
        builder.load_documents(request.documents)
        lineages = builder.build_lineages()

        detector = EvolutionPatternDetector(lineages)
        patterns = detector.detect_all_patterns()

        gen = TimelineGenerator(lineages, patterns)
        timeline = gen.generate_timeline_json()

        # Compute summary
        highest_risk = max(lineages, key=lambda ln: ln.risk_score, default=None)
        total_spend = sum(ln.current_amount for ln in lineages)
        all_dates = [
            d
            for ln in lineages
            for d in (ln.original_date, ln.latest_date)
            if d and d != "unknown"
        ]
        date_range = {
            "start": min(all_dates) if all_dates else "",
            "end": max(all_dates) if all_dates else "",
        }

        return {
            "lineages": [ln.model_dump() for ln in lineages],
            "patterns": [p.model_dump() for p in patterns],
            "timeline": timeline,
            "summary": {
                "lineage_count": len(lineages),
                "pattern_count": len(patterns),
                "total_spend": total_spend,
                "date_range": date_range,
                "highest_risk_lineage": (highest_risk.vendor if highest_risk else None),
            },
        }

    @router.get("/patterns")
    async def list_pattern_types() -> list[dict[str, Any]]:
        """Return all supported evolution pattern types with descriptions."""
        return _PATTERN_TYPES

    @router.post("/lineage/{vendor}")
    async def vendor_lineage(
        vendor: str,
        request: VendorLineageRequest,
    ) -> dict[str, Any]:
        """Return the contract lineage for a specific vendor.

        Builds lineages from the supplied documents and returns the one
        matching the given vendor name (case-insensitive). Returns 404 if
        no documents for that vendor are found.
        """
        from oraculus_di_auditor.temporal.lineage_builder import LineageBuilder

        builder = LineageBuilder()
        builder.load_documents(request.documents)
        lineages = builder.build_lineages()

        match = next(
            (ln for ln in lineages if ln.vendor.lower() == vendor.lower()),
            None,
        )
        if match is None:
            raise HTTPException(
                status_code=404,
                detail=f"No lineage found for vendor '{vendor}'",
            )
        return match.model_dump()

    app.include_router(router)
    logger.info("Temporal analysis routes registered")
