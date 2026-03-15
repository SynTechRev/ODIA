"""Context builder for assembling LLM-ready context from retrieval results.

Formats retrieved chunks into a coherent context string within token limits,
with proper source attribution for LLM citation.

Author: ODIA Team
Date: 2026-03-14
"""

from __future__ import annotations

from oraculus_di_auditor.rag.models import BuiltContext, RetrievalResult


class ContextBuilder:
    """Builds LLM context from retrieval results."""

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def build_context(
        self,
        results: list[RetrievalResult],
        query: str,
        include_metadata: bool = True,
    ) -> BuiltContext:
        """Assemble retrieval results into LLM-ready context.

        Results are formatted with source attribution and packed into the
        token budget in order (highest-score first).
        """
        parts: list[str] = []
        sources_used: list[RetrievalResult] = []
        tokens_used = 0

        for result in results:
            chunk = self._format_result(result, include_metadata)
            chunk_tokens = self.estimate_tokens(chunk)

            if tokens_used + chunk_tokens > self.max_tokens:
                break

            parts.append(chunk)
            sources_used.append(result)
            tokens_used += chunk_tokens

        return BuiltContext(
            context_text="\n\n".join(parts),
            sources_used=sources_used,
            tokens_used=tokens_used,
            tokens_remaining=self.max_tokens - tokens_used,
        )

    def _format_result(self, result: RetrievalResult, include_metadata: bool) -> str:
        """Route to the appropriate formatter by source type."""
        if result.source_type == "document":
            return self.format_document_context(result)
        if result.source_type == "finding":
            return self.format_finding_context(result)
        if result.source_type == "analysis":
            return self.format_analysis_context(result)
        # Fallback for unknown types
        header = (
            f"[Source: {result.source_id}"
            f" | Type: {result.source_type}"
            f" | Score: {result.score:.2f}]"
        )
        return f"{header}\n{result.content}"

    def format_document_context(self, result: RetrievalResult) -> str:
        """Format a document retrieval result with attribution."""
        header = (
            f"[Source: {result.source_id}"
            f" | Type: document"
            f" | Score: {result.score:.2f}]"
        )
        return f"{header}\n{result.content}"

    def format_finding_context(self, result: RetrievalResult) -> str:
        """Format a finding retrieval result with attribution."""
        severity = result.metadata.get("severity", "unknown")
        layer = result.metadata.get("layer", "unknown")
        header = (
            f"[Finding: {result.source_id}"
            f" | Severity: {severity}"
            f" | Detector: {layer}]"
        )
        return f"{header}\n{result.content}"

    def format_analysis_context(self, result: RetrievalResult) -> str:
        """Format an analysis result with attribution."""
        jurisdiction = result.metadata.get(
            "jurisdiction", result.metadata.get("title", "unknown")
        )
        detector = result.metadata.get("detector", "unknown")
        header = f"[Analysis: {jurisdiction}" f" | Detector: {detector}]"
        return f"{header}\n{result.content}"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count. ~4 chars = 1 token for English."""
        return max(1, len(text) // 4)
