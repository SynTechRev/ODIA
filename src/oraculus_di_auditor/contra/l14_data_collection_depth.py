"""L-14 Data Collection Depth detector (CCPA taxonomy sub-detectors A through I).

Maps privacy notice data collection disclosures to California Consumer Privacy
Act categories. Each triggered category produces a Finding that populates the
data_extraction_depth CASI axis. Severity scales with privacy sensitivity and
with California Delete Act and CCPA/CPRA SPI treatment obligations.

Sub-detectors (CCPA category codes):
  A -- Identifiers (Cat A): name, email, phone, IP, device ID
  B -- Personal records (Cat B): financial, medical, employment, insurance
  C -- Protected classification characteristics (Cat C)
  D -- Commercial / transaction information (Cat D)
  E -- Biometric information (Cat E / SPI): fingerprint, facial recognition
  F -- Internet / network activity (Cat F): browsing, search, clicks
  G -- Geolocation data (Cat G / SPI): precise location, GPS history
  H -- Inferences (Cat K): profiles, segments, predictions
  I -- Sensitive Personal Information aggregate detection (SPI / 1798.121)

Source: C.O.N.T.R.A. Framework V1.0 Section 4.4, Handoff Spec V1.0 Section 5.4
        CCPA: Cal. Civ. Code section 1798.140
        SPI:  Cal. Civ. Code section 1798.121
"""

from __future__ import annotations

import re

from . import anchors as A
from ._utils import scan_pattern
from .base import Finding, Severity

_LAYER = "L-14"

# ---------------------------------------------------------------------------
# Patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

_P_A = re.compile(
    r"\b(?:(?:collect|gather|receiv|obtain|process)\w*\s+(?:your\s+)?)"
    r"(?:[^.]{0,60}\b)?"
    r"\b(?:name|email\s+address|phone\s+number|postal\s+address"
    r"|social\s+security|tax\s+(?:id|identification)|driver.?s?\s+license"
    r"|passport\s+number|account\s+number|ip\s+address|device\s+identifier"
    r"|online\s+identifier|customer\s+(?:id|number))\b"
)

_P_B = re.compile(
    r"\b(?:financial\s+(?:information|data|records?|account|history)"
    r"|bank\s+(?:account|information|data)"
    r"|credit\s+(?:card|report|score|history|information)"
    r"|health\s+(?:information|data|record|condition|status|history)"
    r"|medical\s+(?:information|data|record|history|condition)"
    r"|employment\s+(?:history|information|record|status)"
    r"|insurance\s+(?:information|data|record|policy)"
    r"|income\s+(?:information|data|level|range))\b"
)

_P_C = re.compile(
    r"\b(?:race|ethnicity|national\s+origin|religion|religious\s+belief"
    r"|age\s+(?:or\s+date\s+of\s+birth|information)"
    r"|gender\s+(?:identity|expression|information)"
    r"|sexual\s+orientation|disability\s+(?:status|information)"
    r"|pregnancy\s+(?:status|information)|marital\s+status"
    r"|citizenship\s+status|veteran\s+status)\b"
)

_P_D = re.compile(
    r"\b(?:purchase\s+(?:history|information|record|data)"
    r"|transaction\s+(?:history|information|record|data)"
    r"|products?\s+(?:you\s+)?(?:buy|bought|purchased|order(?:ed)?)"
    r"|services?\s+(?:you\s+)?(?:use|used|subscribe|subscribed)"
    r"|shopping\s+(?:history|behavior|cart|bag))\b"
)

_P_E = re.compile(
    r"\b(?:biometric\s+(?:information|data|identifier|template)"
    r"|fingerprint(?:s?)\b"
    r"|face(?:ial)?\s+recognition|facial\s+(?:scan|image|template|geometry)"
    r"|retina\s+(?:scan|data)|iris\s+(?:scan|data)"
    r"|voice\s+(?:print|recognition|pattern|biometric)"
    r"|hand\s+geometry|gait\s+(?:analysis|recognition)"
    r"|keystroke\s+(?:dynamics|pattern)|dna\b)\b"
)

_P_F = re.compile(
    r"\b(?:browsing\s+(?:history|data|behavior|activity)"
    r"|search\s+(?:history|queries?|terms?|data)"
    r"|website\s+(?:visits?|interactions?|usage)"
    r"|(?:pages?|links?|ads?)\s+(?:clicked?|visited?|viewed?)"
    r"|(?:app|application)\s+(?:usage|interactions?|activity)"
    r"|time\s+spent\s+on|internet\s+(?:activity|usage|history))\b"
)

_P_G = re.compile(
    r"\b(?:geolocation\s+(?:data|information|history)"
    r"|location\s+(?:data|information|history|services?)"
    r"|gps\s+(?:data|information|location|coordinates?)"
    r"|precise\s+(?:location|geolocation)"
    r"|where\s+you\s+(?:are|go|travel|visit|have\s+been)"
    r"|tracking\s+(?:your\s+)?location|real.?time\s+location)\b"
)

_P_H = re.compile(
    r"\b(?:infer(?:ence)?s?\s+(?:about|regarding|from)"
    r"|predict(?:ions?|ive)\s+(?:model\w*|score\w*|analytics?)"
    r"|profil(?:e|es|ing)\s+(?:you|your|consumer|user|about)"
    r"|segment(?:ation)?\s+(?:based\s+on|of\s+your|of\s+users?)"
    r"|(?:build|create|develop)\s+(?:\w+\s+){0,2}(?:profile\w*|model\w*)"
    r"\s+(?:of|about)\s+(?:you|your|consumer|user)"
    r"|likelihood\s+(?:you\s+will|that\s+you)"
    r"|propensit(?:y|ies)\s+(?:to|for))\b"
)

# SPI: check for any two or more SPI sub-categories present
_SPI_PATTERNS = [
    re.compile(r"\b(?:biometric|fingerprint|facial\s+recognition|dna)\b"),
    re.compile(r"\b(?:geolocation|gps|precise\s+location)\b"),
    re.compile(
        r"\b(?:race|ethnicity|religious\s+belief|sexual\s+orientation|citizenship)\b"
    ),
    re.compile(r"\b(?:health|medical|genetic)\b"),
    re.compile(r"\b(?:financial\s+account|bank\s+account|credit\s+card)\b"),
    re.compile(
        r"\b(?:email\s+address|text\s+message|private\s+(?:communication|message))\b"
        r".{0,100}\b(?:password|credential|login|authentication)\b",
        re.DOTALL,
    ),
]

_REMEDY_DATA = ["CCPA_opt_out", "CCPA_delete_request", "CPPA_complaint"]
_REMEDY_SPI = ["CCPA_opt_out", "CCPA_delete_request", "CPPA_complaint", "AG_complaint"]


class L14DataCollectionDepth:
    """L-14 detector: Data Collection Depth (CCPA taxonomy, sub-detectors A-I)."""

    layer: str = _LAYER

    def __init__(self, llm_client=None) -> None:
        self._llm = llm_client

    def scan(self, doc_text: str, doc_meta: dict) -> list[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        findings: list[Finding] = []
        findings += scan_pattern(
            _P_A,
            doc_text,
            _LAYER,
            "A",
            Severity.LOW,
            doc_hash,
            A.CCPA_140,
            "data_extraction_depth",
            1,
            _REMEDY_DATA,
            notes="Category A identifiers collected (CCPA Cat A).",
        )
        findings += scan_pattern(
            _P_B,
            doc_text,
            _LAYER,
            "B",
            Severity.MEDIUM,
            doc_hash,
            A.CCPA_110,
            "data_extraction_depth",
            2,
            _REMEDY_DATA,
            notes="Personal records collected (CCPA Cat B).",
        )
        findings += scan_pattern(
            _P_C,
            doc_text,
            _LAYER,
            "C",
            Severity.HIGH,
            doc_hash,
            A.CCPA_110,
            "data_extraction_depth",
            4,
            _REMEDY_SPI,
            notes="Protected classification characteristics collected (CCPA Cat C).",
        )
        findings += scan_pattern(
            _P_D,
            doc_text,
            _LAYER,
            "D",
            Severity.LOW,
            doc_hash,
            A.CCPA_140,
            "data_extraction_depth",
            1,
            _REMEDY_DATA,
            notes="Commercial/transaction information collected (CCPA Cat D).",
        )
        findings += scan_pattern(
            _P_E,
            doc_text,
            _LAYER,
            "E",
            Severity.CRITICAL,
            doc_hash,
            A.CCPA_121,
            "data_extraction_depth",
            7,
            _REMEDY_SPI,
            notes="Biometric information collected -- SPI category; heightened CCPA obligations.",
        )
        findings += scan_pattern(
            _P_F,
            doc_text,
            _LAYER,
            "F",
            Severity.MEDIUM,
            doc_hash,
            A.CCPA_110,
            "data_extraction_depth",
            2,
            _REMEDY_DATA,
            notes="Internet/network activity collected (CCPA Cat F).",
        )
        findings += scan_pattern(
            _P_G,
            doc_text,
            _LAYER,
            "G",
            Severity.HIGH,
            doc_hash,
            A.CCPA_121,
            "data_extraction_depth",
            4,
            _REMEDY_SPI,
            notes="Geolocation / precise location data collected -- SPI category.",
        )
        findings += scan_pattern(
            _P_H,
            doc_text,
            _LAYER,
            "H",
            Severity.MEDIUM,
            doc_hash,
            A.CCPA_140,
            "data_extraction_depth",
            2,
            _REMEDY_DATA,
            notes="Inferential profiles / predictions drawn from personal data (CCPA Cat K).",
        )
        # I: SPI aggregate -- any two or more distinct SPI sub-types detected
        text_lower = doc_text.lower()
        spi_hits = [p for p in _SPI_PATTERNS if p.search(text_lower)]
        if len(spi_hits) >= 2:
            m = spi_hits[0].search(text_lower)
            if m:
                from ._utils import make_finding

                findings.append(
                    make_finding(
                        layer=_LAYER,
                        sub="I",
                        sev=Severity.CRITICAL,
                        doc_hash=doc_hash,
                        text=doc_text,
                        match_start=m.start(),
                        match_end=m.end(),
                        anchor=A.CCPA_121,
                        axis="data_extraction_depth",
                        delta=7,
                        remedy_channels=_REMEDY_SPI,
                        notes=(
                            f"Multiple SPI sub-types detected ({len(spi_hits)} of 6); "
                            f"Cal. Civ. Code 1798.121 heightened consent + CPPA audit obligations apply."
                        ),
                    )
                )
        return findings
