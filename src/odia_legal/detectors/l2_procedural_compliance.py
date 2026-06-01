"""L-2 Procedural Compliance detector.

Identifies failures to follow required statutory procedures in public-agency
documents, with a focus on CPRA response obligations and AB 481 compliance.

Checks performed:
  1. CPRA response-timing violations
     — Document references CPRA denial/response but no specific timeline stated,
       OR response timeline exceeds the statutory 10-calendar-day limit
       (Gov. Code § 7922.535).
  2. CPRA denial form deficiency
     — Denial letter lacks required statutory basis citation (§ 7923.600 series)
       or lacks the required statement of the requester's right to appeal
       (Gov. Code § 7923.115).
  3. AB 481 missing annual report
     — Document references use of surveillance technology but no annual report
       reference or compliance date is present (Gov. Code § 36002).
  4. AB 481 missing governing-body approval
     — Document references acquiring surveillance technology without referencing
       governing-body approval (Gov. Code § 36001 / § 36003).
  5. Federal grant — missing anti-supplanting certification
     — Document references JAG/Byrne grant expenditures without referencing
       the anti-supplanting requirement (2 CFR § 200.303).

Severity:
  high   — CPRA response-timing violation; AB 481 missing governing-body approval
  medium — CPRA denial form deficiency; AB 481 missing annual report
  low    — Federal grant procedural note (anti-supplanting)

Finding contract follows the ODIA anomaly dict standard.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# CPRA denial / withholding language
_CPRA_DENIAL_RE = re.compile(
    r"\b(?:denied?|denial|withheld?|withholding|refusing?|refus(?:ed|al)|"
    r"not\s+subject\s+to\s+disclosure|exempt)\b",
    re.IGNORECASE,
)

# CPRA request / response language
_CPRA_REQUEST_RE = re.compile(
    r"\b(?:public\s+records\s+request|cpra\s+request|records\s+request|"
    r"california\s+public\s+records|government\s+code\s+(?:7920|6250))\b",
    re.IGNORECASE,
)

# Ten-day (statutory) reference
_TEN_DAY_RE = re.compile(
    r"\b(?:10\s*(?:calendar\s*)?days?|ten\s+(?:calendar\s+)?days?|7922\.535|6253\(c\))\b",
    re.IGNORECASE,
)

# Response timeline — tries to capture "N days" patterns
_RESPONSE_DAYS_RE = re.compile(
    r"\b(?:responded?\s+(?:in\s+)?(?:within\s+)?|response\s+(?:was\s+)?)(\d{1,3})\s*(?:calendar\s+)?days?\b",
    re.IGNORECASE,
)

# Statutory citation for denial basis (§ 7923.xxx or old § 6254.xxx)
_DENIAL_BASIS_RE = re.compile(
    r"\b(?:792[0-9]\.\d+|625[0-9](?:\(\w+\))?)\b",
    re.IGNORECASE,
)

# Right to appeal / seek review
_APPEAL_RIGHTS_RE = re.compile(
    r"\b(?:right\s+to\s+appeal|right\s+to\s+seek|judicial\s+review|"
    r"petition\s+for\s+writ|writ\s+of\s+mandate|7923\.115|6259)\b",
    re.IGNORECASE,
)

# AB 481 / military equipment language
_AB481_TECH_RE = re.compile(
    r"\b(?:ab\s*481|military\s+equipment|surveillance\s+technolog|"
    r"government\s+code\s+36\d{3}|36000|36001|36002)\b",
    re.IGNORECASE,
)

# Annual report reference
_ANNUAL_REPORT_RE = re.compile(
    r"\b(?:annual\s+report|annual\s+review|public\s+report|36002)\b",
    re.IGNORECASE,
)

# Governing body approval
_GOVERNING_BODY_RE = re.compile(
    r"\b(?:governing\s+body|board\s+of\s+supervisors|city\s+council|"
    r"board\s+approv|council\s+approv|ordinance|resolution\s+no\.?\s*\d+|36001|36003)\b",
    re.IGNORECASE,
)

# JAG / Byrne grant language
_JAG_RE = re.compile(
    r"\b(?:jag|justice\s+assistance\s+grant|byrne\s+grant|edward\s+byrne|ojp|bja)\b",
    re.IGNORECASE,
)

# Anti-supplanting reference
_ANTI_SUPPLANTING_RE = re.compile(
    r"\b(?:anti.supplant|supplanting|supplant(?:ed|ing)|200\.303)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_text(doc: dict[str, Any]) -> str:
    for key in ("text", "content", "body", "raw_text"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _make_finding(
    rule_id: str,
    issue: str,
    severity: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": f"legal:l2:procedural_compliance:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l2_procedural_compliance",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Detection logic
# ---------------------------------------------------------------------------


def _check_cpra_timing(text: str, is_cpra_doc: bool) -> list[dict[str, Any]]:
    """Check 1: CPRA response timing."""
    results: list[dict[str, Any]] = []
    has_ten_day_ref = bool(_TEN_DAY_RE.search(text))
    day_matches = _RESPONSE_DAYS_RE.findall(text)
    late_responses = [int(d) for d in day_matches if int(d) > 10]

    if late_responses:
        results.append(
            _make_finding(
                "cpra_late_response",
                f"CPRA response may exceed statutory 10-day limit — "
                f"{late_responses[0]}-day response referenced (Gov. Code § 7922.535)",
                "high",
                {
                    "statute": "Gov. Code § 7922.535",
                    "days_found": late_responses,
                    "statutory_limit": 10,
                    "detail": "Gov. Code § 7922.535 requires response within 10 calendar days",
                },
            )
        )
    elif not has_ten_day_ref and is_cpra_doc:
        results.append(
            _make_finding(
                "cpra_response_timing_absent",
                "CPRA document does not reference the 10-calendar-day response requirement (Gov. Code § 7922.535)",
                "medium",
                {
                    "statute": "Gov. Code § 7922.535",
                    "detail": "Agencies must respond within 10 calendar days of receiving a CPRA request",
                },
            )
        )
    return results


def _check_cpra_denial_form(text: str) -> list[dict[str, Any]]:
    """Check 2: CPRA denial form deficiency."""
    results: list[dict[str, Any]] = []
    if not _DENIAL_BASIS_RE.search(text):
        results.append(
            _make_finding(
                "cpra_denial_missing_statutory_basis",
                "CPRA denial does not cite a specific statutory exemption (§ 7923.600 series required)",
                "high",
                {
                    "statute": "Gov. Code § 7923.600",
                    "detail": "Denial must identify the specific exemption under §§ 7923.610–7923.915 or § 7922.000 balancing test",
                },
            )
        )
    if not _APPEAL_RIGHTS_RE.search(text):
        results.append(
            _make_finding(
                "cpra_denial_missing_appeal_rights",
                "CPRA denial does not inform requester of right to seek judicial review (Gov. Code § 7923.115)",
                "medium",
                {
                    "statute": "Gov. Code § 7923.115",
                    "detail": "Agencies must advise requester that they may petition for a writ of mandate to compel disclosure",
                },
            )
        )
    return results


def _check_ab481(text: str) -> list[dict[str, Any]]:
    """Checks 3 & 4: AB 481 annual report + governing-body approval."""
    results: list[dict[str, Any]] = []
    if not _ANNUAL_REPORT_RE.search(text):
        results.append(
            _make_finding(
                "ab481_missing_annual_report",
                "AB 481 surveillance technology referenced without annual report compliance (Gov. Code § 36002)",
                "medium",
                {
                    "statute": "Gov. Code § 36002",
                    "detail": "AB 481 requires agencies to publish an annual public report on surveillance technology use, complaints, and violations",
                },
            )
        )
    if not _GOVERNING_BODY_RE.search(text):
        results.append(
            _make_finding(
                "ab481_missing_governing_body_approval",
                "AB 481 surveillance technology referenced without governing-body approval documentation (Gov. Code §§ 36001/36003)",
                "high",
                {
                    "statute": "Gov. Code § 36001",
                    "detail": "AB 481 prohibits acquiring or using military equipment without prior governing-body approval of a use policy",
                },
            )
        )
    return results


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-2 Procedural Compliance detection on a single document."""
    text = _get_text(doc)
    if not text:
        return []

    is_cpra_doc = bool(_CPRA_REQUEST_RE.search(text))
    has_denial = bool(_CPRA_DENIAL_RE.search(text))

    findings: list[dict[str, Any]] = []

    if is_cpra_doc or has_denial:
        findings.extend(_check_cpra_timing(text, is_cpra_doc))
    if has_denial:
        findings.extend(_check_cpra_denial_form(text))
    if _AB481_TECH_RE.search(text):
        findings.extend(_check_ab481(text))
    if _JAG_RE.search(text) and not _ANTI_SUPPLANTING_RE.search(text):
        findings.append(
            _make_finding(
                "jag_missing_anti_supplanting",
                "JAG/Byrne grant referenced without anti-supplanting compliance statement (2 C.F.R. § 200.303)",
                "low",
                {
                    "statute": "2 C.F.R. § 200.303",
                    "detail": "JAG grant conditions prohibit supplanting state/local funds with federal award funds; compliance statement required",
                },
            )
        )

    return findings
