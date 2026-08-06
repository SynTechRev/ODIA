"""L-11 Arbitration Architecture detector (sub-detectors A through J).

Identifies structural features of arbitration clauses that, individually or
in combination, constitute substantive or procedural unconscionability under
California law (Armendariz) or trigger CCP 1281.96 disclosure obligations.

Sub-detectors:
  A -- Binding / mandatory arbitration clause present
  B -- Class action / representative action waiver
  C -- FAA preemption invocation
  D -- Named administrator (JAMS / AAA / NAM) -- triggers 1281.96 duty
  E -- Fee allocation unfavorable to consumer (split / claimant-pays)
  F -- Non-California venue specified in arbitration clause
  G -- Loser-pays / prevailing-party cost-shifting provision
  H -- Discovery limitations or restrictions
  I -- Confidentiality or non-disclosure obligation on claimant
  J -- No appeal / final-and-binding waiver of judicial review

Source: C.O.N.T.R.A. Framework V1.0 Detector Specification Section 4.1,
        Handoff Specification V1.0 Section 5.1 (L-11)
"""

from __future__ import annotations

import re
from typing import List, Optional

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import EvidenceSpan, Finding, Severity

_LAYER = "L-11"

# ---------------------------------------------------------------------------
# Compiled patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

_P_A = re.compile(
    r"\b(?:binding\s+arbitration|mandatory\s+arbitration"
    r"|shall\s+(?:be\s+)?(?:resolved|submitted?|settled)\s+(?:by|through|via)\s+arbitrat"
    r"|disputes?\s+(?:will|shall|must)\s+be\s+(?:resolved|settled|decided)\s+"
    r"(?:by|through|via|in)\s+arbitrat"
    r"|agree(?:s|d)?\s+to\s+arbitrat"
    r"|submit\s+to\s+(?:binding\s+)?arbitrat)\b"
)

_P_B = re.compile(
    r"\b(?:class\s+action|class[-\s]wide|collective\s+action|representative\s+action"
    r"|class\s+arbitration)\b.{0,250}"
    r"\b(?:waiv\w*|prohibit\w*|barr\w*|cannot|may\s+not|not\s+(?:bring|file|pursue|maintain"
    r"|participate\s+in|be\s+part\s+of))\b"
    r"|\b(?:waiv\w*|prohibit\w*|barr\w*)\b.{0,250}"
    r"\b(?:class\s+action|class[-\s]wide|representative\s+action)\b",
    re.DOTALL,
)

_P_C = re.compile(
    r"\b(?:federal\s+arbitration\s+act"
    r"|9\s+u\.?s\.?c\.?"
    r"|faa\s+(?:govern|apply|applies?|preempt)"
    r"|governed\s+by\s+(?:the\s+)?(?:federal\s+arbitration\s+act|faa))\b"
)

_P_D = re.compile(
    r"\b(?:jams|american\s+arbitration\s+association|aaa"
    r"|nam\b|national\s+arbitration\s+and\s+mediation"
    r"|finra)\b"
)

_P_E = re.compile(
    r"\b(?:split\s+(?:the\s+)?(?:arbitration\s+)?(?:fees?|costs?)"
    r"|each\s+party\s+(?:shall|will|must)\s+(?:bear|pay)\s+(?:its\s+)?own"
    r"|claimant\s+(?:shall|will|must)\s+(?:pay|bear)"
    r"|filing\s+fee(?:s)?\s+(?:shall|will|are)\s+split"
    r"|share\s+(?:equally\s+)?(?:the\s+)?(?:arbitration\s+)?costs?)\b"
)

_P_F = re.compile(
    r"\barbitrat\w*\b.{0,400}"
    r"\b(?:venue|location|take\s+place|be\s+(?:conducted|held)|proceed)\b.{0,200}"
    r"\b(?:new\s+york|delaware|texas|florida|nevada|illinois|virginia"
    r"|washington\s+d\.?c\.?|district\s+of\s+columbia)\b"
    r"|\b(?:new\s+york|delaware|texas|florida|nevada|illinois|virginia"
    r"|washington\s+d\.?c\.?|district\s+of\s+columbia)\b.{0,200}"
    r"\b(?:venue|location)\b.{0,200}\barbitrat\w*\b",
    re.DOTALL,
)

_P_G = re.compile(
    r"\b(?:loser\s+pays?"
    r"|prevailing\s+party\s+(?:shall|will|may|is\s+entitled\s+to)\s+"
    r"(?:recover|collect|be\s+awarded)\s+(?:attorney|legal)\s+fees?\b"
    r"|losing\s+party\s+(?:shall|will|must)\s+(?:pay|bear)\s+"
    r"(?:all\s+)?(?:attorney|legal|arbitration)\s+(?:fees?|costs?)\b"
    r"|award\s+(?:of\s+)?(?:attorney|legal)\s+fees?\s+against\s+the\s+"
    r"(?:non[-\s]?prevailing|losing|unsuccessful)\s+party)\b"
)

_P_H = re.compile(
    r"\b(?:limit(?:ed|ing)\s+discovery"
    r"|discovery\s+(?:shall|will|is|may)\s+(?:be\s+)?limited"
    r"|no\s+(?:depositions?|interrogatories?|requests?\s+for\s+(?:production|admission))"
    r"|discovery\s+(?:shall\s+)?not\s+(?:include|permit|allow)"
    r"|restrict(?:ed|ing)\s+discovery)\b"
)

_P_I = re.compile(
    r"\b(?:(?:arbitration|proceeding|award|process)\b.{0,200}"
    r"\b(?:confidential|shall\s+not\s+(?:disclose|reveal|publicize)"
    r"|non[-\s]?disclosure|sealed?|private)"
    r"|(?:confidential|non[-\s]?disclosure|sealed?|private)\b.{0,200}"
    r"\b(?:arbitration|proceeding|award|process))\b",
    re.DOTALL,
)

_P_J = re.compile(
    r"\b(?:no\s+(?:right\s+to\s+)?appeal"
    r"|waive(?:s|d|r\s+of)?\s+(?:any\s+)?(?:right\s+to\s+)?appeal"
    r"|final\s+and\s+binding"
    r"|not\s+subject\s+to\s+(?:judicial\s+)?review"
    r"|award\s+(?:shall|will|is|may\s+not)\s+(?:be\s+)?(?:final|binding"
    r"|not\s+(?:be\s+)?appealed?))\b"
)

# ---------------------------------------------------------------------------
# Remedy channels (reused across sub-detectors)
# ---------------------------------------------------------------------------

_REMEDY_ARB = ["CCP_1281_97_default", "AG_complaint", "CPPA_complaint"]
_REMEDY_CLASS = ["class_action_federal", "AG_complaint", "PAGA"]
_REMEDY_FEE = ["CCP_1281_97_default", "AG_complaint", "small_claims"]
_REMEDY_GENERAL = ["AG_complaint", "small_claims"]


class L11ArbitrationArchitecture:
    """L-11 detector: Arbitration Architecture (sub-detectors A through J)."""

    layer: str = _LAYER

    def __init__(self, llm_client=None) -> None:
        self._llm = llm_client

    def scan(self, doc_text: str, doc_meta: dict) -> List[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        findings: List[Finding] = []
        findings += scan_pattern(
            _P_A, doc_text, _LAYER, "A", Severity.HIGH, doc_hash,
            A.ARMENDARIZ, "procedural_adhesion", 4,
            _REMEDY_ARB,
            notes="Binding arbitration clause detected.",
        )
        findings += scan_pattern(
            _P_B, doc_text, _LAYER, "B", Severity.CRITICAL, doc_hash,
            A.CONCEPCION, "remedy_foreclosure", 7,
            _REMEDY_CLASS,
            notes="Class/representative action waiver detected.",
        )
        findings += scan_pattern(
            _P_C, doc_text, _LAYER, "C", Severity.MEDIUM, doc_hash,
            A.CONCEPCION, "procedural_adhesion", 2,
            _REMEDY_GENERAL,
            notes="FAA preemption invocation -- limits California unconscionability ceiling.",
        )
        findings += scan_pattern(
            _P_D, doc_text, _LAYER, "D", Severity.LOW, doc_hash,
            A.CCP_1281_96, "procedural_adhesion", 1,
            ["CCP_1281_96_disclosure_request"],
            notes="Named arbitration administrator triggers 1281.96 disclosure obligation.",
        )
        findings += scan_pattern(
            _P_E, doc_text, _LAYER, "E", Severity.HIGH, doc_hash,
            A.ARMENDARIZ, "enforcement_cost_asymmetry", 4,
            _REMEDY_FEE,
            notes="Fee allocation asymmetric against consumer.",
        )
        findings += scan_pattern(
            _P_F, doc_text, _LAYER, "F", Severity.MEDIUM, doc_hash,
            A.ARMENDARIZ, "procedural_adhesion", 2,
            _REMEDY_GENERAL,
            notes="Non-California arbitration venue may violate Armendariz proximity rule.",
        )
        findings += scan_pattern(
            _P_G, doc_text, _LAYER, "G", Severity.CRITICAL, doc_hash,
            A.ARMENDARIZ, "enforcement_cost_asymmetry", 7,
            _REMEDY_ARB,
            notes="Loser-pays / cost-shifting prohibited by Armendariz.",
        )
        findings += scan_pattern(
            _P_H, doc_text, _LAYER, "H", Severity.MEDIUM, doc_hash,
            A.ARMENDARIZ, "remedy_foreclosure", 2,
            _REMEDY_GENERAL,
            notes="Discovery limitations may impair ability to vindicate statutory rights.",
        )
        findings += scan_pattern(
            _P_I, doc_text, _LAYER, "I", Severity.LOW, doc_hash,
            A.ARMENDARIZ, "procedural_adhesion", 1,
            _REMEDY_GENERAL,
            notes="One-sided confidentiality can factor into unconscionability analysis.",
        )
        findings += scan_pattern(
            _P_J, doc_text, _LAYER, "J", Severity.HIGH, doc_hash,
            A.ARMENDARIZ, "remedy_foreclosure", 4,
            _REMEDY_ARB,
            notes="No-appeal / final-binding waiver limits judicial oversight.",
        )
        return findings
