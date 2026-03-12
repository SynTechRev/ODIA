"""Context assembly and ranking for RAG system.

This module handles:
- Deduplication of retrieved documents
- Re-ranking by relevance
- Token budget management
- Source attribution formatting

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContextAssembler:
    """Assemble and manage context from retrieved documents."""

    def __init__(self, max_tokens: int = 4000):
        """Initialize context assembler.

        Args:
            max_tokens: Maximum token budget for context
        """
        self.max_tokens = max_tokens

    def assemble(
        self, query_results: list[dict[str, Any]], max_tokens: int | None = None
    ) -> str:
        """Build context from retrieved documents.

        Args:
            query_results: List of retrieval results with format:
                [{"index": int, "score": float, "metadata": dict}, ...]
            max_tokens: Override maximum tokens (optional)

        Returns:
            Formatted context string with sources
        """
        max_tokens = max_tokens or self.max_tokens

        # Deduplicate by file hash or ID
        deduplicated = self.deduplicate_sources(query_results)

        # Sort by relevance score (descending)
        sorted_results = sorted(
            deduplicated, key=lambda x: x.get("score", 0), reverse=True
        )

        # Build context within token budget
        context_parts = []
        total_tokens = 0

        for result in sorted_results:
            metadata = result.get("metadata", {})

            # Extract relevant fields
            corpus_id = metadata.get("id", "N/A")
            title = metadata.get("title", "Untitled")
            source = metadata.get("source", "Unknown")
            text = metadata.get("text", "")
            score = result.get("score", 0)

            # Format source citation
            citation = f"[{corpus_id}] {title}"

            # Build context entry
            entry = f"\n--- Source: {citation} (relevance: {score:.2f}) ---\n{text}\n"

            # Estimate tokens for this entry
            entry_tokens = self.estimate_tokens(entry)

            # Check if we have budget
            if total_tokens + entry_tokens > max_tokens:
                logger.debug(
                    f"Context token budget reached: {total_tokens}/{max_tokens}"
                )
                break

            context_parts.append(entry)
            total_tokens += entry_tokens

        if not context_parts:
            return "No relevant context found."

        return "\n".join(context_parts)

    def deduplicate_sources(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Remove duplicate documents while preserving best match.

        Args:
            results: List of retrieval results

        Returns:
            Deduplicated list, keeping highest-scoring instance of each document
        """
        seen = {}
        deduplicated = []

        for result in results:
            metadata = result.get("metadata", {})

            # Use file_hash or id as deduplication key
            doc_key = metadata.get("file_hash") or metadata.get("id")

            if not doc_key:
                # No deduplication key, keep it
                deduplicated.append(result)
                continue

            # Keep if first occurrence or higher score
            if doc_key not in seen:
                seen[doc_key] = result
                deduplicated.append(result)
            else:
                existing_score = seen[doc_key].get("score", 0)
                current_score = result.get("score", 0)
                if current_score > existing_score:
                    # Replace with higher-scoring instance
                    deduplicated.remove(seen[doc_key])
                    deduplicated.append(result)
                    seen[doc_key] = result

        logger.debug(f"Deduplication: {len(results)} -> {len(deduplicated)} results")
        return deduplicated

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses rough heuristic: 4 characters ≈ 1 token for English text.
        This is approximate but sufficient for budget management.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def format_sources(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format retrieval results as source citations.

        Args:
            results: Retrieval results

        Returns:
            List of formatted source dictionaries
        """
        sources = []

        for result in results:
            metadata = result.get("metadata", {})
            score = result.get("score", 0)

            source = {
                "corpus_id": metadata.get("id", "N/A"),
                "title": metadata.get("title", "Untitled"),
                "file": metadata.get("source", "Unknown"),
                "relevance_score": round(score, 3),
                "snippet": self._extract_snippet(metadata.get("text", ""), max_len=200),
            }
            sources.append(source)

        return sources

    def _extract_snippet(self, text: str, max_len: int = 200) -> str:
        """Extract a snippet from text.

        Args:
            text: Full text
            max_len: Maximum snippet length

        Returns:
            Text snippet with ellipsis if truncated
        """
        if len(text) <= max_len:
            return text

        # Truncate at word boundary
        snippet = text[:max_len].rsplit(" ", 1)[0]
        return snippet + "..."


__all__ = ["ContextAssembler"]
