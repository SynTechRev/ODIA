"""Parse statutory citations into structured form.

Handles the variant formats found in O.D.I.A. narrative templates,
finding sheets, and ingested document text:

    "34 U.S.C. § 10152"
    "34 U.S.C. § 10152(a)(1)(G)"
    "34 U.S.C. §§ 10152-10153"      # range
    "34 USC 10152"                   # informal
    "34 U.S.C. § 10152 (Supp. 2020)" # with edition

Does NOT handle CFR or case-law citations; those will have their
own parsers when those corpora land.

Returns None for unparseable strings — caller decides how to handle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StatuteCitation:
    """A parsed federal statutory citation.

    Canonical form: f"{title} U.S.C. § {section}{subsection_path}"
    """

    title: int  # e.g., 34
    section: str  # e.g., "10152" (str to handle "10152a" etc.)
    subsection_path: str  # e.g., "(a)(1)(G)" or "" if root
    raw: str  # the original matched substring
    canonical: str  # normalized form for cache keys

    @property
    def section_root(self) -> str:
        """Section number without subsection path. Used for file lookup."""
        return self.section


# Comprehensive USC citation regex. Handles:
#   - 34 U.S.C. § 10152
#   - 34 USC 10152  (without periods or section symbol)
#   - 34 U.S.C. § 10152(a)(1)(G)
#   - 34 U.S.C. §§ 10152-10153  (range — captured but reported as first)
# Negative lookbehind for "C.F.R." prevents misparsing CFR citations
# (e.g. "2 C.F.R. § 200.303" must NOT match this regex).
_USC_PATTERN = re.compile(
    r"""
    (?<!C\.F\.R\.\s)                  # not preceded by "C.F.R. " (CFR guard)
    (?<!CFR\s)                        # not preceded by "CFR " (CFR guard)
    \b(?P<title>\d{1,2})              # title: 1-50ish
    \s*
    U\.?\s?S\.?\s?C\.?                # U.S.C. with variant punctuation
    \s*
    §{0,2}                            # zero, one, or two § symbols
    \s*
    (?P<section>\d+[a-z]*)            # section: digits + optional letter (e.g., 1395dd)
    (?P<subsection>(?:\([a-z0-9]+\))*) # zero or more subsection levels
    """,
    re.VERBOSE | re.IGNORECASE,
)


def parse_usc_citations(text: str) -> list[StatuteCitation]:
    """Extract every USC citation from a block of text."""
    out: list[StatuteCitation] = []
    for m in _USC_PATTERN.finditer(text):
        title = int(m.group("title"))
        if title < 1 or title > 54:
            continue  # USC titles are 1-54
        section = m.group("section")
        subsection = m.group("subsection") or ""
        raw = m.group(0).strip()
        canonical = f"{title} U.S.C. § {section}{subsection}"
        out.append(
            StatuteCitation(
                title=title,
                section=section,
                subsection_path=subsection,
                raw=raw,
                canonical=canonical,
            )
        )
    return out


def parse_single(text: str) -> StatuteCitation | None:
    """Parse a single citation string. Returns None if no match."""
    matches = parse_usc_citations(text)
    return matches[0] if matches else None
