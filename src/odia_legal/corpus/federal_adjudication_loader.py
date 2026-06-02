"""FederalAdjudicationLoader — administrative law decisions corpus.

Loads decisions and procedural rules from federal administrative adjudication
bodies that supplement CourtListener's Article III court coverage.

Bodies covered:

  OAH   — California Office of Administrative Hearings
           (state ALJ decisions; overlaps with CA agency enforcement)
  MSPB  — U.S. Merit Systems Protection Board
           (federal employee adverse actions, whistleblower cases)
  EEOC  — U.S. Equal Employment Opportunity Commission
           (employment discrimination decisions and guidance)
  PCLOB — Privacy and Civil Liberties Oversight Board
           (surveillance program oversight reports)

Expected directory layout::

    <corpus_root>/
        oah/
            <decision_id>.json
        mspb/
            <decision_id>.json
        eeoc/
            <decision_id>.json
        pclob/
            <report_id>.json

Each decision JSON has the schema::

    {
      "body":        "oah",
      "decision_id": "2024-OAH-001",
      "title":       "In the Matter of ...",
      "docket":      "OAH No. 2024010001",
      "date":        "2024-03-15",
      "topics":      ["public records", "surveillance"],
      "holding":     "The agency failed to produce records within the statutory deadline...",
      "text":        "Full decision text...",
      "url":         "https://..."
    }

Citation forms recognized:
  OAH No. 2024010001
  MSPB Docket No. DC-0752-24-0001-I-1
  EEOC Appeal No. 2024000001
  PCLOB Report 2024-01

If no corpus root or empty, degrades gracefully.
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
# Citation patterns
# ---------------------------------------------------------------------------

_OAH_RE = re.compile(
    r"\bOAH\s+No\.?\s+(?P<docket>[A-Z0-9][\w\-]+)",
    re.IGNORECASE,
)

_MSPB_RE = re.compile(
    r"\bMSPB\s+(?:Docket\s+No\.?\s+)?(?P<docket>[A-Z]{2}-\d{4}-\d{2}-\d{4}-[A-Z]-\d+)",
    re.IGNORECASE,
)

_EEOC_RE = re.compile(
    r"\bEEOC\s+(?:Appeal\s+No\.?\s+|No\.?\s+)?(?P<docket>\d{4}-\d+)",
    re.IGNORECASE,
)

_PCLOB_RE = re.compile(
    r"\bPCLOB\s+(?:Report\s+)?(?P<docket>\d{4}-\d+)",
    re.IGNORECASE,
)

# Map body slug → citation prefix
_BODY_PREFIX = {
    "oah": "OAH No.",
    "mspb": "MSPB",
    "eeoc": "EEOC",
    "pclob": "PCLOB Report",
}

# Supported subdirectory names → body slug
_DIR_BODY = {
    "oah": "oah",
    "mspb": "mspb",
    "eeoc": "eeoc",
    "pclob": "pclob",
}


class FederalAdjudicationLoader(CorpusLoader):
    """Loads federal and state administrative adjudication decisions."""

    corpus_id = "federal_adjudication"

    def __init__(self, submodule_path: Path | str):
        self._root = Path(submodule_path)
        # (body, docket) → decision dict
        self._index: dict[tuple[str, str], dict] = {}
        # body → list of decision_ids (for search)
        self._by_body: dict[str, list[tuple[str, str]]] = {}
        self._initialized = False

    def initialize(self) -> dict[str, int]:
        """Scan corpus root for decision JSON files. Returns counts per body."""
        if not self._root.exists():
            logger.warning(
                "FederalAdjudicationLoader: corpus root not found at %s; "
                "adjudication lookups disabled until corpus is ingested",
                self._root,
            )
            self._initialized = True
            return {}

        counts: dict[str, int] = {}
        for body_dir in sorted(self._root.iterdir()):
            if not body_dir.is_dir():
                continue
            body = _DIR_BODY.get(body_dir.name.lower(), body_dir.name.lower())
            loaded = 0
            for json_file in sorted(body_dir.glob("*.json")):
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Skipping %s: %s", json_file, exc)
                    continue

                docket = data.get("docket") or data.get("decision_id", "")
                if not docket:
                    continue

                key = (body, docket)
                self._index[key] = {
                    "title": data.get("title", ""),
                    "date": data.get("date", ""),
                    "holding": data.get("holding", ""),
                    "text": data.get("text", ""),
                    "topics": data.get("topics", []),
                    "url": data.get("url"),
                    "source": str(json_file),
                }
                self._by_body.setdefault(body, []).append(key)
                loaded += 1

            counts[body] = loaded
            logger.info("FederalAdjudicationLoader: %s — %d decisions", body, loaded)

        self._initialized = True
        return counts

    def resolve_citation(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        """Resolve an administrative docket citation to LegalText.

        Recognizes OAH, MSPB, EEOC, and PCLOB citation forms.
        Returns None for unrecognized or uncached dockets.
        """
        if not self._initialized:
            return None

        # Try each body pattern
        body: str | None = None
        docket: str | None = None

        for pattern, body_slug in [
            (_OAH_RE, "oah"),
            (_MSPB_RE, "mspb"),
            (_EEOC_RE, "eeoc"),
            (_PCLOB_RE, "pclob"),
        ]:
            m = pattern.search(citation)
            if m:
                body = body_slug
                docket = m.group("docket")
                break

        if body is None or docket is None:
            return None

        entry = self._index.get((body, docket))
        if entry is None:
            return None

        prefix = _BODY_PREFIX.get(body, body.upper())
        canonical = f"{prefix} {docket}"
        date_str = entry.get("date", "")

        return LegalText(
            corpus_id=self.corpus_id,
            citation=canonical,
            citation_raw=citation,
            title=entry["title"],
            text=entry.get("holding") or entry.get("text", "")[:1000],
            source_path=entry["source"],
            source_commit=None,
            as_of=date.fromisoformat(date_str) if date_str else None,
            url=entry.get("url"),
            notes=f"{body.upper()} decision corpus",
        )

    def search_text(self, query: str, limit: int = 10) -> list[LegalText]:
        """Search decisions by keyword across title, holding, and topics."""
        q = query.lower()
        results: list[LegalText] = []
        for (body, docket), entry in self._index.items():
            searchable = (
                entry["title"]
                + " "
                + entry.get("holding", "")
                + " "
                + " ".join(entry.get("topics", []))
            ).lower()
            if q in searchable:
                prefix = _BODY_PREFIX.get(body, body.upper())
                canonical = f"{prefix} {docket}"
                date_str = entry.get("date", "")
                results.append(
                    LegalText(
                        corpus_id=self.corpus_id,
                        citation=canonical,
                        citation_raw=canonical,
                        title=entry["title"],
                        text=entry.get("holding", "")[:500],
                        source_path=entry["source"],
                        source_commit=None,
                        as_of=date.fromisoformat(date_str) if date_str else None,
                        url=entry.get("url"),
                        notes=f"{body.upper()} decision corpus",
                    )
                )
            if len(results) >= limit:
                break
        return results

    def list_amendments(self, citation: str) -> list[dict]:
        """Administrative decisions are not amended — returns empty list."""
        return []

    def statistics(self) -> dict[str, int]:
        """Return total and per-body decision counts."""
        per_body: dict[str, int] = {}
        for body, _ in self._index:
            per_body[body] = per_body.get(body, 0) + 1
        return {"total_decisions": len(self._index), **per_body}

    def bodies_loaded(self) -> list[str]:
        """Return list of adjudication bodies with loaded decisions."""
        return list({body for body, _ in self._index})

    def decisions_for_body(self, body: str) -> list[dict]:
        """Return all decision metadata for a given body slug."""
        return [
            {"docket": docket, **self._index[(body, docket)]}
            for body_slug, docket in self._index
            if body_slug == body.lower()
        ]
