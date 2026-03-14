"""Multi-jurisdiction API routes.

Provides:
  POST /multi/analyze        — run comparative analysis across jurisdictions
  GET  /multi/jurisdictions  — return the loaded registry summary
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from pydantic import BaseModel, Field

    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore

    def Field(*args: Any, **kwargs: Any) -> Any:  # type: ignore  # noqa: N802
        return None


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class MultiDocumentItem(BaseModel):  # type: ignore
    """A single document for multi-jurisdiction analysis."""

    document_text: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultiAnalyzeRequest(BaseModel):  # type: ignore
    """Request body for POST /multi/analyze.

    ``jurisdictions`` maps each jurisdiction_id to a list of documents.
    """

    jurisdictions: dict[str, list[MultiDocumentItem]] = Field(
        ...,
        min_length=1,
        description="Mapping of jurisdiction_id -> list of documents",
    )


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def register_multi_jurisdiction_routes(
    app: Any,
    registry: Any = None,
) -> None:
    """Register /multi/analyze and /multi/jurisdictions on *app*.

    Args:
        app: FastAPI application instance.
        registry: Optional pre-built JurisdictionRegistry.  When None the
            registry is attempted from ``config/multi_jurisdiction/``; if that
            directory is absent an empty registry is used.
    """
    if not _PYDANTIC_AVAILABLE:
        logger.warning(
            "Pydantic not available; multi-jurisdiction routes not registered."
        )
        return

    from oraculus_di_auditor.multi_jurisdiction.pattern_detector import (
        CrossJurisdictionPatternDetector,
    )
    from oraculus_di_auditor.multi_jurisdiction.registry import JurisdictionRegistry
    from oraculus_di_auditor.multi_jurisdiction.report_generator import (
        ComparativeReportGenerator,
    )
    from oraculus_di_auditor.multi_jurisdiction.runner import MultiJurisdictionRunner

    # Build registry once at route-registration time
    if registry is None:
        registry = _load_registry_at_startup()

    @app.post("/multi/analyze")
    async def multi_analyze(request: MultiAnalyzeRequest) -> dict[str, Any]:
        """Run comparative analysis across multiple jurisdictions.

        Request body::

            {
                "jurisdictions": {
                    "city_a": {"documents": [{"document_text": "...", "metadata": {}}]},
                    "city_b": {"documents": [...]}
                }
            }

        Returns the full comparative report JSON produced by
        :class:`~oraculus_di_auditor.multi_jurisdiction.report_generator.ComparativeReportGenerator`.
        """
        if not request.jurisdictions:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=422,
                detail="jurisdictions must not be empty",
            )

        # Build a registry that covers only the requested jurisdiction IDs.
        # Unknown IDs are silently skipped (no config → no analysis).
        local_registry = JurisdictionRegistry()
        for jid in request.jurisdictions:
            try:
                cfg = registry.get(jid)
                local_registry.register(jid, cfg)
            except KeyError:
                logger.warning(
                    "Jurisdiction %r not in registry — results will be empty.",
                    jid,
                )
                # Register a bare default config so the runner still produces
                # a result entry for this jurisdiction.
                from oraculus_di_auditor.config.jurisdiction_loader import (
                    JurisdictionConfig,
                )

                local_registry.register(jid, JurisdictionConfig(name=jid))

        documents_by_jurisdiction = {
            jid: [
                {"document_text": doc.document_text, "metadata": doc.metadata}
                for doc in docs
            ]
            for jid, docs in request.jurisdictions.items()
        }

        runner = MultiJurisdictionRunner(local_registry)
        runner.analyze_all(documents_by_jurisdiction)
        runner_results = runner.get_all_results()

        patterns = CrossJurisdictionPatternDetector(
            runner_results
        ).detect_all_patterns()
        report = ComparativeReportGenerator(
            runner_results, patterns
        ).generate_json_report()
        return report

    @app.get("/multi/jurisdictions")
    async def multi_jurisdictions() -> dict[str, Any]:
        """Return a summary of the loaded jurisdiction registry."""
        return registry.summary()


def _load_registry_at_startup() -> Any:
    """Load registry from config/multi_jurisdiction/; return empty on failure."""
    from oraculus_di_auditor.multi_jurisdiction.registry import JurisdictionRegistry

    try:
        reg = JurisdictionRegistry.from_directory("config/multi_jurisdiction")
        logger.info(
            "Multi-jurisdiction registry loaded: %d jurisdiction(s)",
            reg.count(),
        )
        return reg
    except Exception as exc:
        logger.warning("Multi-jurisdiction registry not loaded (using empty): %s", exc)
        return JurisdictionRegistry()
