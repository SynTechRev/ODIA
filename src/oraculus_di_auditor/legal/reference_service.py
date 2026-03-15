"""Unified legal reference service for ODIA.

Single entry point for legal lookups across all reference sources:
case law, public domain dictionaries, Latin maxims, and
case-derived definitions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from oraculus_di_auditor.legal.case_law_builder import CaseLawBuilder, CaseLawRecord
from oraculus_di_auditor.legal.definition_extractor import (
    DefinitionExtractor,
)

# ---------------------------------------------------------------------------
# Supporting models
# ---------------------------------------------------------------------------


class DefinitionEntry(BaseModel):
    """A single definition from any legal reference source."""

    term: str
    definition: str
    source: str  # "bouvier_1856", "case_law", "wex_cornell", etc.
    source_detail: str  # Specific citation or page
    year: int | None = None
    authority_level: str  # "supreme_court", "dictionary_pd", "open_reference"


class TermLookupResult(BaseModel):
    """Results from a cross-source term lookup."""

    term: str
    found: bool
    definitions: list[DefinitionEntry]
    case_references: list[dict]  # Simplified case records
    related_terms: list[str]
    etymology: dict | None = None
    sources_searched: list[str]


class DoctrineLookupResult(BaseModel):
    """Results from a doctrine lookup."""

    doctrine: str
    found: bool
    key_cases: list[dict]
    current_standard: str
    evolution: list[dict]
    relevance_to_audit: str


# ---------------------------------------------------------------------------
# Authority level constants
# ---------------------------------------------------------------------------

_AUTHORITY_CASE_LAW = "supreme_court"
_AUTHORITY_PUBLIC_DOMAIN = "dictionary_pd"
_AUTHORITY_OPEN_REFERENCE = "open_reference"

# Dictionary source -> authority level
_DICT_AUTHORITY: dict[str, str] = {
    "bouvier_1856": _AUTHORITY_PUBLIC_DOMAIN,
    "anderson_1889": _AUTHORITY_PUBLIC_DOMAIN,
    "latin_foundational": _AUTHORITY_PUBLIC_DOMAIN,
    "wex_cornell": _AUTHORITY_OPEN_REFERENCE,
    "case_law_definitions": _AUTHORITY_CASE_LAW,
}

# Authority ranking for sorting (lower = higher authority)
_AUTHORITY_RANK: dict[str, int] = {
    _AUTHORITY_CASE_LAW: 0,
    _AUTHORITY_PUBLIC_DOMAIN: 1,
    _AUTHORITY_OPEN_REFERENCE: 2,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    """Return lowercase word tokens for simple keyword scoring."""
    return set(re.findall(r"[a-z]+", text.lower()))


def _keyword_score(query_tokens: set[str], text: str) -> float:
    """Count fraction of query tokens present in text."""
    if not query_tokens:
        return 0.0
    text_tokens = _tokenize(text)
    matches = query_tokens & text_tokens
    return len(matches) / len(query_tokens)


def _simplify_case(case: CaseLawRecord) -> dict:
    """Return a compact dict representation of a case for lookup results."""
    return {
        "case_id": case.case_id,
        "name": case.name,
        "citation": case.citation,
        "year": case.year,
        "court": case.court,
        "doctrine": case.doctrine,
        "holding": case.holding,
        "relevance_to_audit": case.relevance_to_audit,
    }


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------


class LegalReferenceService:
    """Unified search across all legal reference sources."""

    def __init__(self, legal_dir: Path | str = "legal") -> None:
        self.legal_dir = Path(legal_dir)
        self._cases: CaseLawBuilder | None = None
        self._definitions: DefinitionExtractor | None = None
        # Loaded dictionary terms: source_name -> list of raw term dicts
        self._dictionaries: dict[str, list[dict]] = {}
        self._initialized = False

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialize(self) -> dict[str, int]:
        """Load all legal reference data. Returns counts per source."""
        counts: dict[str, int] = {}

        # Case law
        cases_dir = self.legal_dir / "cases"
        self._cases = CaseLawBuilder(cases_dir)
        cases = self._cases.load_all_cases()
        counts["cases"] = len(cases)

        # Case-derived definitions
        self._definitions = DefinitionExtractor(self._cases)

        # Lexicon dictionaries
        lexicon_dir = self.legal_dir / "lexicon"
        dict_files = {
            "bouvier_1856": "bouvier_1856.json",
            "anderson_1889": "anderson_1889.json",
            "latin_foundational": "latin_foundational.json",
            "wex_cornell": "wex_cornell.json",
        }
        for key, filename in dict_files.items():
            path = lexicon_dir / filename
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                terms = data.get("terms", [])
                self._dictionaries[key] = terms
                counts[f"{key}_terms"] = len(terms)
            else:
                self._dictionaries[key] = []
                counts[f"{key}_terms"] = 0

        # Case-law-derived definitions file (pre-generated)
        cld_path = lexicon_dir / "case_law_definitions.json"
        if cld_path.exists():
            cld = json.loads(cld_path.read_text(encoding="utf-8"))
            n = cld.get("term_count", len(cld.get("terms", {})))
            counts["case_law_definitions"] = n

        self._initialized = True
        return counts

    # ------------------------------------------------------------------
    # Term lookup
    # ------------------------------------------------------------------

    def _lookup_in_dict(
        self,
        term_lower: str,
        src_key: str,
        terms_list: list[dict],
        authority: str,
    ) -> tuple[list[DefinitionEntry], list[str]]:
        """Look up a term in one dictionary source. Returns (definitions, related)."""
        definitions: list[DefinitionEntry] = []
        related: list[str] = []
        if src_key == "latin_foundational":
            for entry in terms_list:
                latin = entry.get("latin", "")
                translation = entry.get("translation", "")
                if term_lower in latin.lower() or term_lower in translation.lower():
                    definitions.append(
                        DefinitionEntry(
                            term=latin,
                            definition=entry.get("jurisprudential_usage", ""),
                            source=src_key,
                            source_detail=f"Translation: {translation}",
                            year=None,
                            authority_level=authority,
                        )
                    )
                    related.extend(entry.get("doctrinal_mapping", []))
        else:
            for entry in terms_list:
                entry_term = entry.get("term", "")
                if entry_term.lower() == term_lower:
                    definitions.append(
                        DefinitionEntry(
                            term=entry_term,
                            definition=entry.get("definition", ""),
                            source=src_key,
                            source_detail=entry.get("citation", ""),
                            year=None,
                            authority_level=authority,
                        )
                    )
        return definitions, related

    def lookup_term(self, term: str) -> TermLookupResult:
        """Look up a legal term across all sources."""
        self._ensure_initialized()
        term_lower = term.lower()
        definitions: list[DefinitionEntry] = []
        related: list[str] = []
        sources_searched: list[str] = []

        # 1. Case-law definitions (highest authority)
        all_case_defs = self._definitions.extract_all_definitions()  # type: ignore[union-attr]
        sources_searched.append("case_law_definitions")
        for key, defs in all_case_defs.items():
            if key.lower() == term_lower:
                for d in defs:
                    definitions.append(
                        DefinitionEntry(
                            term=d.term,
                            definition=d.definition,
                            source="case_law",
                            source_detail=f"{d.case_name}, {d.citation}",
                            year=d.year,
                            authority_level=_AUTHORITY_CASE_LAW,
                        )
                    )

        # 2. Public domain + open reference dictionaries
        for src_key, terms_list in self._dictionaries.items():
            sources_searched.append(src_key)
            authority = _DICT_AUTHORITY.get(src_key, _AUTHORITY_OPEN_REFERENCE)
            new_defs, new_related = self._lookup_in_dict(
                term_lower, src_key, terms_list, authority
            )
            definitions.extend(new_defs)
            related.extend(new_related)

        # Sort by authority rank, then recency (year desc)
        definitions.sort(
            key=lambda d: (
                _AUTHORITY_RANK.get(d.authority_level, 99),
                -(d.year or 0),
            )
        )

        # 3. Case references — cases with this term in issue_tags or holdings
        case_refs = self._find_case_references(term_lower)

        # Deduplicate related terms
        seen: set[str] = set()
        deduped_related: list[str] = []
        for r in related:
            if r not in seen:
                seen.add(r)
                deduped_related.append(r)

        # Etymology from Latin source if available
        etymology: dict | None = self._extract_etymology(term_lower)

        return TermLookupResult(
            term=term,
            found=bool(definitions or case_refs),
            definitions=definitions,
            case_references=case_refs,
            related_terms=deduped_related,
            etymology=etymology,
            sources_searched=list(dict.fromkeys(sources_searched)),
        )

    # ------------------------------------------------------------------
    # Doctrine lookup
    # ------------------------------------------------------------------

    def lookup_doctrine(self, doctrine: str) -> DoctrineLookupResult:
        """Look up a legal doctrine and its evolution."""
        self._ensure_initialized()
        doctrine_lower = doctrine.lower()

        cases = self._cases.search_by_doctrine(doctrine)  # type: ignore[union-attr]
        if not cases:
            return DoctrineLookupResult(
                doctrine=doctrine,
                found=False,
                key_cases=[],
                current_standard="",
                evolution=[],
                relevance_to_audit="",
            )

        # Sort chronologically
        cases_sorted = sorted(cases, key=lambda c: c.year)

        key_cases = [_simplify_case(c) for c in cases_sorted]

        # Evolution: one entry per case showing how holdings changed
        evolution = [
            {
                "year": c.year,
                "case": c.name,
                "citation": c.citation,
                "holding": c.holding,
            }
            for c in cases_sorted
            if c.holding
        ]

        # Most recent case's holding is the current standard
        current_standard = ""
        relevance = ""
        for c in reversed(cases_sorted):
            if c.holding:
                current_standard = f"{c.name} ({c.citation}): {c.holding}"
                relevance = c.relevance_to_audit
                break

        # Also scan wex/bouvier for doctrine descriptions
        if not relevance:
            for terms_list in self._dictionaries.values():
                for entry in terms_list:
                    category = entry.get("category", "")
                    if doctrine_lower.replace("_", " ") in category.replace("_", " "):
                        relevance = entry.get("definition", "")[:200]
                        if relevance:
                            break
                if relevance:
                    break

        return DoctrineLookupResult(
            doctrine=doctrine,
            found=True,
            key_cases=key_cases,
            current_standard=current_standard,
            evolution=evolution,
            relevance_to_audit=relevance,
        )

    # ------------------------------------------------------------------
    # Free-text search (private helpers)
    # ------------------------------------------------------------------

    def _search_dicts(self, query_tokens: set[str]) -> list[tuple[float, dict]]:
        """Score all dictionary entries against query_tokens."""
        results: list[tuple[float, dict]] = []
        for src_key, terms_list in self._dictionaries.items():
            authority = _DICT_AUTHORITY.get(src_key, _AUTHORITY_OPEN_REFERENCE)
            for entry in terms_list:
                if src_key == "latin_foundational":
                    text = " ".join(
                        filter(
                            None,
                            [
                                entry.get("latin", ""),
                                entry.get("translation", ""),
                                entry.get("jurisprudential_usage", ""),
                            ],
                        )
                    )
                    term_label = entry.get("latin", "")
                    definition = entry.get("jurisprudential_usage", "")
                else:
                    text = " ".join(
                        filter(
                            None,
                            [entry.get("term", ""), entry.get("definition", "")],
                        )
                    )
                    term_label = entry.get("term", "")
                    definition = entry.get("definition", "")

                score = _keyword_score(query_tokens, text)
                if score > 0:
                    results.append(
                        (
                            score,
                            {
                                "source_type": "legal_dictionary",
                                "document_id": f"{src_key}__{term_label}",
                                "title": f"{term_label} ({src_key})",
                                "content": definition,
                                "score": score,
                                "metadata": {
                                    "source": src_key,
                                    "authority_level": authority,
                                },
                            },
                        )
                    )
        return results

    def _search_case_definitions(
        self, query_tokens: set[str]
    ) -> list[tuple[float, dict]]:
        """Score case-derived definitions against query_tokens."""
        results: list[tuple[float, dict]] = []
        all_defs = self._definitions.extract_all_definitions()  # type: ignore[union-attr]
        for term, defs in all_defs.items():
            best = defs[-1] if defs else None
            if best:
                text = f"{term} {best.definition} {best.case_name}"
                score = _keyword_score(query_tokens, text)
                if score > 0:
                    results.append(
                        (
                            score,
                            {
                                "source_type": "case_law_definition",
                                "document_id": f"case_def__{term}",
                                "title": f"Case-Law Definition: {term}",
                                "content": best.definition,
                                "score": score,
                                "metadata": {
                                    "term": term,
                                    "case_name": best.case_name,
                                    "year": best.year,
                                    "authority_level": _AUTHORITY_CASE_LAW,
                                },
                            },
                        )
                    )
        return results

    # ------------------------------------------------------------------
    # Free-text search (public)
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Free-text keyword search across all legal reference data."""
        self._ensure_initialized()
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        candidates: list[tuple[float, dict]] = []

        # Search case summaries / holdings
        for case in self._cases.load_all_cases():  # type: ignore[union-attr]
            text = " ".join(
                filter(None, [case.name, case.summary, case.holding, case.doctrine])
            )
            score = _keyword_score(query_tokens, text)
            if score > 0:
                candidates.append(
                    (
                        score,
                        {
                            "source_type": "case_law",
                            "document_id": case.case_id,
                            "title": f"{case.name} ({case.citation})",
                            "content": case.summary or case.holding,
                            "score": score,
                            "metadata": {
                                "case_id": case.case_id,
                                "year": case.year,
                                "doctrine": case.doctrine,
                            },
                        },
                    )
                )

        # Search dictionaries and case-derived definitions
        candidates.extend(self._search_dicts(query_tokens))
        candidates.extend(self._search_case_definitions(query_tokens))

        # Sort descending by score, deduplicate by document_id
        candidates.sort(key=lambda x: x[0], reverse=True)
        seen_ids: set[str] = set()
        results: list[dict] = []
        for _score, entry in candidates:
            did = entry["document_id"]
            if did not in seen_ids:
                seen_ids.add(did)
                results.append(entry)
            if len(results) >= top_k:
                break

        return results

    # ------------------------------------------------------------------
    # RAG export
    # ------------------------------------------------------------------

    def export_all_for_rag(self) -> list[dict]:
        """Export entire legal reference dataset in RAG-indexable format."""
        self._ensure_initialized()
        chunks: list[dict] = []

        # Case law chunks (main, definitions, quotes)
        chunks.extend(self._cases.export_for_rag())  # type: ignore[union-attr]

        # Case-derived definition chunks
        chunks.extend(self._definitions.export_for_rag())  # type: ignore[union-attr]

        # Dictionary chunks — one chunk per term
        for src_key, terms_list in self._dictionaries.items():
            authority = _DICT_AUTHORITY.get(src_key, _AUTHORITY_OPEN_REFERENCE)
            for entry in terms_list:
                if src_key == "latin_foundational":
                    term_label = entry.get("latin", "")
                    definition = entry.get("jurisprudential_usage", "")
                    content_parts = [
                        f"Term: {term_label}",
                        f"Translation: {entry.get('translation', '')}",
                        f"Usage: {definition}",
                    ]
                    if entry.get("relevance_to_audit"):
                        content_parts.append(
                            f"Audit relevance: {entry['relevance_to_audit']}"
                        )
                else:
                    term_label = entry.get("term", "")
                    definition = entry.get("definition", "")
                    content_parts = [
                        f"Term: {term_label}",
                        f"Definition: {definition}",
                    ]
                    if entry.get("citation"):
                        content_parts.append(f"Citation: {entry['citation']}")

                if not term_label or not definition:
                    continue

                chunks.append(
                    {
                        "document_id": (
                            f"{src_key}__{term_label.lower().replace(' ', '_')}"
                        ),
                        "title": f"{term_label} ({src_key})",
                        "content": "\n".join(content_parts),
                        "source_type": "legal_dictionary",
                        "metadata": {
                            "source": src_key,
                            "term": term_label,
                            "category": entry.get("category", ""),
                            "authority_level": authority,
                            "chunk_type": "dictionary_entry",
                        },
                    }
                )

        return chunks

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> dict[str, Any]:
        """Return coverage statistics for the legal reference dataset."""
        self._ensure_initialized()
        all_case_defs = self._definitions.extract_all_definitions()  # type: ignore[union-attr]
        cases = self._cases.load_all_cases()  # type: ignore[union-attr]
        doctrine_index = self._cases.build_doctrine_index()  # type: ignore[union-attr]

        dict_term_counts = {k: len(v) for k, v in self._dictionaries.items()}
        total_dict_terms = sum(dict_term_counts.values())

        return {
            "cases": len(cases),
            "doctrines_covered": len(doctrine_index),
            "case_law_definitions": len(all_case_defs),
            "dictionary_sources": len(self._dictionaries),
            "dictionary_terms": dict_term_counts,
            "total_dictionary_terms": total_dict_terms,
            "total_rag_chunks": len(self.export_all_for_rag()),
            "sources": list(self._dictionaries.keys()) + ["case_law"],
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    def _find_case_references(self, term_lower: str) -> list[dict]:
        """Find cases that reference a term in issue_tags or holdings."""
        results: list[dict] = []
        for case in self._cases.load_all_cases():  # type: ignore[union-attr]
            tag_match = any(term_lower in t.lower() for t in case.issue_tags)
            holding_match = term_lower in (case.holding or "").lower()
            summary_match = term_lower in (case.summary or "").lower()
            if tag_match or holding_match or summary_match:
                results.append(_simplify_case(case))
        return results

    def _extract_etymology(self, term_lower: str) -> dict | None:
        """Return etymology info from Latin lexicon if the term appears there."""
        latin_terms = self._dictionaries.get("latin_foundational", [])
        for entry in latin_terms:
            latin = entry.get("latin", "")
            translation = entry.get("translation", "")
            if term_lower in latin.lower() or term_lower in translation.lower():
                return {
                    "latin": latin,
                    "translation": translation,
                    "origin_language": entry.get("origin_language", "Latin"),
                }
        # Check origin_language in other dicts
        for src_key, terms_list in self._dictionaries.items():
            if src_key == "latin_foundational":
                continue
            for entry in terms_list:
                if entry.get("term", "").lower() == term_lower:
                    lang = entry.get("origin_language", "")
                    if lang and lang.lower() != "english":
                        return {"origin_language": lang}
        return None
