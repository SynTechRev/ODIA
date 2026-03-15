"""Case-law-derived legal definition extractor for ODIA.

Extracts authoritative legal definitions from Supreme Court holdings,
building a case-law dictionary that supplements static lexicon sources.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from oraculus_di_auditor.legal.case_law_builder import CaseLawBuilder, CaseLawRecord


class CaseDefinition(BaseModel):
    """A legal term definition extracted from a court opinion."""

    term: str
    definition: str
    case_name: str
    citation: str
    year: int
    court: str
    context: str = ""  # Legal question that prompted the definition
    is_holding: bool = True  # Definition from holding vs. dicta
    superseded_by: str | None = None  # Later case that redefined the term


class CaseLawDictionary(BaseModel):
    """Complete dictionary built from case-law definitions."""

    version: str
    generated_at: str
    source: str = "ODIA Case Law Definition Extractor"
    description: str = "Legal definitions extracted from public domain court opinions"
    term_count: int
    case_count: int
    terms: dict[str, CaseDefinition]  # term -> authoritative definition
    all_definitions: dict[str, list[CaseDefinition]]  # term -> all definitions


# Cases where a later ruling superseded a definition from an earlier case.
# Maps earlier_case_id -> {term -> superseding_case_citation}.
_SUPERSEDED_BY: dict[str, dict[str, str]] = {
    "auer_v_robbins_1997": {
        "Auer deference": "Kisor v. Wilkie, 588 U.S. 558 (2019)",
    },
    "chevron_usa_v_natural_resources_defense_council_1984": {
        "Chevron deference": (
            "Loper Bright Enterprises v. Raimondo, 603 U.S. ___ (2024)"
        ),
    },
    "panama_refining_co_v_ryan_1935": {
        "intelligible principle": ("Mistretta v. United States, 488 U.S. 361 (1989)"),
    },
}


def _case_to_definitions(case: CaseLawRecord) -> list[CaseDefinition]:
    """Convert a CaseLawRecord's LegalDefinition list to CaseDefinition objects."""
    results: list[CaseDefinition] = []
    superseded = _SUPERSEDED_BY.get(case.case_id, {})
    for ld in case.legal_definitions:
        results.append(
            CaseDefinition(
                term=ld.term,
                definition=ld.definition,
                case_name=case.name,
                citation=case.citation,
                year=case.year,
                court=case.court,
                context=ld.context,
                is_holding=ld.binding_authority,
                superseded_by=superseded.get(ld.term),
            )
        )
    return results


class DefinitionExtractor:
    """Extracts legal definitions from case law holdings."""

    def __init__(self, case_builder: CaseLawBuilder) -> None:
        self.case_builder = case_builder

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_all_definitions(self) -> dict[str, list[CaseDefinition]]:
        """Extract all definitions from all loaded cases.

        Returns dict mapping term -> list of definitions from different cases.
        When multiple cases define the same term, all definitions are preserved
        with their case citations, allowing the user to see how the definition
        evolved over time.
        """
        result: dict[str, list[CaseDefinition]] = {}
        for case in self.case_builder.load_all_cases():
            for defn in _case_to_definitions(case):
                result.setdefault(defn.term, []).append(defn)
        # Sort each list chronologically
        for defs in result.values():
            defs.sort(key=lambda d: d.year)
        return result

    def get_authoritative_definition(self, term: str) -> CaseDefinition | None:
        """Get the most authoritative definition for a term.

        Priority:
        1. Most recent SCOTUS case defining the term
        2. Most relevant to ODIA's audit context (holding, not dicta)
        3. Most recent case of any court
        """
        all_defs = self.extract_all_definitions()
        candidates = all_defs.get(term.lower()) or all_defs.get(term)
        if not candidates:
            # Case-insensitive fallback
            term_lower = term.lower()
            for key, defs in all_defs.items():
                if key.lower() == term_lower:
                    candidates = defs
                    break
        if not candidates:
            return None

        # Priority 1: most recent SCOTUS holding (not superseded)
        scotus_holdings = [
            d
            for d in candidates
            if d.court.upper() in ("SCOTUS", "US SUPREME COURT")
            and d.is_holding
            and d.superseded_by is None
        ]
        if scotus_holdings:
            return max(scotus_holdings, key=lambda d: d.year)

        # Priority 2: any SCOTUS definition (not superseded)
        scotus_any = [
            d
            for d in candidates
            if d.court.upper() in ("SCOTUS", "US SUPREME COURT")
            and d.superseded_by is None
        ]
        if scotus_any:
            return max(scotus_any, key=lambda d: d.year)

        # Priority 3: most recent holding from any court (not superseded)
        holdings = [d for d in candidates if d.is_holding and d.superseded_by is None]
        if holdings:
            return max(holdings, key=lambda d: d.year)

        # Fallback: most recent definition of any kind
        return max(candidates, key=lambda d: d.year)

    def build_case_law_dictionary(self) -> CaseLawDictionary:
        """Build a complete dictionary from case law definitions.

        Returns CaseLawDictionary with:
        - terms: dict mapping term -> authoritative definition
        - all_definitions: dict mapping term -> list of all definitions
        - term_count / case_count coverage stats
        - generated_at timestamp
        """
        all_defs = self.extract_all_definitions()
        authoritative: dict[str, CaseDefinition] = {}
        for term in all_defs:
            best = self.get_authoritative_definition(term)
            if best is not None:
                authoritative[term] = best

        case_ids: set[str] = set()
        for defs in all_defs.values():
            for d in defs:
                case_ids.add(d.citation)

        return CaseLawDictionary(
            version="1.0.0",
            generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            term_count=len(authoritative),
            case_count=len(case_ids),
            terms=authoritative,
            all_definitions=all_defs,
        )

    def export_for_rag(self) -> list[dict[str, Any]]:
        """Export definitions in RAG-indexable format.

        Each term produces one chunk with full definition metadata.
        """
        dictionary = self.build_case_law_dictionary()
        chunks: list[dict[str, Any]] = []
        for term, defn in dictionary.terms.items():
            content_parts = [
                f"Term: {defn.term}",
                f"Definition: {defn.definition}",
                f"Source: {defn.case_name} ({defn.citation})",
            ]
            if defn.context:
                content_parts.append(f"Context: {defn.context}")
            if defn.superseded_by:
                content_parts.append(f"Note: superseded by {defn.superseded_by}")

            chunks.append(
                {
                    "document_id": f"case_def__{term.lower().replace(' ', '_')}",
                    "title": f"Case-Law Definition: {defn.term}",
                    "content": "\n".join(content_parts),
                    "source_type": "case_law_definition",
                    "metadata": {
                        "term": defn.term,
                        "case_name": defn.case_name,
                        "citation": defn.citation,
                        "year": defn.year,
                        "court": defn.court,
                        "is_holding": defn.is_holding,
                        "superseded_by": defn.superseded_by,
                        "chunk_type": "case_law_definition",
                    },
                }
            )
        return chunks
