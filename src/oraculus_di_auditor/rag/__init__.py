"""RAG retrieval engine package.

Provides multi-source retrieval across documents, findings, and analysis results.
Also re-exports the legacy OracRAG / RAGRouter classes that previously lived in
``oraculus_di_auditor.rag`` (now ``oraculus_di_auditor.rag.orac_rag``).
"""

from oraculus_di_auditor.rag.context_builder import ContextBuilder
from oraculus_di_auditor.rag.models import (
    BuiltContext,
    EnrichedQuery,
    PromptConfig,
    RAGResponse,
    RetrievalResult,
)
from oraculus_di_auditor.rag.orac_rag import OracRAG, RAGRouter
from oraculus_di_auditor.rag.prompt_router import PromptRouter
from oraculus_di_auditor.rag.query_enrichment import QueryEnricher
from oraculus_di_auditor.rag.rag_service import RAGService
from oraculus_di_auditor.rag.retriever_engine import RetrievalEngine

__all__ = [
    "BuiltContext",
    "ContextBuilder",
    "EnrichedQuery",
    "OracRAG",
    "PromptConfig",
    "PromptRouter",
    "QueryEnricher",
    "RAGResponse",
    "RAGRouter",
    "RAGService",
    "RetrievalEngine",
    "RetrievalResult",
]
