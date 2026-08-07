"""FastAPI routes for RAG natural language querying.

Provides:
- POST /api/v1/rag/query — natural language question with grounded answer
- GET  /api/v1/rag/status — RAG system status (indexed counts, LLM availability)
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from fastapi import APIRouter
    from pydantic import BaseModel, Field

    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False
    BaseModel = object  # type: ignore[assignment,misc]
    Field = lambda *a, **kw: None  # type: ignore[assignment]  # noqa: E731

logger = logging.getLogger(__name__)

# -- request / response models ----------------------------------------------


class RAGQueryRequest(BaseModel):  # type: ignore[misc]
    """Request body for POST /rag/query."""

    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    source_filter: str | None = Field(
        default=None,
        description="Limit to 'documents', 'findings', or 'analysis'",
    )


class RAGQueryResponse(BaseModel):  # type: ignore[misc]
    """Response body for POST /rag/query."""

    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    query: str
    model_used: str
    confidence: float | None = None
    tokens_used: int | None = None


class RAGStatusResponse(BaseModel):  # type: ignore[misc]
    """Response body for GET /rag/status."""

    indexed: dict[str, int]
    llm_available: bool
    llm_provider: str
    llm_model: str


# -- singleton service -------------------------------------------------------

_rag_service = None


def _get_service():
    """Lazy-initialise a module-level OracRAG singleton with disk index loaded."""
    global _rag_service  # noqa: PLW0603
    if _rag_service is None:
        try:

            from oraculus_di_auditor.rag.orac_rag import _DEFAULT_VECTORS_DIR, OracRAG

            svc = OracRAG()
            svc.load_index("collection")
            logger.info(
                "RAG corpus index loaded (%d vectors)",
                len(svc.retriever.vectors),
            )

            # Extend with anomaly-findings (ace) and legal-inference (jim) collections.
            for extra_name in ("ace_collection", "jim_collection"):
                vocab_path = _DEFAULT_VECTORS_DIR / f"{extra_name}_vocab.pkl"
                try:
                    count = svc.extend_index(extra_name, str(vocab_path))
                    logger.info("Loaded extra index %s (%d vectors)", extra_name, count)
                except FileNotFoundError:
                    logger.debug("Optional index not found: %s", extra_name)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to load extra index %s: %s", extra_name, exc)

            _rag_service = svc
        except FileNotFoundError as exc:
            logger.warning(
                "RAG index not found (%s) — run scripts/build_rag_index.py first",
                exc,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("RAG service init failed: %s", exc, exc_info=True)
    return _rag_service


# -- route registration ------------------------------------------------------


def register_rag_routes(app: Any) -> None:
    """Register /api/v1/rag/* endpoints on *app*."""
    if not _FASTAPI_AVAILABLE:
        return  # pragma: no cover

    router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

    @router.post("/query", response_model=RAGQueryResponse)
    async def rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
        """Natural language query against indexed audit data."""
        from fastapi import HTTPException

        svc = _get_service()
        if svc is None:
            raise HTTPException(
                status_code=503,
                detail="RAG index not loaded — run scripts/build_rag_index.py first",
            )

        result = svc.query(question=request.query, top_k=request.top_k)

        # Normalise sources to list[dict]
        raw_sources = result.get("sources", [])
        if raw_sources and isinstance(raw_sources[0], str):
            sources = [{"text": s} for s in raw_sources]
        else:
            sources = [
                s if isinstance(s, dict) else {"text": str(s)} for s in raw_sources
            ]

        answer = result.get("answer") or result.get("error", "No answer generated.")
        model_used = (
            getattr(svc.llm, "model", svc.llm_provider_name) if svc.llm else "none"
        )

        return RAGQueryResponse(
            answer=answer,
            sources=sources,
            query=request.query,
            model_used=model_used,
            confidence=result.get("confidence"),
            tokens_used=None,
        )

    @router.get("/status", response_model=RAGStatusResponse)
    async def rag_status() -> RAGStatusResponse:
        """Return RAG system status."""
        svc = _get_service()
        if svc is None:
            return RAGStatusResponse(
                indexed={"documents": 0, "findings": 0, "analysis": 0},
                llm_available=False,
                llm_provider="ollama",
                llm_model="odia-v1",
            )
        retriever = svc.retriever
        indexed_count = len(retriever.vectors) if hasattr(retriever, "vectors") else 0
        llm_available = svc.llm is not None and svc.llm.is_available()
        model_name = (
            getattr(svc.llm, "model", svc.llm_provider_name) if svc.llm else "none"
        )

        return RAGStatusResponse(
            indexed={"documents": indexed_count, "findings": 0, "analysis": 0},
            llm_available=llm_available,
            llm_provider=svc.llm_provider_name,
            llm_model=model_name,
        )

    app.include_router(router)
