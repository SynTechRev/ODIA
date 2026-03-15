"""FastAPI routes for RAG natural language querying.

Provides:
- POST /rag/query — natural language question with grounded answer
- GET  /rag/status — RAG system status (indexed counts, LLM availability)
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

    question: str = Field(..., min_length=1)
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
    """Lazy-initialise a module-level RAGService singleton."""
    global _rag_service  # noqa: PLW0603
    if _rag_service is None:
        from oraculus_di_auditor.rag import RAGService

        _rag_service = RAGService()
    return _rag_service


# -- route registration ------------------------------------------------------


def register_rag_routes(app: Any) -> None:
    """Register /rag/* endpoints on *app*."""
    if not _FASTAPI_AVAILABLE:
        return  # pragma: no cover

    router = APIRouter(prefix="/rag", tags=["rag"])

    @router.post("/query", response_model=RAGQueryResponse)
    async def rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
        """Natural language query against indexed audit data.

        If no LLM is configured the endpoint still returns 200
        with retrieval results (the context is still valuable).
        """
        svc = _get_service()
        resp = svc.query(
            question=request.question,
            top_k=request.top_k,
            source_filter=request.source_filter,
        )
        return RAGQueryResponse(
            answer=resp.answer,
            sources=[s.model_dump() for s in resp.sources],
            query=resp.query,
            model_used=resp.model_used,
            confidence=resp.confidence,
            tokens_used=resp.tokens_used,
        )

    @router.get("/status", response_model=RAGStatusResponse)
    async def rag_status() -> RAGStatusResponse:
        """Return RAG system status."""
        svc = _get_service()
        status = svc.get_status()
        return RAGStatusResponse(**status)

    app.include_router(router)
