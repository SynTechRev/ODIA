"""FastAPI REST API Interface for Oraculus-DI-Auditor.

This module provides a RESTful API for document ingestion, analysis, and
anomaly detection. Designed for integration with external systems.

To run the API server:
    pip install fastapi uvicorn
    uvicorn oraculus_di_auditor.interface.api:app --reload

Configure CORS via environment variable:
    export ORACULUS_CORS_ORIGINS="http://localhost:3000,https://example.com"

Example endpoints:
    POST /api/v1/analyze - Analyze a document
    GET /api/v1/health - Health check
"""

from __future__ import annotations

import logging
import os
from typing import Any

# API stub - requires FastAPI to be installed
# This is a minimal interface to demonstrate the architecture

API_VERSION = "1.0.0"
logger = logging.getLogger(__name__)

# Try to import FastAPI dependencies
try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore

    def Field(*args, **kwargs):  # type: ignore  # noqa: N802
        """Stub Field function for when Pydantic is not installed."""
        return None


class AnalyzeRequest(BaseModel):  # type: ignore
    """Request model for /analyze endpoint."""

    document_text: str = Field(
        ..., min_length=1, description="Document text content to analyze"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional document metadata"
    )


class RAGQueryRequest(BaseModel):  # type: ignore
    """Request model for /rag/query endpoint."""

    query: str = Field(..., min_length=1, description="Natural language question")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve"
    )
    corpus_filter: list[str] | None = Field(
        default=None, description="Optional list of corpus IDs to filter"
    )
    date_range: list[str] | None = Field(
        default=None, description="Optional date range [start, end]"
    )


class RAGQueryResponse(BaseModel):  # type: ignore
    """Response model for /rag/query endpoint."""

    answer: str = Field(..., description="Generated answer text")
    sources: list[dict[str, Any]] = Field(
        default_factory=list, description="Source citations"
    )
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    error: str | None = Field(default=None, description="Error message if any")


def create_app() -> Any:
    """Create and configure FastAPI application.

    Returns:
        FastAPI application instance (if FastAPI is installed)

    Raises:
        ImportError: If FastAPI is not installed
    """
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as e:
        raise ImportError(
            "FastAPI is required for the API interface. "
            "Install with: pip install fastapi uvicorn"
        ) from e

    app = FastAPI(
        title="Oraculus-DI-Auditor API",
        description=(
            "Legislative document analysis and anomaly detection API. "
            "Provides endpoints for ingestion, normalization, embedding, "
            "and multi-layered audit intelligence."
        ),
        version=API_VERSION,
    )

    # CORS configuration - secure by default, configurable via environment
    # Set ORACULUS_CORS_ORIGINS to comma-separated list of allowed origins
    # Example: ORACULUS_CORS_ORIGINS="http://localhost:3000,https://app.example.com"
    cors_origins_env = os.getenv("ORACULUS_CORS_ORIGINS", "")
    allow_origins = (
        [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        if cors_origins_env
        else ["http://localhost:3000"]  # Default: localhost only
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    _register_routes(app)
    _register_feature_routes(app)

    return app


def _register_feature_routes(app: Any) -> None:  # noqa: C901
    """Register optional feature routes; each is best-effort (never raises)."""
    try:
        from .routes.orchestrator import register_orchestrator_routes

        register_orchestrator_routes(app)
    except ImportError as e:
        logger.warning(f"Orchestrator routes not available: {e}")

    try:
        from .routes.governor import register_governor_routes

        register_governor_routes(app)
    except ImportError as e:
        logger.warning(f"Governor routes not available: {e}")

    try:
        from .routes.gcn import router as gcn_router

        app.include_router(gcn_router)
        logger.info("Phase 10 GCN routes registered")
    except ImportError as e:
        logger.warning(f"GCN routes not available: {e}")

    try:
        from .routes.mesh import router as mesh_router

        app.include_router(mesh_router)
        logger.info("Phase 10 Mesh routes registered")
    except ImportError as e:
        logger.warning(f"Mesh routes not available: {e}")

    try:
        from .routes.multi_jurisdiction import register_multi_jurisdiction_routes

        register_multi_jurisdiction_routes(app)
        logger.info("Multi-jurisdiction routes registered")
    except Exception as e:
        logger.warning(f"Multi-jurisdiction routes not available: {e}")

    try:
        from .routes.reports import register_report_routes

        register_report_routes(app)
        logger.info("Report generation routes registered")
    except Exception as e:
        logger.warning(f"Report generation routes not available: {e}")

    try:
        from .routes.rag import register_rag_routes

        register_rag_routes(app)
        logger.info("RAG query routes registered")
    except Exception as e:
        logger.warning(f"RAG query routes not available: {e}")

    try:
        from .routes.compliance import register_compliance_routes

        register_compliance_routes(app)
        logger.info("Compliance assessment routes registered")
    except Exception as e:
        logger.warning(f"Compliance routes not available: {e}")

    try:
        from .routes.temporal import register_temporal_routes

        register_temporal_routes(app)
        logger.info("Temporal analysis routes registered")
    except Exception as e:
        logger.warning(f"Temporal routes not available: {e}")


def _load_jurisdiction_config_at_startup() -> Any:
    """Attempt to load jurisdiction config from config/; return None on failure."""
    try:
        from oraculus_di_auditor.config import load_jurisdiction_config

        cfg = load_jurisdiction_config("config")
        logger.info(
            "Jurisdiction config loaded: %s (%s)",
            cfg.name,
            cfg.state or "unknown state",
        )
        return cfg
    except Exception as exc:
        logger.warning("Jurisdiction config not loaded (using defaults): %s", exc)
        return None


def _execute_rag_query(
    request: RAGQueryRequest,
) -> RAGQueryResponse:
    """Execute a RAG query, returning a populated response or an error response.

    Args:
        request: RAG query request containing query text, top_k, and optional filter

    Returns:
        RAGQueryResponse with answer, sources, confidence, and optional error
    """
    _logger = logging.getLogger(__name__)
    try:
        from oraculus_di_auditor.rag import OracRAG

        orac_rag = OracRAG()
        # TODO: Cache loaded index in production (e.g., using functools.lru_cache
        # or global singleton) to avoid reloading on every request
        orac_rag.load_index(index_name="collection")

        if request.corpus_filter:
            result = orac_rag.query_with_filter(
                question=request.query,
                corpus_ids=request.corpus_filter,
                top_k=request.top_k,
            )
        else:
            result = orac_rag.query(
                question=request.query,
                top_k=request.top_k,
                include_sources=True,
            )

        _logger.debug(
            "RAG query complete: confidence=%.2f, sources=%d",
            result.get("confidence", 0),
            len(result.get("sources", [])),
        )
        return RAGQueryResponse(**result)

    except ImportError as e:
        _logger.error("RAG not available: %s", e)
        return RAGQueryResponse(
            answer="",
            sources=[],
            confidence=0.0,
            error="RAG system not available. Install required dependencies.",
        )
    except Exception as e:
        _logger.error("RAG query failed: %s", e, exc_info=True)
        return RAGQueryResponse(
            answer="",
            sources=[],
            confidence=0.0,
            error=str(e),
        )


def _register_routes(app: Any) -> None:
    """Register API routes.

    Args:
        app: FastAPI application instance
    """
    from oraculus_di_auditor.analysis import analyze_document, run_full_analysis

    logger = logging.getLogger(__name__)

    # Load jurisdiction config once at route-registration time
    _jurisdiction_config = _load_jurisdiction_config_at_startup()

    @app.get("/api/v1/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": API_VERSION}

    @app.post("/analyze")
    async def analyze(request: AnalyzeRequest) -> dict[str, Any]:
        """Analyze document text for anomalies (Phase 4 unified pipeline).

        This is the primary analysis endpoint that processes raw document text
        through the complete detection pipeline.

        Args:
            request: AnalyzeRequest containing document_text and optional metadata

        Returns:
            Structured analysis result with findings, scores, flags, and summary
        """
        logger.debug(
            "Analysis request received: text_length=%d, metadata_keys=%s",
            len(request.document_text),
            list(request.metadata.keys()),
        )

        result = run_full_analysis(
            request.document_text,
            request.metadata,
            jurisdiction_config=_jurisdiction_config,
        )

        logger.debug(
            "Analysis complete: anomaly_count=%d, severity=%.2f, lattice=%.2f",
            sum(len(v) for v in result["findings"].values()),
            result["severity_score"],
            result["lattice_score"],
        )

        return result

    @app.post("/api/v1/analyze")
    async def analyze_legacy(document: dict[str, Any]) -> dict[str, Any]:
        """Analyze a normalized document for anomalies (legacy endpoint).

        Args:
            document: Normalized document dict

        Returns:
            Analysis result with anomaly count, score, and details
        """
        logger.debug(
            "Legacy analysis request received: document_id=%s",
            document.get("document_id"),
        )
        result = analyze_document(document)
        return result

    @app.post("/api/v1/rag/query")
    async def rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
        """Natural language query endpoint using RAG.

        Query the legislative corpus using natural language and get
        AI-generated answers with source citations.

        Args:
            request: RAG query request

        Returns:
            RAG query response with answer, sources, and confidence

        Example:
            POST /api/v1/rag/query
            {
                "query": "What vendor contracts were approved in the last fiscal year?",
                "top_k": 5,
                "corpus_filter": ["#23-0148", "#23-0214"]
            }
        """
        logger.debug("RAG query received: %s", request.query)
        return _execute_rag_query(request)

    @app.get("/config/jurisdiction")
    async def jurisdiction_info() -> dict[str, Any]:
        """Return current jurisdiction configuration (non-sensitive fields only).

        Returns name, state, country, meeting_type, and agency count.
        Does not expose Legistar URLs or raw agency alias lists.
        """
        if _jurisdiction_config is None:
            return {
                "loaded": False,
                "name": None,
                "state": None,
                "country": None,
                "meeting_type": None,
                "agency_count": 0,
            }
        return {
            "loaded": True,
            "name": _jurisdiction_config.name,
            "state": _jurisdiction_config.state,
            "country": _jurisdiction_config.country,
            "meeting_type": _jurisdiction_config.meeting_type,
            "agency_count": len(_jurisdiction_config.agencies),
        }

    @app.get("/api/v1/info")
    async def info() -> dict[str, Any]:
        """Get API information and capabilities."""
        return {
            "version": API_VERSION,
            "endpoints": [
                "/api/v1/health",
                "/analyze",  # Primary Phase 4 endpoint
                "/analyze/detailed",  # Per-detector breakdown
                "/analyze/batch",  # Multi-document batch analysis
                "/detectors",  # Detector registry
                "/api/v1/analyze",  # Legacy endpoint
                "/api/v1/info",
                "/config/jurisdiction",  # Current jurisdiction metadata
                "/api/v1/rag/query",  # RAG natural language query
                "/orchestrator/run",  # Phase 8 multi-document orchestrator
                "/governor/state",  # Phase 9 governor state
                "/governor/validate",  # Phase 9 pipeline validation
                "/governor/enforce",  # Phase 9 policy enforcement
                "/gcn/state",  # Phase 10 GCN state
                "/gcn/validate",  # Phase 10 GCN validation
                "/gcn/validate/entity",  # Phase 10 entity constraint validation
                "/mesh/agent/register",  # Phase 10 agent registration
                "/mesh/execute",  # Phase 10 mesh execution
                "/mesh/graph",  # Phase 10 mesh connectivity graph
                "/mesh/state",  # Phase 10 mesh state
            ],
            "detectors": [
                "fiscal",
                "constitutional",
                "surveillance",
                "procurement_timeline",
                "signature_chain",
                "scope_expansion",
                "governance_gap",
                "administrative_integrity",
            ],
            "features": [
                "Multi-format document ingestion",
                "Anomaly detection",
                "Recursive scalar scoring",
                "Provenance tracking",
                "Phase 4 unified analysis pipeline",
                "Phase 5 autonomous agent orchestration",
                "Phase 8 multi-document orchestration",
                "Cross-document pattern recognition",
                "Anomaly correlation",
                "Phase 9 pipeline governance",
                "Security gatekeeper",
                "Policy enforcement",
                "Phase 10 global constraint network",
                "Phase 10 autonomous agent mesh",
                "Multi-agent coordination",
                "Intent-based routing",
                "Result synthesis",
                "RAG natural language querying",
                "AI-powered document Q&A",
                "Source-cited answers",
            ],
        }

    # Register detector-specific routes with access to _jurisdiction_config
    try:
        from .routes.detectors import register_detector_routes

        register_detector_routes(app, jurisdiction_config=_jurisdiction_config)
        logger.info("Detector routes registered")
    except Exception as e:
        logger.warning("Detector routes not available: %s", e)


# Create the app instance
try:
    app = create_app()
except ImportError:
    # FastAPI not installed - API unavailable
    app = None

__all__ = ["create_app", "app", "API_VERSION"]
