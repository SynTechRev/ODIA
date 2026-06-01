"""CFRLoader — addressable CFR corpus backed by data/legal_corpora/cfr/.

Loads Code of Federal Regulations sections from locally-ingested JSON files
(produced by scripts/ingest_cfr.py).  Same JSON schema as CaliforniaCodeLoader.

Resolution: 2 CFR § 200.303 → looks up (corpus_id="cfr_2_200", section="200.303").
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from odia_legal.citations.parser import parse_cfr
from oraculus_di_auditor.legal.corpus_base import CorpusLoader, LegalText

logger = logging.getLogger(__name__)


class CFRLoader(CorpusLoader):
    """Loads CFR sections from the local JSON corpus."""

    corpus_id = "cfr"

    def __init__(self, submodule_path: Path | str):
        self._root = Path(submodule_path)
        self._index: dict[tuple[str, str], dict] = {}
        self._as_of: dict[str, str] = {}
        self._initialized = False

    def initialize(self) -> dict[str, int]:
        if not self._root.exists():
            logger.warning(
                "CFRLoader: corpus root not found at %s; CFR lookups disabled",
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
            logger.info("CFRLoader: %s — %d sections", code_id, loaded)

        self._initialized = True
        return counts

    def resolve_citation(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        if not self._initialized:
            return None

        cites = parse_cfr(citation)
        if not cites:
            return None
        c = cites[0]

        # Map CFR title+part → corpus_id (e.g. title=2, § 200.303 → "cfr_2_200")
        # cfr_part is only set for "Part N" citations; for "§ N.NN" citations,
        # derive part from the section number prefix (e.g. "200.303" → "200").
        section = c.section or ""
        if c.cfr_part:
            part: str = c.cfr_part
        elif "." in section:
            part = section.split(".")[0]
        else:
            part = section
        corpus_id = f"cfr_{c.cfr_title}_{part}"

        entry = self._index.get((corpus_id, section))
        if entry is None:
            return None

        as_of_str = self._as_of.get(corpus_id, "unknown")
        return LegalText(
            corpus_id=corpus_id,
            citation=c.canonical,
            citation_raw=citation,
            title=entry["title"],
            text=entry["text"],
            source_path=entry["source"],
            source_commit=None,
            as_of=date.fromisoformat(as_of_str) if as_of_str != "unknown" else None,
            url=entry.get("url"),
            notes=f"CFR corpus as of {as_of_str}",
        )

    def search_text(self, query: str, limit: int = 10) -> list[LegalText]:
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
        return []

    def statistics(self) -> dict[str, int]:
        per_corpus: dict[str, int] = {}
        for corpus_id, _ in self._index:
            per_corpus[corpus_id] = per_corpus.get(corpus_id, 0) + 1
        return {"total_sections": len(self._index), **per_corpus}
