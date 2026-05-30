"""Vote-Date Alignment Detector.

Flags temporal misalignment between when a legislative body authorized an
action and when that action was executed or became effective:

  * Retroactive approval language (nunc pro tunc, retroactive, effective [past])
  * Urgency item without a recorded urgency finding
  * High-value contract on consent calendar (bypasses individual vote)
  * Execution date preceding authorization date (from doc metadata)
  * Excessive gap between authorization and execution (>90 days)
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from .text_utils import extract_text_content
from .vendor_database import detect_consent_calendar

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

_RETROACTIVE = re.compile(
    r"\b(?:retroactive(?:ly)?|nunc\s+pro\s+tunc|effective\s+as\s+of\s+"
    r"(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4}|"
    r"ratif(?:y|ied|ication)\s+of\s+(?:prior|previous|earlier))\b",
    re.IGNORECASE,
)

_URGENCY = re.compile(
    r"\b(?:urgency\s+(?:ordinance|item|measure|statute)|"
    r"declared\s+an?\s+urgency|four-?fifths\s+vote|4\/5\s+vote|"
    r"immediate(?:ly)?\s+(?:effective|operative))\b",
    re.IGNORECASE,
)

_URGENCY_FINDING = re.compile(
    r"\b(?:urgency\s+finding|finding\s+of\s+urgency|"
    r"emergency\s+(?:exists|finding|declared)|"
    r"public\s+(?:health|safety|welfare)\s+(?:requires?|necessitates?))\b",
    re.IGNORECASE,
)

_ISO_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

_PROSE_DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b",
    re.IGNORECASE,
)

_HIGH_VALUE = re.compile(
    r"\$\s*(?:(?:\d{1,3},){2,}\d{3}|\d+\s*[MB](?:illion)?)",
    re.IGNORECASE,
)

_AUTHORIZATION_LABEL = re.compile(
    r"\b(?:authorized?|approved?|adopted?|authorized\s+on|"
    r"approval\s+date|action\s+date)\b",
    re.IGNORECASE,
)

_EXECUTION_LABEL = re.compile(
    r"\b(?:executed?|signed?|effective\s+date|commencement|"
    r"contract\s+date|agreement\s+date)\b",
    re.IGNORECASE,
)

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build(
    finding_id: str, issue: str, severity: str, **details: Any
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "issue": issue,
        "severity": severity,
        "layer": "vote_date_alignment",
        "details": details,
    }


def _parse_iso(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def _extract_dates_from_text(text: str) -> list[date]:
    """Extract all recognisable dates from prose text."""
    found: list[date] = []
    for m in _ISO_DATE.finditer(text):
        d = _parse_iso(m.group(1))
        if d:
            found.append(d)
    for m in _PROSE_DATE.finditer(text):
        try:
            month = _MONTHS[m.group(1).lower()]
            day = int(m.group(2))
            year = int(m.group(3))
            found.append(date(year, month, day))
        except (ValueError, KeyError):
            pass
    return found


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


def detect_vote_date_alignment_anomalies(  # noqa: C901
    doc: dict[str, Any],
) -> list[dict[str, Any]]:
    """Detect vote / authorization vs. execution date misalignment in *doc*."""
    findings: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return findings

    text = extract_text_content(doc) or ""
    if not text.strip():
        return findings

    # ------------------------------------------------------------------
    # 1. Retroactive approval language
    # ------------------------------------------------------------------
    retro_matches = _RETROACTIVE.findall(text)
    if retro_matches:
        findings.append(
            _build(
                "vote_date:retroactive-approval",
                "Retroactive approval language detected — action may have been "
                "executed before legislative authorization ('nunc pro tunc', "
                "'retroactive', or past-dated effective clause)",
                "high",
                triggers=list(set(retro_matches))[:3],
            )
        )

    # ------------------------------------------------------------------
    # 2. Urgency item without a recorded urgency finding
    # ------------------------------------------------------------------
    has_urgency = bool(_URGENCY.search(text))
    has_urgency_finding = bool(_URGENCY_FINDING.search(text))
    if has_urgency and not has_urgency_finding:
        findings.append(
            _build(
                "vote_date:urgency-without-finding",
                "Urgency designation present without a recorded urgency finding — "
                "California Gov. Code § 36937 requires a written declaration that "
                "an emergency exists before urgency procedures apply",
                "high",
                statute="Cal. Gov. Code § 36937",
            )
        )

    # ------------------------------------------------------------------
    # 3. High-value contract placed on consent calendar
    # ------------------------------------------------------------------
    on_consent = detect_consent_calendar(text)
    has_high_value = bool(_HIGH_VALUE.search(text))
    if on_consent and has_high_value:
        findings.append(
            _build(
                "vote_date:consent-calendar-high-value",
                "High-value contract or expenditure placed on consent calendar — "
                "consent calendar items are adopted without individual discussion "
                "or vote, bypassing public scrutiny for significant commitments",
                "medium",
            )
        )

    # ------------------------------------------------------------------
    # 4. Metadata date misalignment: execution before authorization
    # ------------------------------------------------------------------
    auth_date = _parse_iso(doc.get("authorization_date") or doc.get("approval_date"))
    exec_date = _parse_iso(doc.get("execution_date") or doc.get("effective_date"))

    if auth_date and exec_date and exec_date < auth_date:
        findings.append(
            _build(
                "vote_date:execution-before-authorization",
                "Execution date precedes authorization date in document metadata — "
                "contract or agreement was effective before legislative approval",
                "critical",
                authorization_date=str(auth_date),
                execution_date=str(exec_date),
                days_early=(auth_date - exec_date).days,
            )
        )

    # ------------------------------------------------------------------
    # 5. Excessive gap between authorization and execution (>90 days)
    # ------------------------------------------------------------------
    if auth_date and exec_date and exec_date > auth_date:
        gap = (exec_date - auth_date).days
        if gap > 90:
            findings.append(
                _build(
                    "vote_date:authorization-execution-gap",
                    f"Execution occurred {gap} days after authorization — "
                    "gaps exceeding 90 days suggest delayed implementation, "
                    "changed scope, or an authorization that lapsed",
                    "medium",
                    authorization_date=str(auth_date),
                    execution_date=str(exec_date),
                    gap_days=gap,
                )
            )

    # ------------------------------------------------------------------
    # 6. Text-derived date ordering anomaly
    #    When doc lacks structured date fields, look for authorization and
    #    execution language near dates in prose and flag if an execution-
    #    labelled date appears to precede an authorization-labelled date.
    # ------------------------------------------------------------------
    if not (auth_date and exec_date):
        text_dates = _extract_dates_from_text(text)
        if len(text_dates) >= 2:
            # Find earliest date near authorization language and earliest
            # date near execution language by scanning window around matches.
            auth_dates: list[date] = []
            exec_dates: list[date] = []
            for m in _AUTHORIZATION_LABEL.finditer(text):
                window = text[max(0, m.start() - 80) : m.end() + 80]
                for d in _extract_dates_from_text(window):
                    auth_dates.append(d)
            for m in _EXECUTION_LABEL.finditer(text):
                window = text[max(0, m.start() - 80) : m.end() + 80]
                for d in _extract_dates_from_text(window):
                    exec_dates.append(d)
            if auth_dates and exec_dates:
                earliest_auth = min(auth_dates)
                earliest_exec = min(exec_dates)
                if earliest_exec < earliest_auth:
                    findings.append(
                        _build(
                            "vote_date:text-date-ordering-anomaly",
                            "Execution-related date in document text appears to "
                            "precede authorization-related date — possible retroactive "
                            "ratification or date-recording error",
                            "medium",
                            earliest_authorization_date=str(earliest_auth),
                            earliest_execution_date=str(earliest_exec),
                        )
                    )

    return findings
