"""L-13 Unilateral Modification detector (sub-detectors A through E).

Identifies provisions that allow the drafter to amend terms without meaningful
consumer consent, using notice methods that fall short of adequate disclosure,
or that bind consumers retroactively or without an opt-out path.

Sub-detectors:
  A -- Unilateral right to modify terms reserved by drafter
  B -- Notice by website posting only (no direct / advance communication)
  C -- Continued use construed as acceptance of modified terms
  D -- Retroactive application of modifications
  E -- No opt-out mechanism offered upon material modification

Source: C.O.N.T.R.A. Framework V1.0 Section 4.3, Handoff Spec V1.0 Section 5.3
"""

from __future__ import annotations

import re
from typing import List

from . import anchors as A
from ._utils import scan_pattern
from .base import Finding, Severity

_LAYER = "L-13"

# ---------------------------------------------------------------------------
# Compiled patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

_P_A = re.compile(
    r"\b(?:we\s+(?:may|reserve\s+the\s+right\s+to|can|will)"
    r"|(?:company|service\s+provider|we)\s+(?:may|reserves?|can)\s+(?:at\s+any\s+time\s+)?"
    r"(?:modify|change|update|revise|amend|alter)\s+"
    r"(?:these\s+)?(?:terms?|agreement|policy|conditions?|provisions?))\b"
)

_P_B = re.compile(
    r"\b(?:post(?:ing|ed)?\s+(?:an?\s+)?(?:updated?\s+)?(?:notice|version|revision)\s+"
    r"(?:on|to)\s+(?:our\s+)?(?:website|site|app|portal|platform)"
    r"|notif(?:y|ied|ication)\s+(?:you\s+)?(?:by\s+)?(?:updating?|posting)\s+"
    r"(?:to\s+)?(?:our\s+)?(?:website|site|app|portal|platform)"
    r"|such\s+(?:posting|update|revision)\s+(?:on|to)\s+(?:our\s+)?(?:website|site)"
    r"\s+(?:constitutes?|shall\s+be\s+deemed)\s+(?:notice|notification)"
    r"|notif\w*\b.{0,150}\bby\s+post\w*\b.{0,150}"
    r"\b(?:website|site|app|portal|platform)\b)\b",
    re.DOTALL,
)

_P_C = re.compile(
    r"\b(?:continu(?:ed|ing)\s+(?:to\s+)?(?:use|access|visit|engage\s+with)"
    r"|your\s+(?:continued|ongoing)\s+use"
    r"|by\s+(?:continu(?:ed|ing)\s+(?:to\s+)?)?(?:using|accessing))\b"
    r".{0,200}"
    r"\b(?:constitutes?|means?|indicates?|signifies?|shall\s+be\s+deemed?|"
    r"is\s+deemed?|implies?)\b"
    r".{0,100}"
    r"\b(?:accept(?:ance|ing)|agree(?:ment|ing|d)|consent|assent)\b",
    re.DOTALL,
)

_P_D = re.compile(
    r"\b(?:retroactive(?:ly)?|apply\s+(?:retroactively\s+)?to\s+(?:all|any)\s+"
    r"(?:prior|previous|past|existing|pending)\s+(?:disputes?|claims?|transactions?)"
    r"|effective\s+(?:immediately|upon\s+posting).{0,100}"
    r"\b(?:prior|past|pending|existing)\b"
    r"|modifications?\s+(?:shall|will)\s+apply\s+to\s+(?:all\s+)?(?:prior|past))\b",
    re.DOTALL,
)

_P_E_MOD = re.compile(
    r"\b(?:modify|change|update|revise|amend|alter)\b.{0,100}"
    r"\b(?:terms?|agreement|policy|conditions?)\b"
)
_P_E_OPTOUT = re.compile(
    r"\b(?:opt.?out|opt(?:ing)?\s+out|close\s+your\s+account|terminate\s+your\s+"
    r"(?:account|use|access)|stop\s+using|cease\s+using|disagree)\b"
)

_REMEDY_MOD = ["FTC_complaint", "AG_complaint", "CFPB_complaint"]
_REMEDY_CONSENT = ["AG_complaint", "FTC_complaint"]


class L13UnilateralModification:
    """L-13 detector: Unilateral Modification (sub-detectors A through E)."""

    layer: str = _LAYER

    def __init__(self, llm_client=None) -> None:
        self._llm = llm_client

    def scan(self, doc_text: str, doc_meta: dict) -> List[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        findings: List[Finding] = []
        findings += scan_pattern(
            _P_A, doc_text, _LAYER, "A", Severity.HIGH, doc_hash,
            A.DOUGLAS_USDC, "modification_and_consent", 4,
            _REMEDY_MOD,
            notes="Drafter reserves unilateral right to modify terms.",
        )
        findings += scan_pattern(
            _P_B, doc_text, _LAYER, "B", Severity.MEDIUM, doc_hash,
            A.RING_ORDER, "modification_and_consent", 2,
            _REMEDY_CONSENT,
            notes="Website-posting-only notice is insufficient for material changes.",
        )
        findings += scan_pattern(
            _P_C, doc_text, _LAYER, "C", Severity.CRITICAL, doc_hash,
            A.OTO_KHO, "modification_and_consent", 7,
            _REMEDY_CONSENT,
            notes="Continued use = acceptance eliminates meaningful consent.",
        )
        findings += scan_pattern(
            _P_D, doc_text, _LAYER, "D", Severity.HIGH, doc_hash,
            A.SANCHEZ_VALENCIA, "modification_and_consent", 4,
            _REMEDY_MOD,
            notes="Retroactive modification application denies ability to reject changed terms.",
        )
        # E: modification language present but no opt-out path
        text_lower = doc_text.lower()
        has_mod = bool(_P_E_MOD.search(text_lower))
        has_optout = bool(_P_E_OPTOUT.search(text_lower))
        if has_mod and not has_optout:
            m = _P_E_MOD.search(text_lower)
            if m:
                from ._utils import make_finding
                findings.append(
                    make_finding(
                        layer=_LAYER,
                        sub="E",
                        sev=Severity.LOW,
                        doc_hash=doc_hash,
                        text=doc_text,
                        match_start=m.start(),
                        match_end=m.end(),
                        anchor=A.SONIC_CALABASAS,
                        axis="modification_and_consent",
                        delta=1,
                        remedy_channels=_REMEDY_CONSENT,
                        notes="Modification language present with no opt-out mechanism disclosed.",
                    )
                )
        return findings
