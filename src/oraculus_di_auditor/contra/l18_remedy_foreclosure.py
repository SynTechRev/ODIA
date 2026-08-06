"""L-18 Remedy Foreclosure detector (sub-detectors A through H).

Identifies contract provisions that cap, limit, or entirely eliminate the
consumer's remedial options.  Remedy foreclosure provisions shift litigation
risk asymmetrically: when recovery is capped at nominal amounts or equitable
relief is waived, even meritorious claims become economically unviable.

Sub-detectors:
  A -- Aggregate damages cap (capped at subscription price / nominal amount)
  B -- Consequential / incidental / special damages waiver
  C -- Punitive damages waiver (against Cal. Civ. Code section 3294)
  D -- Shortened statute of limitations / claim filing deadline
  E -- Jury trial waiver (HIGH: Grafton Partners California standard)
  F -- Equitable / injunctive relief waiver (CRITICAL)
  G -- Class representative PAGA waiver (post-Viking River)
  H -- Third-party disclaimer of warranties / indemnification

Source: C.O.N.T.R.A. Framework V1.0 Section 4.8, Handoff Spec V1.0 Section 5.8
"""

from __future__ import annotations

import re
from typing import List

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import Finding, Severity

_LAYER = "L-18"

# ---------------------------------------------------------------------------
# Patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

_P_A = re.compile(
    r"\b(?:(?:total\s+)?(?:liability|damages?)\b.{0,200}"
    r"\b(?:shall\s+not\s+exceed|limited\s+to|capped?\s+at|will\s+not\s+exceed)"
    r"\b.{0,100}\b(?:\$|dollar|\bamount\s+(?:paid|you\s+paid|paid\s+by\s+you)"
    r"|\bfees?\s+paid\b|\bsubscription\b|\bpurchase\s+price)"
    r"|(?:shall\s+not\s+exceed|limited\s+to|will\s+not\s+exceed)\b.{0,150}"
    r"\b(?:\$\s*(?:50|100|500|1[\s,]?000)|one\s+hundred|fifty\s+dollars?"
    r"|amount\s+paid|fees?\s+paid\s+in\s+the\s+(?:past|preceding|prior)\s+\d+))\b",
    re.DOTALL,
)

_P_B = re.compile(
    r"\b(?:(?:consequential|incidental|special|indirect|exemplary)\s+damages?\b.{0,200}"
    r"\b(?:waiv\w*|not\s+(?:liable|responsible|recover|available)|excluded?|disclaim\w*"
    r"|shall\s+not\s+(?:be\s+)?(?:liable|responsible|award\w*))\b"
    r"|(?:waiv\w*|disclaim\w*|excluded?)\b.{0,200}"
    r"\b(?:consequential|incidental|special|indirect|exemplary)\s+damages?\b"
    r"|no\s+(?:liability|responsibility)\s+for\b.{0,100}"
    r"\b(?:consequential|incidental|indirect|special)\s+damages?"
    r"|(?:shall|will)\s+not\b.{0,50}\bliable\b.{0,150}"
    r"\b(?:consequential|incidental|special|indirect|exemplary)\s+damages?"
    r"|not\s+(?:be\s+)?(?:liable|responsible)\b.{0,150}"
    r"\b(?:consequential|incidental|special|indirect|exemplary)\s+damages?)\b",
    re.DOTALL,
)

_P_C = re.compile(
    r"\b(?:punitive\s+damages?\b.{0,200}"
    r"\b(?:waiv\w*|not\s+(?:liable|responsible|award\w*)|excluded?|disclaim\w*"
    r"|shall\s+not\s+(?:be\s+)?(?:liable|responsible|award\w*)|hereby\s+waiv\w*"
    r"|shall\s+not\s+be\s+available)\b"
    r"|(?:waiv\w*|disclaim\w*|excluded?|hereby\s+waiv\w*)\b.{0,200}\bpunitive\s+damages?\b"
    r"|no\s+(?:liability|responsibility)\s+for\b.{0,100}\bpunitive\s+damages?"
    r"|punitive\s+damages?\s+(?:are\s+(?:hereby\s+)?waiv\w*|shall\s+not\s+be\s+"
    r"(?:available|awarded|recover\w*)))\b",
    re.DOTALL,
)

_P_D = re.compile(
    r"\b(?:any\s+)?(?:claim|action|suit|lawsuit|legal\s+action|cause\s+of\s+action"
    r"|dispute|proceeding)\b.{0,300}"
    r"\b(?:within|no\s+later\s+than|must\s+be\s+(?:filed|brought|commenced)"
    r"|shall\s+be\s+(?:filed|brought|commenced))\b.{0,50}"
    r"\b(?:one\s+(?:year|month)|two\s+(?:year|month)|30\s+days?|60\s+days?"
    r"|90\s+days?|six\s+months?|one\s+year|two\s+years?)\b"
    r"|\b(?:one|two)\s+(?:year|month)\s+limitation\b"
    r"|\blimitation\s+period\s+of\s+(?:one|two|30|60|90)\b",
    re.DOTALL,
)

_P_E = re.compile(
    r"\b(?:waiv\w*\b.{0,200}\bjury\s+trial\b"
    r"|\bjury\s+trial\b.{0,200}\bwaiv\w*\b"
    r"|you\s+(?:hereby\s+)?waive\w*\b.{0,50}\bright\s+to\s+(?:a\s+)?jury\s+trial"
    r"|right\s+to\s+(?:a\s+)?jury\s+trial\b.{0,50}\bwaiv\w*)\b",
    re.DOTALL,
)

_P_F = re.compile(
    r"\b(?:waiv\w*\b.{0,200}\b(?:injunctive|equitable)\s+relief\b"
    r"|\b(?:injunctive|equitable)\s+relief\b.{0,200}\bwaiv\w*\b"
    r"|you\s+(?:may\s+not|cannot|shall\s+not)\b.{0,100}"
    r"\b(?:seek|obtain|request|bring\s+(?:an?\s+)?(?:action|claim))\b.{0,50}"
    r"\b(?:injunctive|equitable|preliminary|temporary)\s+(?:relief|remedy|injunction)\b"
    r"|no\s+(?:injunctive|equitable)\s+(?:relief|remedy)\s+(?:will|shall|may)\s+be"
    r"\s+(?:granted|available|sought|issued))\b",
    re.DOTALL,
)

_P_G = re.compile(
    r"\b(?:paga\b.{0,300}\b(?:waiv\w*|not\s+(?:permitted|allowed|available)"
    r"|prohibit\w*|barr\w*)\b"
    r"|\b(?:waiv\w*|prohibit\w*|barr\w*)\b.{0,300}\bpaga\b"
    r"|private\s+attorneys?\s+general\s+act\b.{0,300}"
    r"\b(?:waiv\w*|not\s+(?:permitted|allowed)|prohibit\w*)\b)\b",
    re.DOTALL,
)

_P_H = re.compile(
    r"\b(?:as\s+is|(?:without|disclaims?)\s+(?:any\s+)?(?:implied\s+)?warranty"
    r"|(?:all\s+)?warranties?\s+disclaim\w*|no\s+warranties?"
    r"|disclaim\s+all\s+warranties?"
    r"|third[-\s]?part(?:y|ies)\b.{0,200}\b(?:disclaim\w*|not\s+responsible"
    r"|not\s+liable|no\s+(?:liability|responsibility)))\b",
    re.DOTALL,
)

_REMEDY_CAP = ["demand_letter", "CPPA_complaint", "AG_complaint"]
_REMEDY_WAIVER = ["demand_letter", "CPPA_complaint", "AG_complaint", "class_action"]
_REMEDY_JURY = ["demand_letter", "GRAFTON_PARTNERS_challenge"]
_REMEDY_EQUITABLE = ["demand_letter", "CPPA_complaint", "AG_complaint", "Armendariz_challenge"]
_REMEDY_PAGA = ["PAGA_action", "AG_complaint", "demand_letter"]


class L18RemedyForeclosure:
    """L-18 detector: Remedy Foreclosure (sub-detectors A through H)."""

    layer: str = _LAYER

    def __init__(self) -> None:
        pass

    def scan(self, doc_text: str, doc_meta: dict) -> List[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        findings: List[Finding] = []
        findings += scan_pattern(
            _P_A, doc_text, _LAYER, "A", Severity.HIGH, doc_hash,
            A.ARMENDARIZ, "remedy_foreclosure", 4, _REMEDY_CAP,
            notes="Aggregate damages cap -- recovery limited to nominal amount paid.",
        )
        findings += scan_pattern(
            _P_B, doc_text, _LAYER, "B", Severity.HIGH, doc_hash,
            A.ARMENDARIZ, "remedy_foreclosure", 4, _REMEDY_WAIVER,
            notes="Consequential/incidental/special damages waiver -- eliminates real-world harm recovery.",
        )
        findings += scan_pattern(
            _P_C, doc_text, _LAYER, "C", Severity.HIGH, doc_hash,
            A.CIVCODE_3294, "remedy_foreclosure", 4, _REMEDY_WAIVER,
            notes="Punitive damages waiver -- California courts disfavor this in consumer adhesion contracts.",
        )
        findings += scan_pattern(
            _P_D, doc_text, _LAYER, "D", Severity.HIGH, doc_hash,
            A.CCP_337, "remedy_foreclosure", 4, _REMEDY_CAP,
            notes="Shortened statute of limitations -- reduces time below California statutory baseline.",
        )
        findings += scan_pattern(
            _P_E, doc_text, _LAYER, "E", Severity.HIGH, doc_hash,
            A.GRAFTON_PARTNERS, "remedy_foreclosure", 4, _REMEDY_JURY,
            notes="Jury trial waiver -- Grafton Partners bars pre-dispute waivers in California.",
        )
        findings += scan_pattern(
            _P_F, doc_text, _LAYER, "F", Severity.CRITICAL, doc_hash,
            A.ARMENDARIZ, "remedy_foreclosure", 7, _REMEDY_EQUITABLE,
            notes="Equitable relief waiver -- forecloses injunction even when damages are inadequate remedy.",
        )
        findings += scan_pattern(
            _P_G, doc_text, _LAYER, "G", Severity.CRITICAL, doc_hash,
            A.VIKING_RIVER, "remedy_foreclosure", 7, _REMEDY_PAGA,
            notes="PAGA waiver -- Viking River permits individual PAGA waivers but not representative waivers.",
        )
        findings += scan_pattern(
            _P_H, doc_text, _LAYER, "H", Severity.MEDIUM, doc_hash,
            A.ARMENDARIZ, "remedy_foreclosure", 2, _REMEDY_CAP,
            notes="As-is / third-party warranty disclaimer -- shifts liability to consumer for partner conduct.",
        )
        return findings
