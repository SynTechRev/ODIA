"""L-9 Recodification Translation detector.

Identifies CPRA citation scheme errors in public-agency documents:

  1. Legacy citation in a post-2022 document — Gov. Code § 6254(f) should
     be Gov. Code § 7923.650 in any document produced after SB 1439 took
     effect (January 1, 2022).

  2. Mixed citation scheme — same document uses both old-form (§ 625x)
     and new-form (§ 792x) sections, indicating inconsistent legal research
     or copy-pasted boilerplate from different eras.

  3. Unmatched exemption claim — document invokes a CPRA exemption but
     does not provide the corresponding new-form citation, making the legal
     basis harder to verify in appeals or litigation.

For each finding the detector provides:
  - The old citation found in the document
  - The correct new-form citation (from CPRACrosswalk)
  - The section title
  - The document date (if parseable) and whether SB 1439 was in effect

Severity scale:
  high   — post-2022 document with old-form exemption claim (§ 6254 family)
  medium — post-2022 document with old-form non-exemption citation
  low    — pre-2022 document with mixed citation scheme or informational

ODIA anomaly dict contract:
  {
    "id":       "legal:l9:recodification:<finding_type>",
    "issue":    str,
    "severity": "low" | "medium" | "high",
    "layer":    "l9_recodification",
    "details":  {
      "old_section":   str,
      "new_section":   str,
      "title":         str,
      "raw_citation":  str,
      "document_date": str | None,
      "post_sb1439":   bool,
    }
  }
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from odia_legal.citations.parser import parse_cal_code
from odia_legal.recodification.cpra_crosswalk import (
    _OLD_TO_NEW,
    RECODIFICATION_DATE,
    CPRACrosswalk,
)

_CROSSWALK = CPRACrosswalk()

# Regex to find plausible dates in document text (YYYY or MM/DD/YYYY or Month DD, YYYY)
_DATE_PATTERNS = [
    re.compile(r"\b(20\d{2})\b"),  # bare year
    re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b"),  # MM/DD/YYYY
    re.compile(
        r"\b(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+\d{1,2},?\s+(20\d{2})\b",
        re.IGNORECASE,
    ),
]

_EXEMPTION_SECTIONS = frozenset(s for s in _OLD_TO_NEW if s.startswith("6254"))

_EXEMPTION_LANGUAGE_RE = re.compile(
    r"\b(?:exempt(?:ion)?|withhold(?:ing)?|privileged?|nondisclosure"
    r"|not\s+subject\s+to\s+disclosure|confidential)\b",
    re.IGNORECASE,
)


def _extract_document_date(doc: dict[str, Any]) -> date | None:
    """Best-effort date extraction from document metadata or text."""
    meta = doc.get("metadata") or {}

    # 1. Metadata fields
    for field in ("date", "doc_date", "created_at", "meeting_date", "year"):
        val = meta.get(field) or doc.get(field)
        if val:
            if isinstance(val, date):
                return val
            try:
                return date.fromisoformat(str(val)[:10])
            except (ValueError, TypeError):
                pass

    # 2. Scan text for the first plausible year
    text = _get_text(doc)
    for pat in _DATE_PATTERNS:
        m = pat.search(text)
        if m:
            year_str = m.group(m.lastindex or 1)
            try:
                year = int(year_str)
                if 2000 <= year <= 2030:
                    return date(year, 1, 1)
            except (ValueError, IndexError):
                pass
    return None


def _get_text(doc: dict[str, Any]) -> str:
    """Extract the text payload from a document dict."""
    for key in ("text", "content", "body", "raw_text"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-9 Recodification Translation detection on a single document.

    Args:
        doc: Document dict with at least a ``text`` / ``content`` field.
             Optional ``metadata.date`` for temporal context.

    Returns:
        List of anomaly dicts (may be empty).
    """
    text = _get_text(doc)
    if not text:
        return []

    doc_date = _extract_document_date(doc)
    post_sb1439 = doc_date is None or doc_date >= RECODIFICATION_DATE

    findings: list[dict[str, Any]] = []
    seen_old: set[str] = set()
    has_new_form = _CROSSWALK.is_current(text)

    # ------------------------------------------------------------------
    # Finding 1 & 2: Legacy citations in text
    # ------------------------------------------------------------------
    for result in _CROSSWALK.find_all_in_text(text):
        old_sec = result.old_section
        if old_sec in seen_old:
            continue
        seen_old.add(old_sec)

        is_exemption = old_sec in _EXEMPTION_SECTIONS or old_sec.startswith(
            "6254"
        )

        if post_sb1439:
            severity = "high" if is_exemption else "medium"
            issue = (
                f"CPRA exemption cited using repealed § {old_sec} "
                f"(post-SB-1439 form: § {result.new_section})"
                if is_exemption
                else f"CPRA § {old_sec} uses pre-2022 numbering "
                f"(current form: § {result.new_section})"
            )
        else:
            # Pre-2022 doc: old form is expected; only flag mixing
            if not has_new_form:
                continue
            severity = "low"
            issue = (
                f"Pre-2022 document mixes CPRA citation schemes: "
                f"§ {old_sec} (old) alongside new-form §§"
            )

        findings.append(
            {
                "id": f"legal:l9:recodification:legacy_citation:{old_sec}",
                "issue": issue,
                "severity": severity,
                "layer": "l9_recodification",
                "details": {
                    "old_section": old_sec,
                    "new_section": result.new_section,
                    "title": result.title,
                    "raw_citation": f"§ {old_sec}",
                    "document_date": doc_date.isoformat() if doc_date else None,
                    "post_sb1439": post_sb1439,
                    "article": result.article,
                },
            }
        )

    # ------------------------------------------------------------------
    # Finding 3: Unmatched exemption claim (no explicit statutory basis)
    # Fires when the text mentions a CPRA denial / exemption *language*
    # but contains no parseable § 6254 / § 7923 citation.
    # ------------------------------------------------------------------
    has_exemption_language = bool(_EXEMPTION_LANGUAGE_RE.search(text))
    has_exemption_citation = any(
        old_sec.startswith("6254") or result.new_section.startswith("7923")
        for old_sec in seen_old
        for result in [_CROSSWALK.lookup_old(old_sec)]
        if result
    )
    if not has_exemption_citation:
        # Also check new-form citations directly
        new_cites = parse_cal_code(text)
        has_exemption_citation = any(
            c.section and c.section.startswith("7923")
            for c in new_cites
            if c.corpus_id == "cal_gov_code"
        )

    if has_exemption_language and not has_exemption_citation and post_sb1439:
        findings.append(
            {
                "id": "legal:l9:recodification:unmatched_exemption_claim",
                "issue": (
                    "Document asserts CPRA exemption / withholding but provides "
                    "no parseable § 6254 / § 7923 statutory basis"
                ),
                "severity": "medium",
                "layer": "l9_recodification",
                "details": {
                    "old_section": None,
                    "new_section": None,
                    "title": "Unmatched exemption claim",
                    "raw_citation": None,
                    "document_date": doc_date.isoformat() if doc_date else None,
                    "post_sb1439": post_sb1439,
                    "article": "Exemptions",
                },
            }
        )

    return findings
