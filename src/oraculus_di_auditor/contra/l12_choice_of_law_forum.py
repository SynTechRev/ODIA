"""L-12 Choice of Law / Forum detector (sub-detectors A through E).

Identifies clauses that displace California law, foreclose California forums,
shorten limitation periods, waive unwaivable statutory rights (CCPA/CPRA),
or use integration language to erase prior disclosures.

Sub-detectors:
  A -- Non-California governing law designation
  B -- Exclusive non-California forum selection
  C -- Shortened limitation of action period (< statutory minimum)
  D -- Express waiver of California consumer / privacy statutory rights
  E -- Integration clause excluding prior representations or disclosures

Source: C.O.N.T.R.A. Framework V1.0 Section 4.2, Handoff Spec V1.0 Section 5.2
"""

from __future__ import annotations

import re
from typing import List

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import Finding, Severity

_LAYER = "L-12"

# ---------------------------------------------------------------------------
# Compiled patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

_OUT_OF_STATE = (
    r"(?:new\s+york|delaware|texas|florida|nevada|illinois|virginia"
    r"|washington\s+d\.?c\.?|district\s+of\s+columbia|utah|arizona"
    r"|georgia|new\s+jersey|colorado|ohio|washington\s+state)"
)

_P_A = re.compile(
    r"\b(?:govern(?:ed|ing)\s+(?:law\s+)?(?:by\s+)?(?:the\s+)?laws?\s+of\s+(?:the\s+state\s+of\s+)?"
    + _OUT_OF_STATE
    + r"|law\s+of\s+(?:the\s+state\s+of\s+)?"
    + _OUT_OF_STATE
    + r"|laws?\s+of\s+"
    + _OUT_OF_STATE
    + r"\s+shall\s+govern)\b"
)

_P_B = re.compile(
    r"\b(?:exclusive(?:ly)?\s+(?:jurisdiction|venue|forum)"
    r"|venue\s+(?:shall|will|must)\s+be\b.{0,100}"
    + _OUT_OF_STATE
    + r"|submit\s+to\s+(?:the\s+)?(?:exclusive\s+)?jurisdiction\s+of.{0,100}"
    + _OUT_OF_STATE
    + r")\b",
    re.DOTALL,
)

_P_C = re.compile(
    r"\b(?:claim|action|suit|lawsuit|legal\s+action|cause\s+of\s+action|dispute)\b"
    r".{0,300}"
    r"\bwithin\s+(?:one\s+\(?1\)?|two\s+\(?2\)?|(?:30|60|90|180|365))\s+"
    r"(?:days?|months?|years?)\b"
    r"|\b(?:must\s+be\s+(?:brought|filed|submitted)|only\s+if\s+(?:brought|filed))"
    r"\s+within\s+"
    r"(?:one\s+\(?1\)?|two\s+\(?2\)?|(?:30|60|90|180|365))\s+(?:days?|months?|years?)\b",
    re.DOTALL,
)

_P_D = re.compile(
    r"\b(?:waive(?:s|d|r\s+of)?\s+(?:any\s+)?(?:and\s+all\s+)?"
    r"(?:california\s+)?(?:privacy|consumer|statutory)\s+"
    r"(?:rights?|protections?|remedies?|claims?)"
    r"|you\s+(?:waive|give\s+up|agree\s+not\s+to\s+exercise)\s+"
    r"(?:any\s+)?(?:rights?\s+under|rights?\s+provided\s+by)\s+"
    r"(?:the\s+)?(?:ccpa|cpra|california\s+consumer\s+privacy\s+act"
    r"|california\s+privacy\s+rights\s+act)"
    r"|you\s+waive\w*\b.{0,100}\brights?\b.{0,200}"
    r"\b(?:ccpa|cpra|california\s+consumer\s+privacy\s+act"
    r"|california\s+privacy\s+rights\s+act)\b)\b",
    re.DOTALL,
)

_P_E = re.compile(
    r"\b(?:entire\s+agreement|integration\s+clause"
    r"|supersedes?\s+(?:and\s+)?(?:replaces?\s+)?(?:all|any)\s+prior"
    r"|replaces?\s+(?:all|any)\s+prior\s+(?:agreements?|terms?|representations?"
    r"|understandings?|disclosures?|communications?)"
    r"|no\s+other\s+(?:representations?|warranties?|statements?)\s+"
    r"(?:are|have\s+been)\s+made)\b"
)

# ---------------------------------------------------------------------------
# Remedy channel maps
# ---------------------------------------------------------------------------

_REMEDY_GOV_LAW = ["AG_complaint", "CPPA_complaint"]
_REMEDY_FORUM = ["AG_complaint", "small_claims"]
_REMEDY_SOL = ["AG_complaint", "small_claims"]
_REMEDY_WAIVER = ["CPPA_complaint", "AG_complaint", "CCPA_opt_out"]
_REMEDY_INTEGRATION = ["FTC_complaint", "AG_complaint"]


class L12ChoiceOfLawForum:
    """L-12 detector: Choice of Law / Forum (sub-detectors A through E)."""

    layer: str = _LAYER

    def __init__(self) -> None:
        pass

    def scan(self, doc_text: str, doc_meta: dict) -> List[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        findings: List[Finding] = []
        findings += scan_pattern(
            _P_A, doc_text, _LAYER, "A", Severity.MEDIUM, doc_hash,
            A.SANCHEZ_VALENCIA, "procedural_adhesion", 2,
            _REMEDY_GOV_LAW,
            notes="Non-California governing law -- California unconscionability doctrine still applies.",
        )
        findings += scan_pattern(
            _P_B, doc_text, _LAYER, "B", Severity.MEDIUM, doc_hash,
            A.ARMENDARIZ, "procedural_adhesion", 2,
            _REMEDY_FORUM,
            notes="Exclusive out-of-state forum selection against California consumers.",
        )
        findings += scan_pattern(
            _P_C, doc_text, _LAYER, "C", Severity.HIGH, doc_hash,
            A.CCP_337, "remedy_foreclosure", 4,
            _REMEDY_SOL,
            notes="Contractual limitation period shorter than California statutory minimum.",
        )
        findings += scan_pattern(
            _P_D, doc_text, _LAYER, "D", Severity.CRITICAL, doc_hash,
            A.CCPA_192, "remedy_foreclosure", 7,
            _REMEDY_WAIVER,
            notes="CCPA/CPRA rights are non-waivable by contract (Cal. Civ. Code 1798.192).",
        )
        findings += scan_pattern(
            _P_E, doc_text, _LAYER, "E", Severity.LOW, doc_hash,
            A.RING_ORDER, "modification_and_consent", 1,
            _REMEDY_INTEGRATION,
            notes="Integration clause may erase prior privacy disclosures or material representations.",
        )
        return findings
