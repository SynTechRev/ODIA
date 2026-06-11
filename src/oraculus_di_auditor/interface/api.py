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
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Load .env from repo root before any os.getenv() calls so CORS origins,
# webhook tokens, and other config are available without manual export.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[4] / ".env", override=False)
except ImportError:
    pass  # python-dotenv not installed — fall back to environment variables only

# API stub - requires FastAPI to be installed
# This is a minimal interface to demonstrate the architecture

API_VERSION = "1.0.0"
logger = logging.getLogger(__name__)


def _resolve_odia_version() -> str:
    """Return the installed ODIA release version.

    Priority: ODIA_VERSION env var (set by desktop backend.js) →
    importlib.metadata (dev installs) → compiled-in default.
    The env var takes precedence so the desktop app always reports the
    version baked into the Electron package, not whatever dist-info the
    PyInstaller bundle happens to surface.
    """
    env_ver = os.environ.get("ODIA_VERSION")
    if env_ver:
        return env_ver
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version("odia")
    except (ImportError, Exception):
        return "3.3.1"


ODIA_VERSION = _resolve_odia_version()

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


@asynccontextmanager
async def _lifespan(app: Any):
    """FastAPI lifespan — pre-warm expensive singletons at startup."""
    try:
        from oraculus_di_auditor.legal.legal_resolver import get_resolver

        resolver = get_resolver()
        stats = resolver.statistics()
        logger.info("Legal resolver pre-warmed at boot: %s", stats)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Legal resolver pre-warm failed: %s", exc)
    yield


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

    # Configure bundled OCR binaries (tesseract, poppler) before any PDF
    # path is triggered. Safe no-op outside PyInstaller or when binaries
    # are absent from the bundle.
    try:
        from oraculus_di_auditor.bundled_binaries import configure_bundled_binaries

        logger.info("Bundled OCR binary status: %s", configure_bundled_binaries())
    except Exception as exc:  # noqa: BLE001 - never crash app startup
        logger.warning("Bundled OCR binary configuration failed: %s", exc)

    app = FastAPI(
        title="Oraculus-DI-Auditor API",
        description=(
            "Legislative document analysis and anomaly detection API. "
            "Provides endpoints for ingestion, normalization, embedding, "
            "and multi-layered audit intelligence."
        ),
        version=API_VERSION,
        lifespan=_lifespan,
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

    # v2.7.3 V1 — bootstrap the DB schema before routes register.
    # Without this, every code path that calls `get_db()` silently
    # degrades to "DB not initialised" and returns empty results:
    # SeenHash dedup (D2), Document/Analysis/Anomaly persistence
    # (C5.1), RAIAService reads (C5), and the Orchestrator
    # /executions endpoint (D4) all depend on this. init_db() is
    # idempotent — ``Base.metadata.create_all`` skips tables that
    # already exist, so it's safe on every subsequent boot too.
    _init_database_at_startup()

    # Register routes
    _register_routes(app)
    _register_feature_routes(app)

    # ODIA AI subsystem integration (odia_ai package) - guarded import.
    # Exposes /ai/extract, /ai/status, /ai/health, /ai/corrections,
    # /ai/corrections/stats, /ai/registry/versions. Silent no-op if odia_ai
    # is not installed so the core backend still starts.
    try:
        from odia_ai.server_routes import include_ai_routes

        ai_config_path = os.environ.get("ODIA_AI_CONFIG")
        include_ai_routes(app, config_path=ai_config_path)
        logger.info("odia_ai routes registered under /ai/*")
    except ImportError:
        logger.info("odia_ai not installed; /ai/* routes unavailable")
    except Exception as exc:  # noqa: BLE001 - never crash app startup
        logger.warning("odia_ai route registration failed: %s", exc)

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

    try:
        from .routes.upload import register_upload_routes

        register_upload_routes(app)
        logger.info("Upload and audit pipeline routes registered")
    except Exception as e:
        logger.warning(f"Upload routes not available: {e}")

    try:
        from .routes.retrieval import register_retrieval_routes

        register_retrieval_routes(app)
        logger.info("Legistar retrieval routes registered")
    except Exception as e:
        logger.warning(f"Retrieval routes not available: {e}")

    try:
        from .routes.auth_routes import register_auth_routes

        register_auth_routes(app)
        logger.info("Auth routes registered")
    except Exception as e:
        logger.warning(f"Auth routes not available: {e}")

    try:
        from .routes.workspace_routes import register_workspace_routes

        register_workspace_routes(app)
        logger.info("Workspace routes registered")
    except Exception as e:
        logger.warning(f"Workspace routes not available: {e}")

    try:
        from .routes.webhook import register_webhook_routes

        # register_webhook_routes self-guards on ODIA_WEBHOOK_TOKEN — if
        # the env var is unset it logs an error and refuses to register
        # the /api/v1/webhook/* surface. Failing loud on missing token
        # beats silently exposing an unauthenticated n8n pipeline.
        register_webhook_routes(app)
        logger.info("n8n webhook routes registration attempted")
    except Exception as e:
        logger.warning(f"Webhook routes not available: {e}")

    try:
        from .routes.cpra import register_cpra_routes

        register_cpra_routes(app)
        logger.info("CPRA deadline-watcher routes registered")
    except Exception as e:
        logger.warning(f"CPRA routes not available: {e}")

    try:
        from .routes.field import register_field_routes

        register_field_routes(app)
        logger.info("Field-verification routes registered")
    except Exception as e:
        logger.warning(f"Field routes not available: {e}")

    try:
        from .routes.automation import register_automation_routes

        # Self-guarded on httpx + fastapi presence. No N8N_API_KEY gate
        # at register time — the health endpoint is useful without it,
        # and the per-endpoint 503s explain the config miss when workflow
        # / execution endpoints are hit without a key.
        register_automation_routes(app)
        logger.info("n8n automation routes registered")
    except Exception as e:
        logger.warning(f"Automation routes not available: {e}")

    try:
        from .routes.triggers import register_trigger_routes

        # v2.7.4 W1 — Manual-trigger endpoints under /api/v1/triggers/*
        # so the Automation page's "Manual Triggers" panel works without
        # ODIA_WEBHOOK_TOKEN or n8n online.
        register_trigger_routes(app)
        logger.info("Manual-trigger routes registered")
    except Exception as e:
        logger.warning(f"Trigger routes not available: {e}")

    try:
        from .routes.dashboard import register_dashboard_routes

        # v2.7.6 X1 — Dashboard summary endpoint backing the Analysis
        # Summary card on the home page (was previously reading from a
        # Zustand store that production audits never wrote to).
        register_dashboard_routes(app)
        logger.info("Dashboard summary route registered")
    except Exception as e:
        logger.warning(f"Dashboard routes not available: {e}")

    try:
        from .routes.config_routes import register_config_routes

        # v2.10.x — runtime-mutable config (currently: webhook token).
        # Lets the Settings UI persist ODIA_WEBHOOK_TOKEN to a per-user
        # file without requiring the env var to be pre-set, which is
        # impossible on the Electron desktop install.
        register_config_routes(app)
        logger.info("Runtime-config routes registered")
    except Exception as e:
        logger.warning(f"Config routes not available: {e}")

    try:
        from .routes.query import register_query_routes

        # v3.2.0 — DB-backed list query endpoints for the operator UI
        # listing pages (Documents / Anomalies / Analysis / Synthesis).
        # Pre-v3.2 those pages read from a browser localStorage store
        # that only captured UI-driven uploads, leaving the entire
        # webhook-ingested corpus invisible in the UI. These endpoints
        # close that gap by exposing paginated + filterable views over
        # the persisted Document / Analysis / Anomaly rows.
        register_query_routes(app)
        logger.info("Query routes registered")
    except Exception as e:
        logger.warning(f"Query routes not available: {e}")

    try:
        from .routes.legal_routes import register_legal_routes

        # v3.3.0 — Legal-corpus status endpoint backing the dashboard
        # 'Legal corpus' card + n8n verification workflows. Resolver
        # warms on first call to get_resolver() either here (via the
        # startup hook below) or lazily on the first plain_language
        # render.
        register_legal_routes(app)
        logger.info("Legal routes registered")
    except Exception as e:
        logger.warning(f"Legal routes not available: {e}")


def _init_database_at_startup() -> None:
    """Best-effort DB schema bootstrap at app start (v2.7.3 V1).

    ``oraculus_di_auditor.db.session.init_db()`` creates every table
    declared in ``db/models.py`` via
    ``Base.metadata.create_all(bind=_engine)``. Idempotent — existing
    tables are skipped — so it's safe on every boot including
    subsequent installer launches. We catch failures rather than
    letting them crash startup: the backend can still serve
    non-DB-backed endpoints (``/analyze``, ``/detectors``,
    ``/orchestrator/task-graph``) even if DB wiring is busted, so
    failing open here preserves UX for the detector paths. Endpoints
    that do need the DB handle their own ``get_db()`` exceptions.
    """
    try:
        from oraculus_di_auditor.db.session import init_db
    except ImportError:
        logger.warning(
            "DB layer not available (SQLAlchemy missing) — continuing without "
            "Document/Analysis/Anomaly persistence."
        )
        return
    try:
        init_db()
        logger.info("Database schema bootstrapped at startup (idempotent).")
    except Exception as exc:  # noqa: BLE001 - never crash app startup
        logger.warning(
            "init_db() failed at startup — DB-backed endpoints will degrade: %s",
            exc,
        )


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


# Maps corpus_filter terms to (index_name, vocab_filename) pairs.
# The index builder (scripts/build_rag_index.py) creates all three collections.
_INDEX_MAP: dict[str, tuple[str, str]] = {
    "documents": ("collection", "data/vectors/collection_vocab.pkl"),
    "corpus": ("collection", "data/vectors/collection_vocab.pkl"),
    "findings": ("ace_collection", "data/vectors/ace_collection_vocab.pkl"),
    "ace": ("ace_collection", "data/vectors/ace_collection_vocab.pkl"),
    "patterns": ("jim_collection", "data/vectors/jim_collection_vocab.pkl"),
    "jim": ("jim_collection", "data/vectors/jim_collection_vocab.pkl"),
}

_ALL_INDICES: list[tuple[str, str]] = [
    ("collection", "data/vectors/collection_vocab.pkl"),
    ("ace_collection", "data/vectors/ace_collection_vocab.pkl"),
    ("jim_collection", "data/vectors/jim_collection_vocab.pkl"),
]

# Module-level OracRAG cache keyed by index_name — avoids reloading TF-IDF
# vocabulary and numpy arrays on every request.
_rag_cache: dict[str, Any] = {}


def _get_rag_instance(index_name: str, vocab_path: str) -> Any:
    """Return a cached OracRAG instance for *index_name*, loading it on first use."""
    if index_name not in _rag_cache:
        from oraculus_di_auditor.rag import OracRAG

        instance = OracRAG()
        try:
            instance.load_index(index_name=index_name, vocab_path=vocab_path)
        except FileNotFoundError:
            return None
        _rag_cache[index_name] = instance
    return _rag_cache[index_name]


def _resolve_target_indices(
    corpus_filter: list[str] | None,
) -> list[tuple[str, str]]:
    """Map corpus_filter values to (index_name, vocab_path) pairs.

    Unknown filter terms are ignored. No filter → all three indices.
    """
    if not corpus_filter:
        return _ALL_INDICES
    seen: set[str] = set()
    targets: list[tuple[str, str]] = []
    for term in corpus_filter:
        pair = _INDEX_MAP.get(term.lower())
        if pair and pair[0] not in seen:
            targets.append(pair)
            seen.add(pair[0])
    return targets or _ALL_INDICES


def _execute_rag_query(
    request: RAGQueryRequest,
) -> RAGQueryResponse:
    """Execute a RAG query across one or more vector indices.

    corpus_filter routes the query to specific sub-indices:
      "documents"/"corpus"  → collection (one entry per document)
      "findings"/"ace"      → ace_collection (one entry per anomaly)
      "patterns"/"jim"      → jim_collection (cross-jurisdiction patterns)
    No filter → all three indices are queried and sources are merged.
    """
    _logger = logging.getLogger(__name__)
    try:
        targets = _resolve_target_indices(request.corpus_filter)

        all_sources: list[dict] = []
        primary_answer = ""
        primary_confidence = 0.0

        for index_name, vocab_path in targets:
            rag = _get_rag_instance(index_name, vocab_path)
            if rag is None:
                _logger.debug("Index '%s' not built yet — skipping", index_name)
                continue

            result = rag.query(
                question=request.query,
                top_k=request.top_k,
                include_sources=True,
            )

            sources = result.get("sources", [])
            for src in sources:
                src.setdefault("index", index_name)
            all_sources.extend(sources)

            conf = result.get("confidence") or 0.0
            if conf > primary_confidence:
                primary_confidence = conf
                primary_answer = result.get("answer", "")

        if not all_sources and not primary_answer:
            return RAGQueryResponse(
                answer="No indexed data found. Run scripts/build_rag_index.py first.",
                sources=[],
                confidence=0.0,
            )

        # Deduplicate and sort sources by score descending
        seen_ids: set[str] = set()
        merged: list[dict] = []
        for src in sorted(all_sources, key=lambda s: s.get("score", 0), reverse=True):
            sid = src.get("id") or src.get("source_id") or str(src)
            if sid not in seen_ids:
                seen_ids.add(sid)
                merged.append(src)
        merged = merged[: request.top_k]

        _logger.debug(
            "RAG query complete: indices=%s confidence=%.2f sources=%d",
            [t[0] for t in targets],
            primary_confidence,
            len(merged),
        )
        return RAGQueryResponse(
            answer=primary_answer,
            sources=merged,
            confidence=round(primary_confidence, 3),
        )

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
        """Health check endpoint.

        ``version`` stays set to the API schema version (1.0.0) for
        back-compat with existing clients. v2.7.3 adds ``odia_version``
        so the DashboardLayout sidebar pill can render the live release
        tag without a hardcoded literal.
        """
        return {
            "status": "healthy",
            "version": API_VERSION,
            "odia_version": ODIA_VERSION,
        }

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
