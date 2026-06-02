"""MultiStateCodeLoader — public records law corpus for OR, WA, and TX.

Loads state public records statutes from a local JSON corpus directory using
the same file format as CaliforniaCodeLoader.

Supported states and their public records acts:

  Oregon  — Oregon Public Records Law (ORS Chapter 192)
  Washington — Washington Public Records Act (RCW Chapter 42.56)
  Texas   — Texas Public Information Act (Gov. Code Chapter 552)

Expected directory layout::

    <corpus_root>/
        oregon_ors192.json
        washington_rcw4256.json
        texas_gc552.json

Each JSON file has the schema::

    {
      "state":       "oregon",
      "code_id":     "or_pub_records",
      "code_name":   "Oregon Public Records Law (ORS Ch. 192)",
      "source_url":  "https://www.oregonlegislature.gov/...",
      "as_of":       "2025-01-01",
      "sections": [
        {
          "section": "192.311",
          "title":   "Definitions",
          "text":    "As used in ORS 192.311 to 192.478...",
          "url":     "https://..."
        },
        ...
      ]
    }

Citation resolution accepts all of:
  ORS 192.311           — Oregon Revised Statutes
  RCW 42.56.070         — Revised Code of Washington
  Tex. Gov. Code § 552.001   — Texas Government Code
  Gov't Code § 552.001  — (alternate Texas form)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path

from oraculus_di_auditor.legal.corpus_base import CorpusLoader, LegalText

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Citation parsing regexes per state
# ---------------------------------------------------------------------------

_ORS_RE = re.compile(
    r"\bORS\s+(?:§\s*)?(?P<section>\d+\.\d+(?:\(\d+\))*)",
    re.IGNORECASE,
)

_RCW_RE = re.compile(
    r"\bRCW\s+(?:§\s*)?(?P<section>\d+\.\d+\.\d+(?:\(\d+\))*)",
    re.IGNORECASE,
)

_TEX_RE = re.compile(
    r"\b(?:Tex(?:as)?\.?\s+Gov(?:ernment|'?t)?\.?\s+Code|Gov(?:ernment|'?t)?\.?\s+Code\s+Ann\.?)"
    r"\s+(?:§\s*)?(?P<section>5\d{2}\.\d+(?:\(\w+\))*)",
    re.IGNORECASE,
)

# State → corpus_id mapping
_STATE_CORPUS_IDS = {
    "oregon": "or_pub_records",
    "washington": "wa_pub_records",
    "texas": "tx_pub_info",
}

# corpus_id → state
_CORPUS_ID_STATE = {v: k for k, v in _STATE_CORPUS_IDS.items()}


def _parse_ors(citation: str) -> str | None:
    m = _ORS_RE.search(citation)
    return m.group("section").split("(")[0] if m else None


def _parse_rcw(citation: str) -> str | None:
    m = _RCW_RE.search(citation)
    return m.group("section").split("(")[0] if m else None


def _parse_tex(citation: str) -> str | None:
    m = _TEX_RE.search(citation)
    return m.group("section").split("(")[0] if m else None


class MultiStateCodeLoader(CorpusLoader):
    """Loads public records statutes for Oregon, Washington, and Texas."""

    corpus_id = "multistate_pub_records"

    def __init__(self, submodule_path: Path | str):
        self._root = Path(submodule_path)
        # (corpus_id, section_number) → {title, text, url, source}
        self._index: dict[tuple[str, str], dict] = {}
        # corpus_id → as_of date string
        self._as_of: dict[str, str] = {}
        # corpus_id → code_name
        self._names: dict[str, str] = {}
        self._initialized = False

    def initialize(self) -> dict[str, int]:
        """Scan corpus root and build section index. Returns count per code."""
        if not self._root.exists():
            logger.warning(
                "MultiStateCodeLoader: corpus root not found at %s; "
                "multi-state lookups disabled until corpus is ingested",
                self._root,
            )
            self._initialized = True
            return {}

        counts: dict[str, int] = {}
        for json_file in sorted(self._root.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping %s: %s", json_file.name, exc)
                continue

            state = data.get("state", "").lower()
            code_id = _STATE_CORPUS_IDS.get(state, data.get("code_id", json_file.stem))
            self._as_of[code_id] = data.get("as_of", "unknown")
            self._names[code_id] = data.get("code_name", code_id)

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
            logger.info(
                "MultiStateCodeLoader: %s (%s) — %d sections", code_id, state, loaded
            )

        self._initialized = True
        return counts

    def resolve_citation(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        """Resolve a state public records citation string to LegalText.

        Recognizes ORS, RCW, and Texas Government Code citation forms.
        Returns None for unrecognized or uncached sections.
        """
        if not self._initialized:
            return None

        # Determine state and section from citation
        corpus_id: str | None = None
        section: str | None = None
        canonical: str | None = None

        ors_sec = _parse_ors(citation)
        if ors_sec:
            corpus_id = "or_pub_records"
            section = ors_sec
            canonical = f"ORS § {section}"

        if corpus_id is None:
            rcw_sec = _parse_rcw(citation)
            if rcw_sec:
                corpus_id = "wa_pub_records"
                section = rcw_sec
                canonical = f"RCW § {section}"

        if corpus_id is None:
            tex_sec = _parse_tex(citation)
            if tex_sec:
                corpus_id = "tx_pub_info"
                section = tex_sec
                canonical = f"Tex. Gov't Code § {section}"

        if corpus_id is None or section is None:
            return None

        entry = self._index.get((corpus_id, section))
        if entry is None:
            return None

        as_of_str = self._as_of.get(corpus_id, "unknown")
        code_name = self._names.get(corpus_id, corpus_id)

        return LegalText(
            corpus_id=corpus_id,
            citation=canonical or citation,
            citation_raw=citation,
            title=entry["title"],
            text=entry["text"],
            source_path=entry["source"],
            source_commit=None,
            as_of=date.fromisoformat(as_of_str) if as_of_str != "unknown" else None,
            url=entry.get("url"),
            notes=f"{code_name} corpus as of {as_of_str}",
        )

    def search_text(self, query: str, limit: int = 10) -> list[LegalText]:
        """Substring search across all loaded state statute sections."""
        q = query.lower()
        results: list[LegalText] = []
        for (corpus_id, section), entry in self._index.items():
            if q in (entry["title"] + " " + entry["text"]).lower():
                canonical = f"{corpus_id} § {section}"
                as_of_str = self._as_of.get(corpus_id, "unknown")
                results.append(
                    LegalText(
                        corpus_id=corpus_id,
                        citation=canonical,
                        citation_raw=canonical,
                        title=entry["title"],
                        text=entry["text"][:500],
                        source_path=entry["source"],
                        source_commit=None,
                        as_of=(
                            date.fromisoformat(as_of_str)
                            if as_of_str != "unknown"
                            else None
                        ),
                        url=entry.get("url"),
                        notes=None,
                    )
                )
            if len(results) >= limit:
                break
        return results

    def list_amendments(self, citation: str) -> list[dict]:
        """Multi-state corpus has no git history — returns empty list."""
        return []

    def statistics(self) -> dict[str, int]:
        """Return total and per-state section counts."""
        per_code: dict[str, int] = {}
        for corpus_id, _ in self._index:
            per_code[corpus_id] = per_code.get(corpus_id, 0) + 1
        return {"total_sections": len(self._index), **per_code}

    def available_states(self) -> list[str]:
        """Return list of states with loaded corpus data."""
        return [
            _CORPUS_ID_STATE.get(cid, cid) for cid in {cid for cid, _ in self._index}
        ]

    def section_count(self, state: str) -> int:
        """Return number of loaded sections for *state* ('oregon', 'washington', 'texas')."""
        corpus_id = _STATE_CORPUS_IDS.get(state.lower())
        if not corpus_id:
            return 0
        return sum(1 for (cid, _) in self._index if cid == corpus_id)
