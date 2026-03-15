"""Case law dataset builder for ODIA legal reference corpus.

Manages structured case records from public domain court opinions,
with indexing and RAG export capabilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class LegalDefinition(BaseModel):
    """A legal term defined authoritatively in a case holding."""

    term: str
    definition: str
    context: str = ""
    pinpoint_citation: str = ""
    binding_authority: bool = True


class KeyQuote(BaseModel):
    """A short quotation from the opinion (fair use — under 50 words)."""

    text: str
    pinpoint_citation: str = ""
    context: str = ""

    @field_validator("text")
    @classmethod
    def text_under_50_words(cls, v: str) -> str:
        words = v.split()
        if len(words) > 50:
            raise ValueError(
                f"Quote must be under 50 words for fair use; got {len(words)}"
            )
        return v


class CaseLawRecord(BaseModel):
    """Structured representation of a court case for ODIA analysis."""

    case_id: str
    name: str
    citation: str = ""
    year: int = 0
    court: str = "SCOTUS"
    doctrine: str = ""
    secondary_doctrines: list[str] = []
    summary: str = ""
    holding: str = ""
    legal_definitions: list[LegalDefinition] = []
    issue_tags: list[str] = []
    constitutional_basis: list[str] = []
    relevance_to_audit: str = ""
    key_quotes: list[KeyQuote] = []
    procedural_posture: str = ""
    vote: str = ""
    majority_author: str = ""
    dissent_authors: list[str] = []
    subsequent_treatment: str = ""
    source_url: str = ""

    model_config = {"extra": "allow"}

    @model_validator(mode="before")
    @classmethod
    def coerce_constitutional_basis(cls, data: Any) -> Any:
        """Accept constitutional_basis as str or list."""
        if isinstance(data, dict):
            cb = data.get("constitutional_basis")
            if isinstance(cb, str) and cb:
                data = dict(data)
                data["constitutional_basis"] = [cb]
            elif cb is None:
                data = dict(data)
                data["constitutional_basis"] = []
        return data


class CaseLawBuilder:
    """Builds and manages the case law reference dataset."""

    def __init__(self, cases_dir: Path | str = "legal/cases"):
        self.cases_dir = Path(cases_dir)

    def _is_case_file(self, path: Path) -> bool:
        """Return True if the file is a case record (not an index/meta file)."""
        skip = {
            "SCOTUS_INDEX",
            "CASE_LAW_EXPANSION_INDEX",
            "CLEP_CORRELATION_GRAPH",
            "JIM_CASE_EXPANSION_V2",
        }
        return path.suffix == ".json" and path.stem not in skip

    def load_all_cases(self) -> list[CaseLawRecord]:
        """Load all case files from the cases directory."""
        records: list[CaseLawRecord] = []
        if not self.cases_dir.exists():
            return records
        for path in sorted(self.cases_dir.glob("*.json")):
            if not self._is_case_file(path):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                records.append(CaseLawRecord.model_validate(data))
            except Exception:
                continue
        return records

    def save_case(self, case: CaseLawRecord) -> Path:
        """Save a case record to JSON file."""
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        path = self.cases_dir / f"{case.case_id}.json"
        path.write_text(
            case.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )
        return path

    def search_by_doctrine(self, doctrine: str) -> list[CaseLawRecord]:
        """Find cases by primary or secondary doctrinal category."""
        doctrine_lower = doctrine.lower()
        return [
            c
            for c in self.load_all_cases()
            if c.doctrine.lower() == doctrine_lower
            or doctrine_lower in [d.lower() for d in c.secondary_doctrines]
        ]

    def search_by_tag(self, tag: str) -> list[CaseLawRecord]:
        """Find cases by issue tag."""
        tag_lower = tag.lower()
        return [
            c
            for c in self.load_all_cases()
            if tag_lower in [t.lower() for t in c.issue_tags]
        ]

    def get_definitions_for_term(self, term: str) -> list[LegalDefinition]:
        """Get all case-law definitions for a legal term."""
        term_lower = term.lower()
        definitions: list[LegalDefinition] = []
        for case in self.load_all_cases():
            for defn in case.legal_definitions:
                if defn.term.lower() == term_lower:
                    definitions.append(defn)
        return definitions

    def build_doctrine_index(self) -> dict[str, list[str]]:
        """Build index: doctrine -> list of case_ids."""
        index: dict[str, list[str]] = {}
        for case in self.load_all_cases():
            if case.doctrine:
                index.setdefault(case.doctrine, []).append(case.case_id)
            for doc in case.secondary_doctrines:
                index.setdefault(doc, []).append(case.case_id)
        return index

    def build_definition_index(self) -> dict[str, list[LegalDefinition]]:
        """Build index: term -> list of definitions from case law."""
        index: dict[str, list[LegalDefinition]] = {}
        for case in self.load_all_cases():
            for defn in case.legal_definitions:
                index.setdefault(defn.term, []).append(defn)
        return index

    def export_for_rag(self) -> list[dict]:
        """Export case law in a format optimized for RAG indexing.

        Each case produces 1–3 chunks: summary/holding, definitions, quotes.
        """
        chunks: list[dict] = []
        for case in self.load_all_cases():
            base_meta = {
                "case_id": case.case_id,
                "name": case.name,
                "citation": case.citation,
                "year": case.year,
                "court": case.court,
                "doctrine": case.doctrine,
                "issue_tags": case.issue_tags,
            }

            # Chunk 1: summary + holding
            body_parts = []
            if case.summary:
                body_parts.append(f"Summary: {case.summary}")
            if case.holding:
                body_parts.append(f"Holding: {case.holding}")
            if case.relevance_to_audit:
                body_parts.append(f"Relevance: {case.relevance_to_audit}")
            if body_parts:
                chunks.append(
                    {
                        "document_id": f"{case.case_id}__main",
                        "title": f"{case.name} ({case.citation})",
                        "content": "\n".join(body_parts),
                        "source_type": "case_law",
                        "metadata": {**base_meta, "chunk_type": "main"},
                    }
                )

            # Chunk 2: legal definitions (if any)
            if case.legal_definitions:
                defn_lines = [
                    f"{d.term}: {d.definition}" for d in case.legal_definitions
                ]
                chunks.append(
                    {
                        "document_id": f"{case.case_id}__definitions",
                        "title": f"{case.name} — Legal Definitions",
                        "content": "\n".join(defn_lines),
                        "source_type": "case_law",
                        "metadata": {**base_meta, "chunk_type": "definitions"},
                    }
                )

            # Chunk 3: key quotes (if any)
            if case.key_quotes:
                quote_lines = [
                    f'"{q.text}" ({q.pinpoint_citation})' for q in case.key_quotes
                ]
                chunks.append(
                    {
                        "document_id": f"{case.case_id}__quotes",
                        "title": f"{case.name} — Key Quotes",
                        "content": "\n".join(quote_lines),
                        "source_type": "case_law",
                        "metadata": {**base_meta, "chunk_type": "quotes"},
                    }
                )

        return chunks
