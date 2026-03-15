"""Enhanced retrieval engine for multi-source RAG queries.

Searches across document corpus, analysis results, and audit findings —
not just raw document text.

Author: ODIA Team
Date: 2026-03-14
"""

from __future__ import annotations

import hashlib
from typing import Any

from oraculus_di_auditor.embeddings import LocalEmbedder
from oraculus_di_auditor.rag.models import RetrievalResult
from oraculus_di_auditor.retriever import Retriever


def _stable_id(obj: dict, prefix: str) -> str:
    """Generate a stable ID from dict content."""
    raw = str(sorted(obj.items()))
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def _text_for_document(doc: dict) -> str:
    """Extract searchable text from a document dict."""
    parts: list[str] = []
    for key in ("text", "content", "body", "title", "summary"):
        if key in doc and doc[key]:
            parts.append(str(doc[key]))
    return " ".join(parts) if parts else str(doc)


def _text_for_finding(finding: dict) -> str:
    """Extract searchable text from a finding dict."""
    parts: list[str] = []
    for key in ("issue", "details", "layer", "severity", "id"):
        val = finding.get(key)
        if val:
            parts.append(str(val) if not isinstance(val, dict) else str(val))
    return " ".join(parts) if parts else str(finding)


def _text_for_analysis(result: dict) -> str:
    """Extract searchable text from an analysis result dict."""
    parts: list[str] = []
    for key in ("summary", "description", "result", "findings", "title"):
        val = result.get(key)
        if val:
            parts.append(
                str(val) if not isinstance(val, list) else " ".join(str(v) for v in val)
            )
    return " ".join(parts) if parts else str(result)


class RetrievalEngine:
    """Multi-source retrieval for RAG queries.

    Indexes and searches across documents, audit findings, and analysis
    results using TF-IDF embeddings and cosine similarity.
    """

    def __init__(
        self,
        embedder: LocalEmbedder | None = None,
        retriever: Retriever | None = None,
    ):
        """Initialize with existing embedder/retriever or create new ones."""
        self._embedder = embedder or LocalEmbedder(max_features=512)
        self._retriever = retriever or Retriever()
        self._documents: list[dict] = []
        self._findings: list[dict] = []
        self._analysis_results: list[dict] = []
        self._corpus_texts: list[str] = []
        self._entry_map: list[dict[str, Any]] = []
        self._fitted = False

    def _refit(self) -> None:
        """Refit the embedder on the full corpus and rebuild the retriever."""
        if not self._corpus_texts:
            return
        self._embedder.fit(self._corpus_texts)
        self._fitted = True
        self._retriever.vectors.clear()
        self._retriever.metadata.clear()
        for i, text in enumerate(self._corpus_texts):
            vec = self._embedder.embed(text)
            self._retriever.add_vector(vec, self._entry_map[i])

    def index_documents(self, documents: list[dict]) -> int:
        """Index documents for retrieval. Returns count indexed."""
        for doc in documents:
            doc_id = doc.get("id", doc.get("document_id", _stable_id(doc, "doc")))
            text = _text_for_document(doc)
            self._documents.append(doc)
            self._corpus_texts.append(text)
            self._entry_map.append(
                {
                    "source_type": "document",
                    "source_id": str(doc_id),
                    "content": text,
                    "original": doc,
                }
            )
        self._refit()
        return len(documents)

    def index_findings(self, findings: list[dict]) -> int:
        """Index audit findings for retrieval."""
        for finding in findings:
            fid = finding.get("id", _stable_id(finding, "finding"))
            text = _text_for_finding(finding)
            self._findings.append(finding)
            self._corpus_texts.append(text)
            self._entry_map.append(
                {
                    "source_type": "finding",
                    "source_id": str(fid),
                    "content": text,
                    "original": finding,
                }
            )
        self._refit()
        return len(findings)

    def index_analysis_results(self, results: list[dict]) -> int:
        """Index analysis results for retrieval."""
        for result in results:
            rid = result.get("id", _stable_id(result, "analysis"))
            text = _text_for_analysis(result)
            self._analysis_results.append(result)
            self._corpus_texts.append(text)
            self._entry_map.append(
                {
                    "source_type": "analysis",
                    "source_id": str(rid),
                    "content": text,
                    "original": result,
                }
            )
        self._refit()
        return len(results)

    def index_legal_references(self, chunks: list[dict]) -> int:
        """Index legal reference chunks (case law, dictionaries) for retrieval.

        Accepts the output of LegalReferenceService.export_all_for_rag().
        Returns count indexed.
        """
        for chunk in chunks:
            doc_id = chunk.get("document_id", _stable_id(chunk, "legal"))
            text = " ".join(
                filter(
                    None,
                    [
                        chunk.get("title", ""),
                        chunk.get("content", ""),
                    ],
                )
            )
            self._corpus_texts.append(text)
            self._entry_map.append(
                {
                    "source_type": chunk.get("source_type", "legal_reference"),
                    "source_id": str(doc_id),
                    "content": text,
                    "original": chunk,
                }
            )
        self._refit()
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[RetrievalResult]:
        """Search across all indexed sources.

        Args:
            query: Natural language search query
            top_k: Max results to return
            source_filter: Limit to "documents", "findings", or "analysis"

        Returns:
            RetrievalResult objects sorted by score descending.
        """
        if not self._fitted:
            return []

        query_vec = self._embedder.embed(query)
        raw = self._retriever.search(query_vec, top_k=len(self._corpus_texts))

        results: list[RetrievalResult] = []
        type_map = {
            "documents": "document",
            "findings": "finding",
            "analysis": "analysis",
        }
        filter_type = (
            type_map.get(source_filter, source_filter) if source_filter else None
        )

        for _idx, score, meta in raw:
            if filter_type and meta.get("source_type") != filter_type:
                continue
            results.append(
                RetrievalResult(
                    content=meta["content"],
                    source_type=meta["source_type"],
                    source_id=meta["source_id"],
                    score=score,
                    metadata={
                        k: v
                        for k, v in meta.get("original", {}).items()
                        if k != "content"
                    },
                )
            )
            if len(results) >= top_k:
                break

        return results

    def search_by_detector(
        self, detector_name: str, top_k: int = 5
    ) -> list[RetrievalResult]:
        """Retrieve findings from a specific detector."""
        matches: list[RetrievalResult] = []
        for finding in self._findings:
            if finding.get("layer") == detector_name:
                fid = finding.get("id", _stable_id(finding, "finding"))
                matches.append(
                    RetrievalResult(
                        content=_text_for_finding(finding),
                        source_type="finding",
                        source_id=str(fid),
                        score=1.0,
                        metadata={k: v for k, v in finding.items() if k != "content"},
                    )
                )
                if len(matches) >= top_k:
                    break
        return matches

    def search_by_severity(
        self, severity: str, top_k: int = 5
    ) -> list[RetrievalResult]:
        """Retrieve findings of a specific severity level."""
        matches: list[RetrievalResult] = []
        for finding in self._findings:
            if finding.get("severity") == severity:
                fid = finding.get("id", _stable_id(finding, "finding"))
                matches.append(
                    RetrievalResult(
                        content=_text_for_finding(finding),
                        source_type="finding",
                        source_id=str(fid),
                        score=1.0,
                        metadata={k: v for k, v in finding.items() if k != "content"},
                    )
                )
                if len(matches) >= top_k:
                    break
        return matches
