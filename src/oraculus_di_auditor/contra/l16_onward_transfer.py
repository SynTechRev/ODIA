"""L-16 Onward Transfer detector (sub-detectors A through H).

Characterizes the drafter's asserted rights to transfer personal information
to third parties, distinguishing sale, behavioral advertising sharing, service
provider and contractor transfers, affiliate transfers, data broker transfers,
government disclosures, and merger-and-acquisition transfers.

Sub-detectors:
  A -- Sale of personal information (CCPA 1798.140(ad) broad definition)
  B -- Sharing for cross-context behavioral advertising (CCPA 1798.140(ah))
  C -- Service provider transfers with contractual restrictions
  D -- Contractor transfers (CCPA 1798.140(j))
  E -- Affiliate transfers with no substantive limitation
  F -- Data broker transfers (California Delete Act trigger)
  G -- Government / law enforcement disclosure
  H -- Merger, acquisition, or asset transfer

Source: C.O.N.T.R.A. Framework V1.0 Section 4.6, Handoff Spec V1.0 Section 5.6
"""

from __future__ import annotations

import re

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import Finding, Severity

_LAYER = "L-16"

_DATA = r"(?:personal\s+(?:information|data)|your\s+(?:data|information)|consumer\s+data|user\s+(?:data|information))"

_P_A = re.compile(
    r"\b(?:sell|sale|sold)\b.{0,150}\b" + _DATA + r"\b"
    r"|\b" + _DATA + r"\b.{0,150}\b(?:sold|sell|sale)\b",
    re.DOTALL,
)

_P_B = re.compile(
    r"\b(?:cross.?context\s+behavioral\s+advertising|behavioral\s+advertising"
    r"|target(?:ed)?\s+advertising|interest.?based\s+advertising)\b"
    r"|\bshare\w*\b.{0,200}\b(?:behavioral\s+advertising|targeted\s+ads?"
    r"|interest.?based\s+(?:advertising|ads?))\b",
    re.DOTALL,
)

_P_C = re.compile(
    r"\bservice\s+provider\w*\b.{0,300}\b" + _DATA + r"\b"
    r"|\b" + _DATA + r"\b.{0,300}\bservice\s+provider\w*\b",
    re.DOTALL,
)

_P_D = re.compile(
    r"\bcontractor\w*\b.{0,200}\b" + _DATA + r"\b"
    r"|\b" + _DATA + r"\b.{0,200}\bcontractor\w*\b",
    re.DOTALL,
)

_P_E = re.compile(
    r"\b(?:affiliates?|subsidiaries|subsidiary|related\s+companies?"
    r"|parent\s+company|corporate\s+family)\b.{0,200}"
    r"\b(?:share|transfer|provide|disclose|access|receive)\w*\b.{0,100}\b"
    + _DATA
    + r"\b"
    r"|\b" + _DATA + r"\b.{0,200}"
    r"\b(?:affiliates?|subsidiaries|related\s+companies?|parent\s+company)\b",
    re.DOTALL,
)

_P_F = re.compile(
    r"\b(?:data\s+broker"
    r"|sell\w*\b.{0,50}\b(?:personal|consumer)\s+(?:information|data)"
    r"|(?:personal|consumer)\s+(?:information|data)\b.{0,100}\b(?:sold|transferred|licensed)\b.{0,100}\bdata\s+broker)\b",
    re.DOTALL,
)

_P_G_NARROW = re.compile(
    r"\b(?:law\s+enforcement|government(?:al)?\s+(?:authorit|agenc|request)|court\s+order"
    r"|legal\s+process|subpoena|search\s+warrant)\b.{0,200}"
    r"\b(?:required\s+by\s+(?:law|legal|court|statute)|pursuant\s+to\s+(?:law|legal\s+process))\b",
    re.DOTALL,
)

_P_G_BROAD = re.compile(
    r"\b(?:we\s+)?(?:may|could|might|determine|choose|decide)\w*\b.{0,80}"
    r"\b(?:disclose|share|provide|release|report|cooperate)\w*\b.{0,200}"
    r"\b(?:law\s+enforcement|government\w*|agenc\w*|authorit\w*|investigat\w*)\b"
    r"|\b(?:law\s+enforcement|government\w*)\b.{0,200}"
    r"\b(?:we\s+)?(?:may|could|might)\b.{0,80}"
    r"\b(?:disclose|share|provide|release|report)\w*\b",
    re.DOTALL,
)

_P_H = re.compile(
    r"\b(?:merger|acquisition|sale\s+of\s+(?:the\s+)?(?:company|business|assets?)"
    r"|reorganization|bankruptcy|change\s+of\s+(?:control|ownership)"
    r"|transfer\s+of\s+(?:business|assets?))\b.{0,300}"
    r"\b(?:personal\s+(?:information|data)|your\s+(?:data|information)"
    r"|transferred|assign(?:ed)?)\b",
    re.DOTALL,
)

_REMEDY_TRANSFER = ["CCPA_opt_out", "CPPA_complaint", "AG_complaint"]
_REMEDY_BROKER = ["California_Delete_Act_DROP", "CPPA_complaint", "AG_complaint"]
_REMEDY_GOV = ["AG_complaint"]


class L16OnwardTransfer:
    """L-16 detector: Onward Transfer (sub-detectors A through H)."""

    layer: str = _LAYER

    def __init__(self) -> None:
        pass

    def scan(self, doc_text: str, doc_meta: dict) -> list[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        findings: list[Finding] = []
        findings += scan_pattern(
            _P_A,
            doc_text,
            _LAYER,
            "A",
            Severity.HIGH,
            doc_hash,
            A.CCPA_140,
            "data_extraction_depth",
            4,
            _REMEDY_TRANSFER,
            notes="Sale of personal information; CCPA 1798.140(ad) broad definition triggers opt-out.",
        )
        findings += scan_pattern(
            _P_B,
            doc_text,
            _LAYER,
            "B",
            Severity.HIGH,
            doc_hash,
            A.CCPA_140,
            "data_extraction_depth",
            4,
            _REMEDY_TRANSFER + ["CCPA_opt_out"],
            notes="Sharing for cross-context behavioral advertising (CCPA 1798.140(ah)) triggers separate opt-out.",
        )
        findings += scan_pattern(
            _P_C,
            doc_text,
            _LAYER,
            "C",
            Severity.LOW,
            doc_hash,
            A.CCPA_140,
            "data_extraction_depth",
            1,
            _REMEDY_TRANSFER,
            notes="Service provider transfer -- CCPA allows but imposes contractual restrictions.",
        )
        findings += scan_pattern(
            _P_D,
            doc_text,
            _LAYER,
            "D",
            Severity.MEDIUM,
            doc_hash,
            A.CCPA_140,
            "data_extraction_depth",
            2,
            _REMEDY_TRANSFER,
            notes="Contractor transfer per CCPA 1798.140(j) -- verify contractual restrictions.",
        )
        findings += scan_pattern(
            _P_E,
            doc_text,
            _LAYER,
            "E",
            Severity.MEDIUM,
            doc_hash,
            A.CCPA_135,
            "data_extraction_depth",
            2,
            _REMEDY_TRANSFER,
            notes="Affiliate transfer with no substantive limitation -- corporate structure used as data-laundering vector.",
        )
        findings += scan_pattern(
            _P_F,
            doc_text,
            _LAYER,
            "F",
            Severity.HIGH,
            doc_hash,
            A.DELETE_ACT,
            "data_extraction_depth",
            4,
            _REMEDY_BROKER,
            notes="Data broker transfer triggers California Delete Act registration and deletion obligations.",
        )
        # G: government disclosure -- narrow (required by law) vs broad (voluntary)
        text_lower = doc_text.lower()
        has_narrow = bool(_P_G_NARROW.search(text_lower))
        has_broad = bool(_P_G_BROAD.search(text_lower))
        if has_broad and not has_narrow:
            m = _P_G_BROAD.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER,
                        sub="G",
                        sev=Severity.MEDIUM,
                        doc_hash=doc_hash,
                        text=doc_text,
                        match_start=m.start(),
                        match_end=m.end(),
                        anchor=A.CCPA_130,
                        axis="data_extraction_depth",
                        delta=2,
                        remedy_channels=_REMEDY_GOV,
                        notes="Discretionary (not legally-compelled) government disclosure.",
                    )
                )
        elif has_narrow:
            m = _P_G_NARROW.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER,
                        sub="G",
                        sev=Severity.LOW,
                        doc_hash=doc_hash,
                        text=doc_text,
                        match_start=m.start(),
                        match_end=m.end(),
                        anchor=A.CCPA_130,
                        axis="data_extraction_depth",
                        delta=1,
                        remedy_channels=_REMEDY_GOV,
                        notes="Government disclosure limited to legal process -- standard practice.",
                    )
                )
        findings += scan_pattern(
            _P_H,
            doc_text,
            _LAYER,
            "H",
            Severity.LOW,
            doc_hash,
            A.CCPA_130,
            "data_extraction_depth",
            1,
            _REMEDY_TRANSFER,
            notes="M&A transfer disclosed -- standard but data may pass to successor without renewed consent.",
        )
        return findings
