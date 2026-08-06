"""Corporate name normalization for entity registry fuzzy matching.

Collapses common suffix variants so that "AT&T Mobility LLC",
"AT&T Mobility L.L.C.", and "AT&T Mobility Limited Liability Company"
all reduce to the same comparison string before fuzzy matching.
"""

from __future__ import annotations

import re

_SUFFIX_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Limited Liability Company variants
    (re.compile(r"\bL\.L\.C\.?\b", re.IGNORECASE), "LLC"),
    (re.compile(r"\bLimited Liability Company\b", re.IGNORECASE), "LLC"),
    (re.compile(r"\bLimited Liability Corp(?:oration)?\b", re.IGNORECASE), "LLC"),
    # Incorporated variants
    (re.compile(r"\bInc(?:orporated)?\.?\b", re.IGNORECASE), "Inc"),
    # Corporation variants
    (re.compile(r"\bCorp(?:oration)?\.?\b", re.IGNORECASE), "Corp"),
    # Limited variants
    (re.compile(r"\bLtd\.?\b", re.IGNORECASE), "Ltd"),
    (re.compile(r"\bLimited\b", re.IGNORECASE), "Ltd"),
    # Company variants
    (re.compile(r"\bCo\.?\b", re.IGNORECASE), "Co"),
    # Partnership variants
    (re.compile(r"\bL\.P\.?\b", re.IGNORECASE), "LP"),
    (re.compile(r"\bLimited Partnership\b", re.IGNORECASE), "LP"),
    # Association / Services variants
    (re.compile(r"\bAssoc(?:iation)?\.?\b", re.IGNORECASE), "Assoc"),
]

# Ampersand is removed without a space so "AT&T" becomes "ATT" not "AT T"
_AMPERSAND = re.compile(r"\s*&\s*")
_PUNCT_STRIP = re.compile(r"[.,]")
_WHITESPACE = re.compile(r"\s+")


def normalize_corporate_suffix(name: str) -> str:
    """Normalize corporate suffix variants and punctuation for fuzzy comparison.

    Does NOT lowercase — rapidfuzz handles case insensitivity at match time.
    Returns a whitespace-normalized string suitable as a fuzzy-match input.
    """
    result = name
    for pattern, replacement in _SUFFIX_PATTERNS:
        result = pattern.sub(replacement, result)
    # Ampersand collapses without a space: "AT&T" -> "ATT", "AT & T" -> "ATT"
    result = _AMPERSAND.sub("", result)
    # Strip remaining punctuation that varies across data sources
    result = _PUNCT_STRIP.sub(" ", result)
    result = _WHITESPACE.sub(" ", result).strip()
    return result
