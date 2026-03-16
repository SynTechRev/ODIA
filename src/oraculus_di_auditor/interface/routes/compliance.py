"""FastAPI routes for CCOPS compliance assessment.

Provides:
- POST /compliance/assess   — run assessment against ODIA findings
- GET  /compliance/mandates — list all 11 CCOPS mandates
- GET  /compliance/mandates/{mandate_id} — single mandate detail
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

# -- request / response models -----------------------------------------------


class ComplianceAssessRequest(BaseModel):  # type: ignore[misc]
    """Request body for POST /compliance/assess."""

    jurisdiction: str = Field(..., min_length=1, description="Jurisdiction name")
    documents: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "ODIA analysis results. Each item may be a flat anomaly dict "
            "(with a 'layer' key) or an analysis-result dict with a 'findings' key."
        ),
    )
    has_ccops_ordinance: bool = Field(
        default=False,
        description="Whether the jurisdiction has adopted a CCOPS ordinance",
    )
    state: str | None = Field(
        default=None, description="Two-letter state abbreviation for Atlas lookups"
    )


# -- helpers -----------------------------------------------------------------


def _extract_findings(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten documents into a list of ODIA anomaly dicts.

    Accepts two formats:
    - Flat anomaly dict: ``{"id": ..., "layer": ..., "issue": ..., ...}``
    - Analysis-result dict: ``{"findings": {"fiscal": [...], "governance_gap": [...]}}``
    """
    findings: list[dict[str, Any]] = []
    for doc in documents:
        if "layer" in doc:
            # Already a flat anomaly finding
            findings.append(doc)
        elif "findings" in doc and isinstance(doc["findings"], dict):
            # Nested findings dict keyed by detector layer
            for layer_findings in doc["findings"].values():
                if isinstance(layer_findings, list):
                    findings.extend(layer_findings)
    return findings


# -- route registration ------------------------------------------------------


def register_compliance_routes(app: Any) -> None:
    """Register /compliance/* endpoints on *app*."""
    if not _FASTAPI_AVAILABLE:
        return  # pragma: no cover

    from oraculus_di_auditor.adapters.ccops_adapter import CCOPSAdapter
    from oraculus_di_auditor.adapters.compliance_engine import (
        ComplianceAssessmentEngine,
    )

    router = APIRouter(prefix="/compliance", tags=["compliance"])

    # Shared adapter instances (lightweight, no I/O at init time)
    _ccops = CCOPSAdapter()
    _engine = ComplianceAssessmentEngine(ccops=_ccops)

    @router.post("/assess")
    async def assess_compliance(
        request: ComplianceAssessRequest,
    ) -> dict[str, Any]:
        """Run CCOPS compliance assessment against ODIA findings.

        Flattens ``documents`` into anomaly findings, then maps each finding
        to the CCOPS mandates whose verification detectors match its ``layer``.
        Returns a full ``ComplianceScorecard`` as JSON.
        """
        findings = _extract_findings(request.documents)
        scorecard = _engine.assess(
            jurisdiction=request.jurisdiction,
            analysis_results=findings,
            state=request.state,
            has_ccops_ordinance=request.has_ccops_ordinance,
        )
        return scorecard.model_dump()

    @router.get("/mandates")
    async def list_mandates() -> list[dict[str, Any]]:
        """Return all 11 CCOPS model bill mandates.

        Each mandate includes its ID, title, description, required evidence
        types, mapped ODIA verification detectors, and severity if missing.
        """
        return [m.model_dump() for m in _ccops.get_all_mandates()]

    @router.get("/mandates/{mandate_id}")
    async def get_mandate(mandate_id: str) -> dict[str, Any]:
        """Return a single CCOPS mandate by ID (e.g. ``M-01``).

        Raises 404 if the mandate ID is not found.
        """
        mandate = _ccops.get_mandate(mandate_id)
        if mandate is None:
            raise HTTPException(
                status_code=404, detail=f"Mandate '{mandate_id}' not found"
            )
        return mandate.model_dump()

    app.include_router(router)
