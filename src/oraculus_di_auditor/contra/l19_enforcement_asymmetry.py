"""L-19 Enforcement Asymmetry detector (sub-detectors A through G).

Identifies provisions that make enforcement expensive or structurally
impossible for the consumer while preserving full enforcement options for the
drafter.  Fee-shifting, cost-bearing, gag clauses, and discovery restrictions
each independently and cumulatively raise the price of a meritorious claim
beyond the consumer's rational-actor threshold.

Sub-detectors:
  A -- One-way attorney fee-shifting (drafter recovers; consumer does not)
  B -- Mutual / bilateral fee-shifting (nominally fair but asymmetric in practice)
  C -- Arbitration cost-bearing on consumer (no company payment)
  D -- Gag / non-disparagement clause (Cal. Code Civ. Proc. section 1001)
  E -- Discovery limitation below statutory minimum
  F -- Confidentiality on arbitration outcome imposed on consumer
  G -- No acknowledgment of CCP 1281.97 / 1281.98 fee-payment obligations

Source: C.O.N.T.R.A. Framework V1.0 Section 4.9, Handoff Spec V1.0 Section 5.9
"""

from __future__ import annotations

import re
from typing import List

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import Finding, Severity

_LAYER = "L-19"

# ---------------------------------------------------------------------------
# Patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

# A: one-way fee-shifting (drafter wins → consumer pays; no equivalent grant to consumer)
_P_A = re.compile(
    r"\b(?:(?:company|we|us|provider|vendor)\b.{0,200}"
    r"\b(?:prevailing\s+party|shall\s+be\s+entitled\s+to|entitled\s+to)\b.{0,100}"
    r"\b(?:recover|collect|be\s+awarded)\b.{0,80}\b(?:attorney|legal)\s+fees?\b"
    r"|if\s+(?:we|the\s+(?:company|provider))\s+prevail\w*\b.{0,100}"
    r"\b(?:recover|collect|attorney|legal)\s+fees?)\b",
    re.DOTALL,
)

# B: mutual fee-shifting (symmetrical text but asymmetric in practice)
_P_B = re.compile(
    r"\b(?:either\s+party|each\s+party|both\s+parties|the\s+prevailing\s+party)\b.{0,200}"
    r"\b(?:shall|will|may|is\s+entitled\s+to)\b.{0,80}"
    r"\b(?:recover|collect|be\s+awarded)\b.{0,80}\b(?:attorney|legal)\s+fees?\b",
    re.DOTALL,
)

# C: consumer bears arbitration costs (no company payment commitment)
_P_C_COST = re.compile(
    r"\b(?:you\s+(?:shall|will|must|agree\s+to)\s+(?:pay|bear|be\s+responsible\s+for)"
    r"\b.{0,100}\b(?:filing|administrative|arbitrator|arbitration)\s+(?:fee|cost|expense)\w*"
    r"|(?:filing|administrative|arbitrator|arbitration)\s+(?:fee|cost|expense)\w*"
    r"\b.{0,100}\b(?:borne\s+by\s+(?:you|the\s+(?:claimant|consumer|user))"
    r"|your\s+responsibility|shall\s+be\s+paid\s+by\s+(?:you|the\s+(?:claimant|consumer))))\b",
    re.DOTALL,
)

_P_C_COMPANY_PAY = re.compile(
    r"\b(?:company|we|us|provider|vendor)\b.{0,200}"
    r"\b(?:shall|will|agree\s+to|responsible\s+for)\b.{0,50}"
    r"\b(?:pay|bear|cover|reimburse)\b.{0,50}"
    r"\b(?:filing|administrative|arbitrator|arbitration)\s+(?:fee|cost|expense)\w*\b",
    re.DOTALL,
)

# D: non-disparagement / gag clause
_P_D = re.compile(
    r"\b(?:non.?disparagement"
    r"|not\s+(?:disparage|make\s+(?:any\s+)?(?:negative|disparaging|defamatory|derogatory)"
    r"\s+(?:statements?|comments?|reviews?|remarks?))\b"
    r"|agree\s+not\s+to\s+(?:post|write|publish|make|share)\b.{0,100}"
    r"\b(?:negative|disparaging|defamatory|derogatory|critical)\s+(?:statements?|comments?"
    r"|reviews?|remarks?|posts?)\b"
    r"|confidential\s+(?:settlement|resolution|outcome|arbitration)\b.{0,200}"
    r"\b(?:non.?disparagement|not\s+(?:disparage|make\s+(?:any\s+)?(?:negative|disparaging))))\b",
    re.DOTALL,
)

# E: discovery limitation
_P_E = re.compile(
    r"\b(?:(?:no|without|limited|waive\w*)\b.{0,50}\bdiscovery\b"
    r"|discovery\b.{0,100}\b(?:limited\s+to|shall\s+not\s+exceed|restricted\s+to"
    r"|may\s+only\s+include|waived|not\s+permitted)\b"
    r"|(?:document\s+exchange\s+only|no\s+depositions?|no\s+interrogatories?"
    r"|no\s+document\s+(?:requests?|productions?)"
    r"|discovery\s+(?:is\s+)?(?:not\s+permitted|waived|excluded))\b)\b",
    re.DOTALL,
)

# F: arbitration outcome confidentiality imposed on consumer
_P_F = re.compile(
    r"\b(?:(?:arbitration|proceeding|decision|award|outcome|result)\b.{0,200}"
    r"\b(?:confidential|not\s+(?:disclose|share|publicize|discuss|divulge))\b"
    r"|\b(?:you\s+(?:shall|will|agree\s+to|must))\b.{0,50}"
    r"\b(?:keep|maintain|hold)\b.{0,50}"
    r"\b(?:confidential|secret|private)\b.{0,100}"
    r"\b(?:arbitration|proceeding|decision|award|outcome|settlement))\b",
    re.DOTALL,
)

# G: arbitration present but no mention of CCP 1281.97 / 1281.98
_P_G_ARB = re.compile(
    r"\b(?:arbitration|arbitrator\w*|arbitrate)\b"
)

_P_G_1281 = re.compile(
    r"\b(?:1281\.97|1281\.98|sb\s*707|senate\s+bill\s+707)\b"
)

_REMEDY_FEE = ["demand_letter", "CPPA_complaint", "AG_complaint", "Armendariz_challenge"]
_REMEDY_GAG = ["CCP_1001_challenge", "AG_complaint", "demand_letter"]
_REMEDY_COST = ["demand_letter", "CPPA_complaint", "Armendariz_challenge"]
_REMEDY_DISCOVERY = ["demand_letter", "Armendariz_challenge"]
_REMEDY_CONF = ["demand_letter", "AG_complaint"]
_REMEDY_1281 = ["CCP_1281_97_demand", "AG_complaint"]


class L19EnforcementAsymmetry:
    """L-19 detector: Enforcement Asymmetry (sub-detectors A through G)."""

    layer: str = _LAYER

    def __init__(self) -> None:
        pass

    def scan(self, doc_text: str, doc_meta: dict) -> List[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        text_lower = doc_text.lower()
        findings: List[Finding] = []

        # A: one-way fee-shifting
        findings += scan_pattern(
            _P_A, doc_text, _LAYER, "A", Severity.CRITICAL, doc_hash,
            A.ARMENDARIZ, "enforcement_cost_asymmetry", 7, _REMEDY_FEE,
            notes="One-way attorney fee-shifting -- drafter recovers fees consumer cannot.",
        )

        # B: mutual fee-shifting
        findings += scan_pattern(
            _P_B, doc_text, _LAYER, "B", Severity.MEDIUM, doc_hash,
            A.ARMENDARIZ, "enforcement_cost_asymmetry", 2, _REMEDY_FEE,
            notes="Mutual fee-shifting -- nominally symmetric but asymmetric when party resources diverge.",
        )

        # C: consumer bears arbitration costs
        has_consumer_cost = bool(_P_C_COST.search(text_lower))
        has_company_pay = bool(_P_C_COMPANY_PAY.search(text_lower))
        if has_consumer_cost and not has_company_pay:
            m = _P_C_COST.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER, sub="C", sev=Severity.HIGH, doc_hash=doc_hash,
                        text=doc_text, match_start=m.start(), match_end=m.end(),
                        anchor=A.ARMENDARIZ, axis="enforcement_cost_asymmetry", delta=4,
                        remedy_channels=_REMEDY_COST,
                        notes="Consumer bears arbitration costs with no company payment commitment.",
                    )
                )

        # D: non-disparagement / gag clause
        findings += scan_pattern(
            _P_D, doc_text, _LAYER, "D", Severity.HIGH, doc_hash,
            A.CCP_1001, "enforcement_cost_asymmetry", 4, _REMEDY_GAG,
            notes="Gag/non-disparagement clause -- Cal. Code Civ. Proc. 1001 bans consumer NDAs in settlements.",
        )

        # E: discovery limitation
        findings += scan_pattern(
            _P_E, doc_text, _LAYER, "E", Severity.MEDIUM, doc_hash,
            A.ARMENDARIZ, "enforcement_cost_asymmetry", 2, _REMEDY_DISCOVERY,
            notes="Discovery limitation -- Armendariz requires adequate discovery for effective vindication.",
        )

        # F: arbitration outcome confidentiality on consumer
        findings += scan_pattern(
            _P_F, doc_text, _LAYER, "F", Severity.MEDIUM, doc_hash,
            A.ARMENDARIZ, "enforcement_cost_asymmetry", 2, _REMEDY_CONF,
            notes="Confidentiality on arbitration outcome imposed on consumer -- suppresses public signal.",
        )

        # G: arbitration present but no CCP 1281.97/98 acknowledgment
        has_arb = bool(_P_G_ARB.search(text_lower))
        has_1281 = bool(_P_G_1281.search(text_lower))
        if has_arb and not has_1281:
            m = _P_G_ARB.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER, sub="G", sev=Severity.HIGH, doc_hash=doc_hash,
                        text=doc_text, match_start=m.start(), match_end=m.end(),
                        anchor=A.CCP_1281_97, axis="enforcement_cost_asymmetry", delta=4,
                        remedy_channels=_REMEDY_1281,
                        notes="Arbitration clause present with no CCP 1281.97/98 fee-payment acknowledgment.",
                    )
                )

        return findings
