"""Data models for the RAG retrieval engine.

Author: ODIA Team
Date: 2026-03-14
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    """A single retrieval result from the engine."""

    content: str
    source_type: str  # "document", "finding", "analysis"
    source_id: str
    score: float
    metadata: dict = Field(default_factory=dict)


class PromptConfig(BaseModel):
    """Configuration for an LLM prompt based on query routing."""

    system_prompt: str
    query_template: str
    response_instructions: str
    expected_source_types: list[str]


class BuiltContext(BaseModel):
    """Assembled LLM context from retrieval results."""

    context_text: str
    sources_used: list[RetrievalResult]
    tokens_used: int
    tokens_remaining: int


class EnrichedQuery(BaseModel):
    """Query enriched with domain-specific expansions."""

    original_query: str
    expanded_terms: list[str]
    search_queries: list[str]
    detected_concepts: list[str]


class RAGResponse(BaseModel):
    """Response from a RAG query combining retrieval with generation."""

    answer: str
    sources: list[RetrievalResult]
    query: str
    model_used: str
    confidence: float | None = None
    tokens_used: int | None = None
