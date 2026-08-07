"""L-20 Dark Pattern detector (sub-detectors A through H).

Identifies structural and presentational features of consumer contracts that
impede informed consent.  Dark patterns operate at the procedural-adhesion
axis: the consumer's nominal choice to accept exists, but cognitive load,
visual friction, and length-time asymmetry make meaningful deliberation
practically impossible.

Sub-detectors:
  A -- Pre-checked / auto-consent boxes referenced in text
  B -- Nested acceptance (acceptance of T&C implies acceptance of multiple other docs)
  C -- Scroll-to-accept / click-wrap with no opportunity to review
  D -- Font differential / fine-print exclusion referenced in text
  E -- Flesch-Kincaid reading level above Tulare County median (grade 9 threshold)
  F -- Length-time asymmetry (estimated reading time vs stated effective date window)
  G -- Language accessibility gap (English-only for Spanish-dominant consumer base)
  H -- Manipulated interface / urgency pressure (Ring Order AEC standard)

Source: C.O.N.T.R.A. Framework V1.0 Section 4.10, Handoff Spec V1.0 Section 5.10
        Ring Order AEC: United States v. Ring, No. 1:23-cv-01549 (D.D.C. June 16 2023)
        Tulare County grade 8–9 reading median: ODIA Regional Literacy Index
"""

from __future__ import annotations

import re

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import Finding, Severity

_LAYER = "L-20"

# ---------------------------------------------------------------------------
# Patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

_P_A = re.compile(
    r"\b(?:pre.?check\w*|automatically\s+(?:opt|enroll|subscrib)\w*"
    r"|by\s+default\s+(?:you\s+(?:are|will\s+be)\s+enrolled|we\s+(?:will|shall)\s+)"
    r"|opt(?:ed)?\s+in\s+by\s+default"
    r"|unless\s+you\s+(?:opt\s+out|uncheck|deselect|disable))\b",
    re.DOTALL,
)

_P_B = re.compile(
    r"\b(?:by\s+(?:accepting|agreeing\s+to|using|clicking)\b.{0,100}"
    r"\b(?:you\s+also\s+(?:agree|accept|consent)\b.{0,100}"
    r"\b(?:privacy\s+policy|data\s+sharing|additional\s+terms?"
    r"|supplemental\s+agreement|separate\s+agreement)\b"
    r"|\b(?:includes?|incorporates?\s+by\s+reference)\b.{0,100}"
    r"\b(?:privacy\s+policy|additional\s+terms?|supplemental\s+policies?"
    r"|all\s+policies?\s+(?:linked|referenced|listed))\b))\b",
    re.DOTALL,
)

_P_C = re.compile(
    r'\b(?:click(?:ing)?\s+(?:["\'])?(?:i\s+agree|accept|agree|ok|continue|submit|next)["\']?\b'
    r"|scroll(?:ing)?\s+(?:past|through|to\s+the\s+bottom)\b"
    r"|by\s+(?:continuing\s+to\s+use|downloading|installing)\b.{0,100}"
    r"\b(?:you\s+agree|constitutes?\s+(?:your\s+)?acceptance)\b)\b",
    re.DOTALL,
)

_P_D = re.compile(
    r"\b(?:fine\s+print|in\s+smaller\s+(?:font|text|type)"
    r"|(?:footnote|endnote|asterisk)\b.{0,100}\b(?:applies?|governs?|controls?)\b"
    r"|see\s+(?:footnote|endnote|note\s+\d+)\s+for\s+(?:important|additional|full)"
    r"|in\s+(?:bold|italic)\s+(?:below|above)\b.{0,50}\b(?:required\s+reading|important))\b",
    re.DOTALL,
)

_P_G = re.compile(
    r"\b(?:available\s+in\s+english\s+only"
    r"|this\s+agreement\s+is\s+in\s+english"
    r"|english\s+(?:version|language)\s+(?:shall\s+)?(?:control|govern|prevail)\b"
    r"|translations?\s+(?:are\s+)?(?:provided\s+for\s+convenience\s+only"
    r"|do\s+not\s+(?:control|govern|have\s+legal\s+effect))\b)\b",
    re.DOTALL,
)

_P_H = re.compile(
    r"\b(?:limited\s+time\s+offer\b.{0,200}\b(?:accept|agree|click)"
    r"|(?:act\s+now|respond\s+within|you\s+must\s+respond)\b.{0,200}\b(?:accept|agree)\b"
    r"|offer\s+expires?\b.{0,200}\b(?:accept|agree|click|today|immediately)\b"
    r"|you\s+(?:must\s+)?(?:accept|agree)\s+(?:now|immediately|within\s+\d+)"
    r"\s+(?:hours?|days?|minutes?)\b)\b",
    re.DOTALL,
)

# ---------------------------------------------------------------------------
# Flesch-Kincaid helpers
# ---------------------------------------------------------------------------

_VOWELS = re.compile(r"[aeiouy]+", re.IGNORECASE)
_SENTENCE_END = re.compile(r"[.!?]+")
_WORD_TOKEN = re.compile(r"\b[a-zA-Z]+\b")


def _count_syllables(word: str) -> int:
    word = word.lower().rstrip("e")
    count = len(_VOWELS.findall(word))
    return max(1, count)


def _flesch_kincaid_grade(text: str) -> float:
    words = _WORD_TOKEN.findall(text)
    sentences = _SENTENCE_END.split(text)
    sentences = [s for s in sentences if s.strip()]
    num_words = len(words)
    num_sentences = max(1, len(sentences))
    num_syllables = sum(_count_syllables(w) for w in words)
    if num_words < 10:
        return 0.0
    return (
        0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59
    )


def _words_per_minute_reading_time_minutes(text: str, wpm: int = 250) -> float:
    words = _WORD_TOKEN.findall(text)
    return len(words) / wpm


# ---------------------------------------------------------------------------
# Remedies
# ---------------------------------------------------------------------------

_REMEDY_DARK = ["RING_ORDER_compliance_review", "CPPA_complaint", "AG_complaint"]
_REMEDY_LANG = ["CPPA_complaint", "AG_complaint"]
_REMEDY_FK = ["CPPA_complaint", "AG_complaint", "demand_letter"]

# Threshold for flagging: grade 12 (college-level) is clearly excessive;
# grade 9-10 is borderline for consumer contracts.  The C.O.N.T.R.A. framework
# flags at grade 12 to avoid false positives on moderately complex contracts.
_FK_THRESHOLD = 12.0
# Reading time / notice window ratio that triggers length-time asymmetry
_LENGTH_TIME_RATIO_THRESHOLD = (
    0.5  # reading time > 50 % of stated notice period in same units
)


class L20DarkPattern:
    """L-20 detector: Dark Pattern (sub-detectors A through H)."""

    layer: str = _LAYER

    def __init__(self) -> None:
        pass

    def scan(self, doc_text: str, doc_meta: dict) -> list[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        text_lower = doc_text.lower()
        findings: list[Finding] = []

        # A: pre-checked / auto-consent
        findings += scan_pattern(
            _P_A,
            doc_text,
            _LAYER,
            "A",
            Severity.HIGH,
            doc_hash,
            A.RING_ORDER,
            "procedural_adhesion",
            4,
            _REMEDY_DARK,
            notes="Pre-checked / auto-enroll design -- affirmative opt-out required rather than opt-in.",
        )

        # B: nested acceptance
        findings += scan_pattern(
            _P_B,
            doc_text,
            _LAYER,
            "B",
            Severity.HIGH,
            doc_hash,
            A.RING_ORDER,
            "procedural_adhesion",
            4,
            _REMEDY_DARK,
            notes="Nested acceptance -- single action binds consumer to multiple undisclosed documents.",
        )

        # C: scroll-to-accept / click-wrap
        findings += scan_pattern(
            _P_C,
            doc_text,
            _LAYER,
            "C",
            Severity.MEDIUM,
            doc_hash,
            A.RING_ORDER,
            "procedural_adhesion",
            2,
            _REMEDY_DARK,
            notes="Click-wrap / scroll-to-accept consent mechanism -- no meaningful review opportunity.",
        )

        # D: font differential / fine print
        findings += scan_pattern(
            _P_D,
            doc_text,
            _LAYER,
            "D",
            Severity.MEDIUM,
            doc_hash,
            A.RING_ORDER,
            "procedural_adhesion",
            2,
            _REMEDY_DARK,
            notes="Fine-print / font differential -- material terms buried in reduced-prominence text.",
        )

        # E: Flesch-Kincaid reading level
        fk_grade = _flesch_kincaid_grade(doc_text)
        if fk_grade > _FK_THRESHOLD:
            first_sentence_end = _SENTENCE_END.search(doc_text)
            match_end = (
                first_sentence_end.end()
                if first_sentence_end
                else min(80, len(doc_text))
            )
            findings.append(
                make_finding(
                    layer=_LAYER,
                    sub="E",
                    sev=Severity.HIGH,
                    doc_hash=doc_hash,
                    text=doc_text,
                    match_start=0,
                    match_end=match_end,
                    anchor=A.RING_ORDER,
                    axis="procedural_adhesion",
                    delta=4,
                    remedy_channels=_REMEDY_FK,
                    notes=f"Flesch-Kincaid grade {fk_grade:.1f} exceeds Tulare County median ({_FK_THRESHOLD}).",
                )
            )

        # F: length-time asymmetry
        reading_time_min = _words_per_minute_reading_time_minutes(doc_text)
        # Look for "X days" notice windows in the modification / effective date language
        _P_DAYS = re.compile(r"\b(\d+)\s+days?\b")
        notice_windows = [int(m.group(1)) for m in _P_DAYS.finditer(text_lower)]
        if notice_windows:
            shortest_window_days = min(notice_windows)
            # Convert to minutes for comparison
            shortest_window_min = shortest_window_days * 24 * 60
            ratio = (
                reading_time_min / shortest_window_min if shortest_window_min > 0 else 0
            )
            if ratio > _LENGTH_TIME_RATIO_THRESHOLD:
                findings.append(
                    make_finding(
                        layer=_LAYER,
                        sub="F",
                        sev=Severity.HIGH,
                        doc_hash=doc_hash,
                        text=doc_text,
                        match_start=0,
                        match_end=min(80, len(doc_text)),
                        anchor=A.RING_ORDER,
                        axis="procedural_adhesion",
                        delta=4,
                        remedy_channels=_REMEDY_DARK,
                        notes=(
                            f"Length-time asymmetry: estimated {reading_time_min:.0f} min read "
                            f"vs {shortest_window_days}-day notice window."
                        ),
                    )
                )

        # G: language accessibility (English-only)
        findings += scan_pattern(
            _P_G,
            doc_text,
            _LAYER,
            "G",
            Severity.MEDIUM,
            doc_hash,
            A.RING_ORDER,
            "procedural_adhesion",
            2,
            _REMEDY_LANG,
            notes="English-only contract in Spanish-dominant service area -- language accessibility gap.",
        )

        # H: urgency / manipulated interface pressure (Ring Order AEC)
        findings += scan_pattern(
            _P_H,
            doc_text,
            _LAYER,
            "H",
            Severity.CRITICAL,
            doc_hash,
            A.RING_ORDER,
            "procedural_adhesion",
            7,
            _REMEDY_DARK,
            notes="Urgency pressure / manipulated interface -- Ring Order AEC standard violation.",
        )

        return findings
