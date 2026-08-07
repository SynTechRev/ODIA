"""RAG (Retrieval-Augmented Generation) system for natural language querying.

This module provides the main RAG orchestration that combines:
- Vector retrieval (using existing embeddings and retriever)
- Context assembly and ranking
- LLM-based answer generation

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import logging
import os
from pathlib import Path
from typing import Any

from ..embeddings import LocalEmbedder
from ..llm_providers import get_provider
from ..rag_context import ContextAssembler
from ..rag_prompts import get_prompt_for_query
from ..retriever import Retriever

# Absolute fallback for vectors directory — works regardless of process CWD.
# Path: orac_rag.py -> rag/ -> oraculus_di_auditor/ -> src/ -> repo_root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_VECTORS_DIR = Path(
    os.getenv("ODIA_VECTORS_DIR", str(_REPO_ROOT / "data" / "vectors"))
)

# Import config
try:
    import sys

    sys.path.insert(0, str(_REPO_ROOT / "config"))
    from rag_config import (
        DEFAULT_VOCAB_PATH,
        RAG_LLM_MODEL,
        RAG_LLM_PROVIDER,
        RAG_MAX_CONTEXT_TOKENS,
        RAG_SIMILARITY_THRESHOLD,
        RAG_TEMPERATURE,
        RAG_TOP_K,
        VECTOR_INDICES,
    )
except ImportError:
    # Fallback defaults if config not available
    RAG_LLM_PROVIDER = "ollama"
    RAG_LLM_MODEL = "odia-v1"
    RAG_TEMPERATURE = 0.1
    RAG_TOP_K = 5
    RAG_SIMILARITY_THRESHOLD = 0.3
    RAG_MAX_CONTEXT_TOKENS = 4000
    VECTOR_INDICES = {"corpus": str(_DEFAULT_VECTORS_DIR / "collection")}
    DEFAULT_VOCAB_PATH = str(_DEFAULT_VECTORS_DIR / "collection_vocab.pkl")

logger = logging.getLogger(__name__)

# odia-v1 was fine-tuned to output full ODIA report templates, so it regenerates
# the template header before the actual analysis text. Strip the echoed prefix.
_CUE_MARKERS = (
    "Your anomaly analysis:",
    "Your audit analysis:",
    "Your compliance analysis:",
    "Your vendor analysis:",
    "Your answer:",
)


def _strip_prompt_echo(text: str) -> str:
    """Return only the generated content after the last cue marker, if present."""
    best_idx = -1
    best_marker_len = 0
    for marker in _CUE_MARKERS:
        idx = text.rfind(marker)
        if idx > best_idx:
            best_idx = idx
            best_marker_len = len(marker)
    if best_idx != -1:
        return text[best_idx + best_marker_len :].strip()
    return text.strip()


class OracRAG:
    """Main RAG system for natural language query answering."""

    def __init__(
        self,
        embedder: LocalEmbedder | None = None,
        retriever: Retriever | None = None,
        llm_provider: str = RAG_LLM_PROVIDER,
        llm_model: str = RAG_LLM_MODEL,
        vectors_dir: Path | None = None,
    ):
        """Initialize RAG system.

        Args:
            embedder: Embedder instance (will be created if None)
            retriever: Retriever instance (will be created if None)
            llm_provider: LLM provider name ("openai", "anthropic", "ollama")
            llm_model: Model name for the provider
            vectors_dir: Directory containing vector indices
        """
        self.embedder = embedder or LocalEmbedder(max_features=2048)
        self.retriever = retriever or Retriever(
            vectors_dir=vectors_dir or _DEFAULT_VECTORS_DIR
        )
        self.context_assembler = ContextAssembler(max_tokens=RAG_MAX_CONTEXT_TOKENS)
        # Extra (embedder, retriever, name) tuples for multi-index queries.
        self._extra_indexes: list[tuple[LocalEmbedder, Retriever, str]] = []

        # Initialize LLM provider
        self.llm_provider_name = llm_provider
        try:
            self.llm = get_provider(
                llm_provider, model=llm_model, temperature=RAG_TEMPERATURE
            )
        except Exception as e:
            logger.warning(f"Failed to initialize LLM provider: {e}")
            self.llm = None

        self.is_index_loaded = False

    def load_index(
        self, index_name: str = "collection", vocab_path: str | None = None
    ) -> None:
        """Load vector index and vocabulary.

        Args:
            index_name: Index filename (without extension)
            vocab_path: Path to vocabulary file (optional)
        """
        vocab_path = vocab_path or DEFAULT_VOCAB_PATH

        # Load vocabulary for embedder
        vocab_file = Path(vocab_path)
        if vocab_file.exists():
            self.embedder.load_vocabulary(vocab_file)
            logger.info(f"Loaded vocabulary from {vocab_path}")
        else:
            logger.warning(f"Vocabulary file not found: {vocab_path}")
            raise FileNotFoundError(f"Vocabulary file not found: {vocab_path}")

        # Load retriever index
        self.retriever.load(index_name)
        self.is_index_loaded = True
        logger.info(f"Loaded vector index: {index_name}")

    def extend_index(self, index_name: str, vocab_path: str) -> int:
        """Load an additional collection alongside the primary corpus.

        Each extra collection gets its own embedder + retriever because
        collections have different TF-IDF vocabularies.

        Args:
            index_name: Base filename of the additional index (e.g. "ace_collection")
            vocab_path: Absolute path to the vocabulary pickle for this collection

        Returns:
            Number of vectors loaded from the extra collection
        """
        vocab_file = Path(vocab_path)
        if not vocab_file.exists():
            raise FileNotFoundError(f"Vocab not found: {vocab_path}")

        extra_embedder = LocalEmbedder()
        extra_embedder.load_vocabulary(vocab_file)

        extra_retriever = Retriever(vectors_dir=self.retriever.vectors_dir)
        extra_retriever.load(index_name)

        count = len(extra_retriever.vectors)
        self._extra_indexes.append((extra_embedder, extra_retriever, index_name))
        logger.info("Extended RAG with %s (%d vectors)", index_name, count)
        return count

    def query(
        self,
        question: str,
        top_k: int = RAG_TOP_K,
        include_sources: bool = True,
        threshold: float = RAG_SIMILARITY_THRESHOLD,
    ) -> dict[str, Any]:
        """Answer a natural language question using RAG.

        Args:
            question: User's natural language question
            top_k: Number of documents to retrieve
            include_sources: Whether to include source citations
            threshold: Minimum similarity threshold

        Returns:
            Dictionary with:
                - answer: Generated answer text
                - sources: List of source citations (if include_sources=True)
                - confidence: Confidence score
                - error: Error message (if any)
        """
        # Check if index is loaded
        if not self.is_index_loaded:
            return {
                "answer": "",
                "sources": [],
                "confidence": 0.0,
                "error": "Vector index not loaded. Call load_index() first.",
            }

        try:
            # Step 1: Embed query
            query_vector = self.embedder.embed(question)
            logger.debug(f"Embedded query: {question[:50]}...")

            # Step 2: Retrieve from primary index
            raw_results = self.retriever.search(query_vector, top_k=top_k)
            results = [
                {"index": idx, "score": score, "metadata": metadata}
                for idx, score, metadata in raw_results
            ]

            # Retrieve from extra indexes (ace, jim, etc.) and merge
            for extra_embedder, extra_retriever, idx_name in self._extra_indexes:
                try:
                    extra_vector = extra_embedder.embed(question)
                    extra_raw = extra_retriever.search(extra_vector, top_k=top_k)
                    for idx, score, metadata in extra_raw:
                        results.append(
                            {
                                "index": idx,
                                "score": score,
                                "metadata": {**metadata, "_source_index": idx_name},
                            }
                        )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Extra index %s search failed: %s", idx_name, exc)

            # Sort merged results by score descending, keep top_k
            results.sort(key=lambda r: r["score"], reverse=True)
            results = results[:top_k]

            # Filter by threshold
            results = [r for r in results if r["score"] >= threshold]

            if not results:
                return {
                    "answer": "No relevant documents found for your query.",
                    "sources": [],
                    "confidence": 0.0,
                }

            logger.debug(f"Retrieved {len(results)} relevant documents")

            # Step 3: Assemble context
            context = self.context_assembler.assemble(results)

            # Step 4: Generate answer with LLM
            if self.llm and self.llm.is_available():
                prompt_template = get_prompt_for_query(question)
                prompt = prompt_template.format(context=context, question=question)

                answer = self.llm.generate(
                    prompt=prompt,
                    context="",  # Already in prompt
                )
                answer = _strip_prompt_echo(answer)
            else:
                # Fallback: return context without LLM generation
                logger.warning("LLM not available, returning context only")
                answer = (
                    f"LLM not available. Retrieved context:\n\n{context}\n\n"
                    f"To enable answer generation, configure an LLM provider "
                    f"(set OPENAI_API_KEY, ANTHROPIC_API_KEY, or run Ollama)."
                )

            # Step 5: Format sources
            sources = []
            if include_sources:
                sources = self.context_assembler.format_sources(results)

            # Calculate confidence (average similarity score)
            confidence = sum(r["score"] for r in results) / len(results)

            return {
                "answer": answer,
                "sources": sources,
                "confidence": round(confidence, 3),
            }

        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            return {
                "answer": "",
                "sources": [],
                "confidence": 0.0,
                "error": str(e),
            }

    def query_with_filter(
        self,
        question: str,
        corpus_ids: list[str] | None = None,
        date_range: tuple[str, str] | None = None,
        top_k: int = RAG_TOP_K,
    ) -> dict[str, Any]:
        """Query with filtering by corpus ID or date range.

        Note: This is a placeholder for future implementation.
        Currently filters results after retrieval, which is not optimal.
        Future: Implement filtered retrieval at index level.

        Args:
            question: User's natural language question
            corpus_ids: List of corpus IDs to filter by
            date_range: Date range tuple (start_date, end_date)
            top_k: Number of documents to retrieve

        Returns:
            Query result dictionary
        """
        # Get initial results
        result = self.query(question, top_k=top_k * 2, include_sources=True)

        if corpus_ids:
            # Filter sources by corpus_ids
            filtered_sources = [
                s for s in result["sources"] if s["corpus_id"] in corpus_ids
            ]
            result["sources"] = filtered_sources[:top_k]

        if date_range:
            # Date filtering would require metadata with date fields
            # This is a placeholder for future implementation
            logger.warning("Date range filtering not yet implemented")

        return result


class RAGRouter:
    """Route queries to appropriate vector indices based on intent.

    Future enhancement: Implement multi-index routing based on query keywords.
    """

    INDICES = VECTOR_INDICES

    def route_query(self, question: str) -> list[str]:
        """Determine which indices to search based on query intent.

        Args:
            question: User's natural language question

        Returns:
            List of index names to search

        Examples:
            - "vendor contracts" -> ["corpus", "vicfm"]
            - "constitutional issues" -> ["corpus", "jim", "lexicon"]
            - "anomaly patterns" -> ["ace", "corpus"]
        """
        question_lower = question.lower()
        indices = ["corpus"]  # Always search main corpus

        # Add vendor/contract indices
        if any(
            kw in question_lower
            for kw in ["vendor", "contract", "procurement", "purchase"]
        ):
            indices.append("vicfm")

        # Add legal/constitutional indices
        if any(
            kw in question_lower
            for kw in ["legal", "constitutional", "amendment", "doctrine"]
        ):
            indices.extend(["jim", "lexicon"])

        # Add anomaly indices
        if any(kw in question_lower for kw in ["anomaly", "missing", "gap", "error"]):
            indices.append("ace")

        # Remove duplicates, preserve order
        seen = set()
        return [x for x in indices if not (x in seen or seen.add(x))]


__all__ = ["OracRAG", "RAGRouter"]
