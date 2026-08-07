"""L-15 Data Retention detector (sub-detectors A through F).

Identifies inadequate, undefined, or asymmetric data retention provisions in
consumer contracts and privacy notices. Biometric data receives heightened
scrutiny. California Delete Act obligations are triggered where the entity
qualifies as a data broker (Cal. Civ. Code 1798.99.80 et seq.).

Sub-detectors:
  A -- No defined retention period for any collected personal data
  B -- Vague / indefinite retention language ("as long as necessary")
  C -- Third-party retention grants without consumer deletion path
  D -- Post-termination data retention disclosure
  E -- California Delete Act trigger (data broker indicators present)
  F -- Biometric data retention with no defined limit

Source: C.O.N.T.R.A. Framework V1.0 Section 4.5, Handoff Spec V1.0 Section 5.5
        Right to delete: Cal. Civ. Code section 1798.105
        Delete Act:      Cal. Civ. Code section 1798.99.80 et seq.
        SPI retention:   Cal. Civ. Code section 1798.121
"""

from __future__ import annotations

import re

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import Finding, Severity

_LAYER = "L-15"

# ---------------------------------------------------------------------------
# Patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

# Signals that data IS being collected / processed
_P_COLLECT = re.compile(
    r"\b(?:we\s+(?:collect|gather|receiv|obtain|process|store|retain|use)\w*"
    r"|your\s+(?:personal\s+)?(?:information|data)\s+(?:is|are|will\s+be)\s+"
    r"(?:collect|gather|receiv|obtain|process|stor|retain)\w*)\b"
)

# Explicit retention period language
_P_RETENTION_DEFINED = re.compile(
    r"\b(?:retain(?:ed)?\b.{0,80}\bfor\s+(?:no\s+more\s+than\s+|up\s+to\s+)?"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:days?|months?|years?)"
    r"|delet(?:ed?|ion)\b.{0,60}\b(?:within|after|in)\s+(?:\d+|one|two|three)\s+"
    r"(?:days?|months?|years?)"
    r"|kept\s+for\s+(?:no\s+more\s+than\s+|up\s+to\s+)?"
    r"(?:\d+|one|two|three)\s+(?:days?|months?|years?)"
    r"|stored\s+for\s+(?:no\s+more\s+than\s+|up\s+to\s+)?"
    r"(?:\d+|one|two|three)\s+(?:days?|months?|years?)"
    r"|purge(?:d)?\b.{0,30}\b(?:within|after)\s+(?:\d+|one|two|three)\s+(?:days?|months?|years?))\b",
    re.DOTALL,
)

_P_B = re.compile(
    r"\b(?:retain\w*|stor\w*|kept|hold\w*)\b.{0,120}\b"
    r"(?:as\s+long\s+as|as\s+(?:needed|necessary)"
    r"|for\s+the\s+duration\s+of"
    r"|for\s+(?:a\s+)?reasonable\s+(?:period|time|duration)"
    r"|for\s+(?:legitimate|legal|business|our)\s+(?:purposes?|needs?|requirements?|obligations?)"
    r"|indefinitely"
    r"|without\s+(?:a\s+)?(?:specific\s+)?(?:time\s+)?limit"
    r"|until\s+(?:no\s+longer\s+)?(?:needed|necessary|required|relevant))\b",
    re.DOTALL,
)

_P_C = re.compile(
    r"\b(?:share\w*\s+.{0,100}\b(?:third[-\s]?part(?:y|ies)|partner|vendor|affiliat)\w*"
    r"|third[-\s]?part(?:y|ies)\s+.{0,100}\b(?:retain|keep|store|maintain|hold)\w*)\b.{0,200}"
    r"\b(?:indefinitely|their\s+own|their\s+standard|according\s+to\s+their|"
    r"subject\s+to\s+their|own\s+(?:retention|policy|practices?|data))\b",
    re.DOTALL,
)

_P_D = re.compile(
    r"\b(?:(?:after|following|upon)\s+(?:termination|closure|cancellation|"
    r"deactivation|deletion\s+of\s+your\s+account|end\s+of\s+(?:the\s+)?(?:service|"
    r"agreement|relationship))\b.{0,300}"
    r"\b(?:we\s+may|data\s+(?:will|may)\s+be|we\s+(?:will|shall)\s+)?(?:retain|"
    r"keep|store|maintain|hold|preserve)\b"
    r"|we\s+may\s+retain\s+(?:your\s+)?(?:information|data|records?)\s+"
    r"(?:after|following|beyond|past)\b)",
    re.DOTALL,
)

_P_E = re.compile(
    r"\b(?:data\s+broker"
    r"|sell(?:ing)?\s+(?:personal|consumer)\s+(?:information|data)"
    r"|monetiz\w*\s+(?:personal|consumer|user)\s+(?:information|data)"
    r"|(?:personal|consumer)\s+(?:information|data)\s+"
    r"(?:sold|transferred|disclosed)\s+(?:to\s+)?(?:third\s+parties?|"
    r"partner(?:s|ing)?|buyer(?:s)?)"
    r"|license\s+(?:your|consumer|user)\s+(?:data|information)\s+to)\b"
)

_P_F_BIO = re.compile(
    r"\b(?:biometric|fingerprint|facial\s+recognition|retina|iris|"
    r"voice\s+(?:print|pattern)|dna)\b"
)
_P_F_RETENTION_LIMIT = re.compile(
    r"\b(?:delet\w*|purge\w*|destroy\w*)\b.{0,50}\b(?:within|after)\s+\d+"
    r"|\bretain\w*\b.{0,80}\bfor\s+(?:no\s+longer\s+than|no\s+more\s+than|up\s+to)"
    r"\s+\d+"
)

_REMEDY_RETENTION = ["CCPA_delete_request", "CPPA_complaint", "AG_complaint"]
_REMEDY_BROKER = ["California_Delete_Act_DROP", "CPPA_complaint", "AG_complaint"]
_REMEDY_BIO = ["CPPA_complaint", "AG_complaint", "CCPA_delete_request"]


class L15DataRetention:
    """L-15 detector: Data Retention (sub-detectors A through F)."""

    layer: str = _LAYER

    def __init__(self, llm_client=None) -> None:
        self._llm = llm_client

    def scan(self, doc_text: str, doc_meta: dict) -> list[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        text_lower = doc_text.lower()
        findings: list[Finding] = []

        # A: data collected but no defined retention period
        has_collection = bool(_P_COLLECT.search(text_lower))
        has_defined = bool(_P_RETENTION_DEFINED.search(text_lower))
        if has_collection and not has_defined:
            m = _P_COLLECT.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER,
                        sub="A",
                        sev=Severity.HIGH,
                        doc_hash=doc_hash,
                        text=doc_text,
                        match_start=m.start(),
                        match_end=m.end(),
                        anchor=A.CCPA_105,
                        axis="data_extraction_depth",
                        delta=4,
                        remedy_channels=_REMEDY_RETENTION,
                        notes="Data collection disclosed but no defined retention period.",
                    )
                )

        # B: vague retention language
        findings += scan_pattern(
            _P_B,
            doc_text,
            _LAYER,
            "B",
            Severity.MEDIUM,
            doc_hash,
            A.CCPA_105,
            "data_extraction_depth",
            2,
            _REMEDY_RETENTION,
            notes="Vague retention language fails CCPA 1798.105 specificity standard.",
        )

        # C: third-party retention grants without consumer deletion path
        findings += scan_pattern(
            _P_C,
            doc_text,
            _LAYER,
            "C",
            Severity.HIGH,
            doc_hash,
            A.CCPA_105,
            "data_extraction_depth",
            4,
            _REMEDY_RETENTION,
            notes="Data shared with third parties under their own retention policies.",
        )

        # D: post-termination retention
        findings += scan_pattern(
            _P_D,
            doc_text,
            _LAYER,
            "D",
            Severity.MEDIUM,
            doc_hash,
            A.CCPA_105,
            "data_extraction_depth",
            2,
            _REMEDY_RETENTION,
            notes="Post-termination data retention disclosed without consumer consent.",
        )

        # E: California Delete Act trigger
        findings += scan_pattern(
            _P_E,
            doc_text,
            _LAYER,
            "E",
            Severity.HIGH,
            doc_hash,
            A.DELETE_ACT,
            "data_extraction_depth",
            4,
            _REMEDY_BROKER,
            notes="Data broker indicators -- California Delete Act obligations may apply.",
        )

        # F: biometric data collected but no defined deletion limit
        has_bio = bool(_P_F_BIO.search(text_lower))
        has_bio_limit = bool(_P_F_RETENTION_LIMIT.search(text_lower))
        if has_bio and not has_bio_limit:
            m = _P_F_BIO.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER,
                        sub="F",
                        sev=Severity.CRITICAL,
                        doc_hash=doc_hash,
                        text=doc_text,
                        match_start=m.start(),
                        match_end=m.end(),
                        anchor=A.CCPA_121,
                        axis="data_extraction_depth",
                        delta=7,
                        remedy_channels=_REMEDY_BIO,
                        notes="Biometric data collected with no stated deletion deadline.",
                    )
                )

        return findings
