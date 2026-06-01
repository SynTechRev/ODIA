"""CaliforniaCodeLoader — addressable California statute corpus.

Loads California code sections from a local JSON corpus directory with the
structure created by the Cal. code ingestion script (item 12 in the legal
corpus roadmap).

Expected directory layout::

    <corpus_root>/
        gov_code.json          — California Government Code
        pen_code.json          — California Penal Code
        civ_code.json          — California Civil Code
        ccp.json               — Code of Civil Procedure
        veh_code.json          — Vehicle Code
        health_safety_code.json
        welf_inst_code.json
        ...

Each JSON file has the schema::

    {
      "code_id":   "cal_gov_code",
      "code_name": "California Government Code",
      "source_url": "https://leginfo.legislature.ca.gov/...",
      "as_of":     "2025-01-01",
      "sections": [
        {
          "section": "7923.650",
          "title":   "Law enforcement investigative records",
          "text":    "A state or local agency... [full text]",
          "url":     "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?..."
        },
        ...
      ]
    }

If the corpus root does not exist or contains no files, initialize() returns
{} and all resolve() calls return None.  The loader degrades gracefully so the
backend starts without Cal. code data.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from odia_legal.citations.parser import parse_cal_code
from odia_legal.recodification.cpra_crosswalk import CPRACrosswalk
from oraculus_di_auditor.legal.corpus_base import CorpusLoader, LegalText

logger = logging.getLogger(__name__)

_CROSSWALK = CPRACrosswalk()


class CaliforniaCodeLoader(CorpusLoader):
    """Loads California code sections from the local JSON corpus."""

    corpus_id = "cal_codes"

    def __init__(self, submodule_path: Path | str):
        self._root = Path(submodule_path)
        # (code_id, section_number) → dict with title + text + url
        self._index: dict[tuple[str, str], dict] = {}
        # corpus_id → as_of date string
        self._as_of: dict[str, str] = {}
        self._initialized = False

    def initialize(self) -> dict[str, int]:
        """Scan corpus root and build section index. Returns count per code."""
        if not self._root.exists():
            logger.warning(
                "CaliforniaCodeLoader: corpus root not found at %s; "
                "Cal. code lookups disabled until corpus is ingested",
                self._root,
            )
            self._initialized = True
            return {}

        counts: dict[str, int] = {}
        for json_file in self._root.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping %s: %s", json_file.name, exc)
                continue

            code_id = data.get("code_id", json_file.stem)
            self._as_of[code_id] = data.get("as_of", "unknown")

            loaded = 0
            for entry in data.get("sections", []):
                section = str(entry.get("section", "")).strip()
                if not section:
                    continue
                self._index[(code_id, section)] = {
                    "title": entry.get("title", ""),
                    "text": entry.get("text", ""),
                    "url": entry.get("url"),
                    "source": str(json_file),
                }
                loaded += 1
            counts[code_id] = loaded
            logger.info("CaliforniaCodeLoader: %s — %d sections", code_id, loaded)

        self._initialized = True
        return counts

    def resolve_citation(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        """Resolve a California code citation to LegalText.

        Accepts either old-form (§ 6254(f)) or new-form (§ 7923.650) CPRA
        citations — the crosswalk normalizes to the new form before lookup.
        Returns None for unrecognized or uncached sections.
        """
        if not self._initialized:
            return None

        # Parse to a structured Citation
        cites = parse_cal_code(citation)
        if not cites:
            return None
        cite = cites[0]

        corpus_id = cite.corpus_id
        section = cite.section or ""

        # Normalize old-form CPRA citations to new form before lookup
        if corpus_id == "cal_gov_code":
            key_raw = f"{section}{cite.subdivision or ''}"
            new_sec = _CROSSWALK.to_new(key_raw)
            if new_sec:
                section = new_sec.split("(")[0]  # strip any subdivision

        entry = self._index.get((corpus_id, section))
        if entry is None:
            return None

        raw_cite = cite.canonical
        as_of_str = self._as_of.get(corpus_id, "unknown")

        return LegalText(
            corpus_id=corpus_id,
            citation=cite.canonical,
            citation_raw=raw_cite,
            title=entry["title"],
            text=entry["text"],
            source_path=entry["source"],
            source_commit=None,
            as_of=date.fromisoformat(as_of_str) if as_of_str != "unknown" else None,
            url=entry.get("url"),
            notes=f"Cal. code corpus as of {as_of_str}",
        )

    def search_text(self, query: str, limit: int = 10) -> list[LegalText]:
        """Simple substring search across all California code sections."""
        q = query.lower()
        results: list[LegalText] = []
        for (corpus_id, section), entry in self._index.items():
            if q in (entry["title"] + " " + entry["text"]).lower():
                results.append(
                    LegalText(
                        corpus_id=corpus_id,
                        citation=f"{corpus_id} § {section}",
                        citation_raw=f"{corpus_id} § {section}",
                        title=entry["title"],
                        text=entry["text"][:500],
                        source_path=entry["source"],
                        source_commit=None,
                        as_of=None,
                        url=entry.get("url"),
                        notes=None,
                    )
                )
            if len(results) >= limit:
                break
        return results

    def list_amendments(self, citation: str) -> list[dict]:
        """Cal. code corpus has no git history — returns empty list."""
        return []

    def statistics(self) -> dict[str, int]:
        """Return total and per-code section counts."""
        per_code: dict[str, int] = {}
        for corpus_id, _ in self._index:
            per_code[corpus_id] = per_code.get(corpus_id, 0) + 1
        return {"total_sections": len(self._index), **per_code}
