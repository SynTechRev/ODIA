"""Administrative Integrity Detector.

Detects administrative record-keeping failures in legislative management
systems: missing final actions, blank required fields, misfiled documents,
and retroactive authorizations. These structural anomalies indicate gaps
in the provenance chain regardless of the underlying action's validity.
"""

from __future__ import annotations

import re
from typing import Any

from .text_utils import extract_text_content

# Required metadata fields that must be present and non-empty
REQUIRED_METADATA_FIELDS = [
    "final_action",
    "status",
    "vote_result",
    "meeting_date",
    "agenda_number",
]

# Text signals of a completed/approved action
APPROVAL_SIGNALS = [
    "approved",
    "adopted",
    "passed",
    "enacted",
    "authorized",
]

# Misfiling indicators
MISFILING_KEYWORDS = [
    "misfiled",
    "wrong agenda",
    "incorrect item",
    "clerical error",
]

# Retroactive authorization patterns
_RETROACTIVE_PATTERN = re.compile(
    r"\bretroactive\b"
    r"|\bnunc\s+pro\s+tunc\b"
    r"|\bratified\s+after\b"
    r"|\bapproved\s+after\s+the\s+fact\b"
    r"|\bback[\s-]dated\b"
    r"|\beffective\s+prior\s+to\b",
    re.IGNORECASE,
)


def _is_blank(value: Any) -> bool:
    """Return True if value is None, empty string, or whitespace-only."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def detect_administrative_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify administrative integrity anomalies in a normalized document.

    Args:
        doc: Normalized document dict

    Returns:
        List of anomaly records; empty if none found.
    """
    anomalies: list[dict[str, Any]] = []

    if not isinstance(doc, dict):
        return anomalies

    # -----------------------------------------------------------------------
    # Check 1: Missing final_action despite approval signals in text
    # -----------------------------------------------------------------------
    final_action = doc.get("final_action")
    if _is_blank(final_action):
        text_content = extract_text_content(doc)
        text_lower = text_content.lower() if text_content else ""
        has_approval_signal = any(sig in text_lower for sig in APPROVAL_SIGNALS)

        if has_approval_signal:
            anomalies.append(
                {
                    "id": "admin:missing-final-action",
                    "issue": (
                        "Document text indicates approval but final_action "
                        "field is blank"
                    ),
                    "severity": "high",
                    "layer": "administrative",
                    "details": {
                        "final_action_value": final_action,
                        "approval_signals_found": [
                            sig for sig in APPROVAL_SIGNALS if sig in text_lower
                        ],
                    },
                }
            )

    # -----------------------------------------------------------------------
    # Check 2: Blank required metadata fields
    # -----------------------------------------------------------------------
    blank_fields = [f for f in REQUIRED_METADATA_FIELDS if _is_blank(doc.get(f))]
    # Always exclude final_action from this list if it was already handled
    # above — report it only once under missing-final-action.
    blank_fields_excluding_final_action = [
        f for f in blank_fields if f != "final_action"
    ]

    if blank_fields_excluding_final_action:
        anomalies.append(
            {
                "id": "admin:blank-required-fields",
                "issue": "Required metadata fields are blank or missing",
                "severity": "medium",
                "layer": "administrative",
                "details": {
                    "blank_fields": blank_fields_excluding_final_action,
                    "field_count": len(blank_fields_excluding_final_action),
                },
            }
        )

    # -----------------------------------------------------------------------
    # Check 3: Retroactive authorization language
    # -----------------------------------------------------------------------
    text_content = extract_text_content(doc)
    if text_content:
        retro_match = _RETROACTIVE_PATTERN.search(text_content)
        if retro_match:
            anomalies.append(
                {
                    "id": "admin:retroactive-authorization",
                    "issue": "Retroactive or back-dated authorization language detected",
                    "severity": "high",
                    "layer": "administrative",
                    "details": {
                        "matched_phrase": retro_match.group(0),
                        "position": retro_match.start(),
                    },
                }
            )

        # -------------------------------------------------------------------
        # Check 4: Misfiling indicators
        # -------------------------------------------------------------------
        text_lower = text_content.lower()
        misfiling_found = [kw for kw in MISFILING_KEYWORDS if kw in text_lower]
        if misfiling_found:
            anomalies.append(
                {
                    "id": "admin:potential-misfiling",
                    "issue": "Misfiling or document placement error indicator found",
                    "severity": "medium",
                    "layer": "administrative",
                    "details": {
                        "misfiling_indicators": misfiling_found,
                    },
                }
            )

    return anomalies
