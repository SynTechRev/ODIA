"""Main RAG service for natural language queries against audit data.

Single entry point tying together retrieval, context building, prompt
routing, and LLM generation.

Author: ODIA Team
Date: 2026-03-15
"""

from __future__ import annotations

import logging
from typing import Any

from oraculus_di_auditor.llm_providers import BaseLLMProvider, get_provider
from oraculus_di_auditor.rag.context_builder import ContextBuilder
from oraculus_di_auditor.rag.models import RAGResponse
from oraculus_di_auditor.rag.prompt_router import PromptRouter
from oraculus_di_auditor.rag.query_enrichment import QueryEnricher
from oraculus_di_auditor.rag.retriever_engine import RetrievalEngine

logger = logging.getLogger(__name__)


class RAGService:
    """Main RAG service for natural language queries against audit data."""

    def __init__(
        self,
        retrieval_engine: RetrievalEngine | None = None,
        context_builder: ContextBuilder | None = None,
        prompt_router: PromptRouter | None = None,
        llm_provider: str = "ollama",
        llm_model: str | None = None,
    ):
        """Initialize RAG service. Creates default components if not provided."""
        self._engine = retrieval_engine or RetrievalEngine()
        self._context_builder = context_builder or ContextBuilder()
        self._prompt_router = prompt_router or PromptRouter()
        self._enricher = QueryEnricher()

        self._llm: BaseLLMProvider | None = None
        self._llm_provider_name = llm_provider
        self._llm_model_name = llm_model or ""

        try:
            kwargs: dict[str, Any] = {}
            if llm_model:
                kwargs["model"] = llm_model
            self._llm = get_provider(llm_provider, **kwargs)
            if not self._llm.is_available():
                logger.info("LLM provider '%s' not available", llm_provider)
                self._llm = None
        except Exception:
            logger.info("Could not initialize LLM provider '%s'", llm_provider)

        self._counts: dict[str, int] = {
            "documents": 0,
            "findings": 0,
            "analysis": 0,
        }

    # -- data loading --------------------------------------------------------

    def load_corpus(
        self,
        documents: list[dict] | None = None,
        findings: list[dict] | None = None,
        analysis_results: list[dict] | None = None,
    ) -> dict[str, int]:
        """Load data into the retrieval engine. Returns counts per type."""
        if documents:
            n = self._engine.index_documents(documents)
            self._counts["documents"] += n
        if findings:
            n = self._engine.index_findings(findings)
            self._counts["findings"] += n
        if analysis_results:
            n = self._engine.index_analysis_results(analysis_results)
            self._counts["analysis"] += n
        return dict(self._counts)

    # -- querying ------------------------------------------------------------

    def query(
        self,
        question: str,
        top_k: int = 5,
        source_filter: str | None = None,
        max_context_tokens: int = 4000,
    ) -> RAGResponse:
        """Ask a natural language question and get a grounded answer."""
        # 1. Enrich and classify
        enriched = self._enricher.enrich(question)
        query_type = self._prompt_router.classify_query(question)

        # 2. Retrieve using all search queries from enrichment
        results = []
        seen_ids: set[str] = set()
        for sq in enriched.search_queries:
            for r in self._engine.search(sq, top_k=top_k, source_filter=source_filter):
                if r.source_id not in seen_ids:
                    seen_ids.add(r.source_id)
                    results.append(r)
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:top_k]

        # 3. Build context
        builder = ContextBuilder(max_tokens=max_context_tokens)
        ctx = builder.build_context(results, query=question)

        # 4. Route prompt
        available = {k for k, v in self._counts.items() if v > 0}
        prompt_cfg = self._prompt_router.route(question, available_data=available)

        # 5. Generate
        if self._llm is None:
            return RAGResponse(
                answer=(
                    "No LLM configured. Showing retrieval results only. "
                    f"Query type: {query_type}. "
                    f"Retrieved {len(ctx.sources_used)} sources."
                ),
                sources=ctx.sources_used,
                query=question,
                model_used="none",
                confidence=None,
                tokens_used=ctx.tokens_used,
            )

        filled_prompt = prompt_cfg.query_template.replace(
            "{context}", ctx.context_text
        ).replace("{question}", question)

        try:
            answer = self._llm.generate(
                prompt=prompt_cfg.system_prompt,
                context=filled_prompt,
            )
        except Exception as exc:
            logger.error("LLM generation failed: %s", exc)
            answer = f"LLM generation failed: {exc}"

        return RAGResponse(
            answer=answer,
            sources=ctx.sources_used,
            query=question,
            model_used=self._llm_model_name or self._llm_provider_name,
            confidence=None,
            tokens_used=ctx.tokens_used,
        )

    def query_without_llm(
        self,
        question: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Retrieve relevant context without calling an LLM."""
        query_type = self._prompt_router.classify_query(question)
        results = self._engine.search(question, top_k=top_k)
        ctx = self._context_builder.build_context(results, query=question)

        available = {k for k, v in self._counts.items() if v > 0}
        prompt_cfg = self._prompt_router.route(question, available_data=available)

        return {
            "query": question,
            "query_type": query_type,
            "retrieved_sources": results,
            "context_preview": ctx.context_text[:500],
            "prompt_that_would_be_used": prompt_cfg.query_template[:300],
            "message": ("No LLM configured. Showing retrieval results only."),
        }

    # -- status --------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return RAG system status."""
        return {
            "indexed": dict(self._counts),
            "llm_available": self._llm is not None,
            "llm_provider": self._llm_provider_name,
            "llm_model": self._llm_model_name,
        }
