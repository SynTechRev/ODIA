"""L-4 Ministerial Duty Analysis detector.

Identifies situations where a public agency has a mandatory, nondiscretionary
duty to act but the document suggests the duty was not performed, was delayed
beyond the statutory deadline, or was mischaracterized as discretionary.

The core distinction in California administrative law:

  Ministerial duty — A duty imposed by law that the officer must perform in a
  prescribed manner, leaving nothing to discretion. Mandamus (Code Civ. Proc.
  § 1085) lies to compel performance. (Transdyn/Cresci JV v. City and County
  of San Francisco (1999) 72 Cal.App.4th 746.)

  Quasi-judicial / discretionary duty — The officer exercises judgment.
  Mandamus lies only to compel exercise of discretion, not to direct its
  outcome. (Common Cause v. Board of Supervisors (1989) 49 Cal.3d 432.)

Checks performed:
  1. CPRA 10-day response deadline (Gov. Code § 7922.530 / old § 6253(c)) —
     agency acknowledges or implies a response delay beyond 10 calendar days
     without citing a valid 14-day extension for unusual circumstances.
  2. CPRA determination-date extension abuse (§ 7922.535 / old § 6253(c)) —
     "unusual circumstances" extension invoked without citing a qualifying
     statutory ground (voluminous records, third-party consultation, offsite
     records, computer data compilation).
  3. AB 481 annual reporting duty (Gov. Code § 7072) — agency that has adopted
     an AB 481 use policy must submit an annual report to the governing body
     by June 1; document suggests report was not submitted or is overdue.
  4. Writ of mandate exposure (Code Civ. Proc. § 1085) — document references
     a legal obligation using mandatory language ("shall", "must", "required")
     but also contains language indicating non-performance without discretion
     justification (implying potential mandamus exposure).
  5. CPRA fee limitation duty (Gov. Code § 7922.570 / old § 6253(b)) —
     agency charged fees beyond the direct cost of duplication without
     invoking an express statutory exception.

Severity:
  high   — CPRA deadline violation; AB 481 reporting overdue
  medium — extension abuse; unexplained mandatory-language non-performance
  low    — fee limitation issue; writ-exposure indicator only

Finding contract follows the ODIA anomaly dict standard.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# --- CPRA 10-day deadline ---
_CPRA_RESPONSE_TRIGGER_RE = re.compile(
    r"\b(?:public\s+records?\s+(?:act\s+)?request|cpra\s+request|"
    r"records?\s+request|pra\s+request|"
    r"government(?:al)?\s+records?\s+request)\b",
    re.IGNORECASE,
)

_CPRA_DELAY_RE = re.compile(
    r"\b(?:delayed?|overdue|past\s+due|no\s+response|"
    r"failed\s+to\s+respond|did\s+not\s+respond|"
    r"(?:1[1-9]|[2-9]\d|\d{3,})\s*(?:calendar\s+)?days?"
    r"|(?:two|three|four|five|six|seven|eight|nine|ten)\s+(?:weeks?|months?)"
    r"|(?:\d+)\s+(?:weeks?|months?|years?)"
    r"|months?\s+(?:later|ago|overdue|without)"
    r"|years?\s+(?:later|ago|overdue|without))\b",
    re.IGNORECASE,
)

_CPRA_EXTENSION_CITED_RE = re.compile(
    r"\b(?:6253\(c\)|7922\.535|unusual\s+circumstance|14.day\s+extension|"
    r"fourteen.day\s+extension)\b",
    re.IGNORECASE,
)

# --- Unusual circumstances grounds (§ 7922.535 / § 6253(c)) ---
_UNUSUAL_CIRCS_TRIGGER_RE = re.compile(
    r"\b(?:unusual\s+circumstances?"
    r"|14.?day\s+extension"
    r"|fourteen.?day\s+extension"
    r"|extended\s+(?:deadline|time|response)"
    r"|additional\s+(?:time|days?)\s+(?:to\s+respond|for\s+response))\b",
    re.IGNORECASE,
)

_UNUSUAL_CIRCS_GROUNDS_RE = re.compile(
    r"\b(?:voluminous|large\s+(?:number|volume)|"
    r"separate\s+(?:facility|office|location)|off.?site|"
    r"third.?party|outside\s+agency|"
    r"computer\s+data|electronic\s+compilation|"
    r"department(?:al)?\s+consultation)\b",
    re.IGNORECASE,
)

# --- AB 481 annual reporting duty ---
_AB481_REPORT_TRIGGER_RE = re.compile(
    r"\b(?:ab\s*481|assembly\s+bill\s+481|7070|7072|"
    r"military\s+equipment\s+(?:use\s+)?policy|"
    r"surveillance\s+(?:use\s+)?policy)\b",
    re.IGNORECASE,
)

_AB481_ANNUAL_REPORT_RE = re.compile(
    r"\bannual\s+report\b",
    re.IGNORECASE,
)

_AB481_REPORT_MISSING_RE = re.compile(
    r"\b(?:"
    r"not\s+(?:submitted|filed|provided|prepared)"
    r"|was\s+not\s+(?:submitted|filed|provided|prepared)"
    r"|(?:is|was|are)\s+(?:overdue|missing|delinquent|absent)"
    r"|overdue"
    r"|no\s+annual\s+report"
    r"|failed\s+to\s+(?:submit|file|provide)"
    r"|report\s+not\s+(?:filed|submitted|provided)"
    r")\b",
    re.IGNORECASE,
)

# --- Writ of mandate exposure ---
_MANDATORY_LANG_RE = re.compile(
    r"\b(?:shall\s+(?:provide|respond|notify|publish|report|disclose|submit|"
    r"conduct|complete|maintain|adopt|establish)|"
    r"must\s+(?:provide|respond|notify|publish|report|disclose|submit|"
    r"conduct|complete|maintain|adopt|establish)|"
    r"is\s+required\s+to|are\s+required\s+to|"
    r"required\s+by\s+(?:law|statute|code|regulation))\b",
    re.IGNORECASE,
)

_NON_PERFORMANCE_RE = re.compile(
    r"\b(?:has\s+not|have\s+not|did\s+not|does\s+not|do\s+not|"
    r"failed\s+to|failure\s+to|refused\s+to|declining\s+to|"
    r"no\s+(?:action|response|compliance)|"
    r"non.?compli(?:ant|ance)|"
    r"has\s+yet\s+to|have\s+yet\s+to)\b",
    re.IGNORECASE,
)

_DISCRETION_QUALIFIER_RE = re.compile(
    r"\b(?:discretion(?:ary)?|judgment|may\s+(?:choose|elect|decide)|"
    r"at\s+(?:its|the\s+agency'?s?)\s+discretion|"
    r"quasi.?judicial|administrative\s+discretion)\b",
    re.IGNORECASE,
)

# --- CPRA fee limitation ---
_FEE_TRIGGER_RE = re.compile(
    r"\b(?:records?\s+(?:copy\s+)?fee|duplication\s+fee|"
    r"copying\s+(?:cost|fee|charge)|per.?page\s+(?:fee|cost|charge)|"
    r"retrieval\s+(?:fee|cost|charge)|search\s+(?:fee|cost|charge)|"
    r"staff\s+(?:time|cost)\s+(?:fee|charge))\b",
    re.IGNORECASE,
)

_FEE_EXCESS_RE = re.compile(
    r"\b(?:actual\s+cost|administrative\s+(?:overhead|cost)|"
    r"staff\s+(?:time|hours?|cost)|labor\s+(?:cost|charge)|"
    r"overhead|indirect\s+cost|research\s+(?:fee|charge))\b",
    re.IGNORECASE,
)

_FEE_EXCEPTION_CITED_RE = re.compile(
    r"\b(?:7922\.570|6253\s*\(b\)|electronic\s+format\s+exception|"
    r"programming\s+(?:cost|fee)|computer\s+extraction\s+cost)\b",
    re.IGNORECASE,
)


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
        "id": f"legal:l4:ministerial_duty:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l4_ministerial_duty",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def _check_cpra_deadline(text: str) -> list[dict[str, Any]]:
    """Check for CPRA 10-day response deadline violations."""
    if not _CPRA_RESPONSE_TRIGGER_RE.search(text):
        return []
    if not _CPRA_DELAY_RE.search(text):
        return []
    if _CPRA_EXTENSION_CITED_RE.search(text):
        return []
    return [
        _make_finding(
            "cpra_response_deadline",
            "CPRA response delay apparent without valid § 7922.535 extension — "
            "agency has ministerial duty to respond within 10 calendar days "
            "(Gov. Code § 7922.530)",
            "high",
            {
                "statute": "Gov. Code § 7922.530",
                "detail": (
                    "Public agencies must determine whether to comply within 10 calendar days "
                    "of receiving a CPRA request. Delay beyond 10 days without invoking a "
                    "valid 'unusual circumstances' extension (§ 7922.535) is a ministerial "
                    "duty violation and may support a writ of mandate under Code Civ. Proc. "
                    "§ 1085."
                ),
            },
        )
    ]


def _check_extension_abuse(text: str) -> list[dict[str, Any]]:
    """Check for § 7922.535 extension invoked without citing a qualifying ground."""
    if not _UNUSUAL_CIRCS_TRIGGER_RE.search(text):
        return []
    if _UNUSUAL_CIRCS_GROUNDS_RE.search(text):
        return []
    return [
        _make_finding(
            "cpra_extension_no_grounds",
            "CPRA 'unusual circumstances' extension invoked without citing a "
            "qualifying statutory ground (§ 7922.535)",
            "medium",
            {
                "statute": "Gov. Code § 7922.535",
                "detail": (
                    "A 14-day extension under § 7922.535 requires citing one of four "
                    "statutory grounds: (1) voluminous records, (2) off-site records, "
                    "(3) third-party consultation required, or (4) computer data "
                    "compilation. A bare invocation of 'unusual circumstances' without "
                    "a qualifying ground does not satisfy the ministerial duty standard."
                ),
            },
        )
    ]


def _check_ab481_annual_report(text: str) -> list[dict[str, Any]]:
    """Check for AB 481 annual reporting duty not performed."""
    if not _AB481_REPORT_TRIGGER_RE.search(text):
        return []
    if not _AB481_ANNUAL_REPORT_RE.search(text):
        return []
    if not _AB481_REPORT_MISSING_RE.search(text):
        return []
    return [
        _make_finding(
            "ab481_annual_report_missing",
            "AB 481 annual report to governing body not submitted — "
            "mandatory duty under Gov. Code § 7072",
            "high",
            {
                "statute": "Gov. Code § 7072",
                "detail": (
                    "Agencies that adopt a military equipment use policy under AB 481 "
                    "must submit an annual report to the governing body by June 1 each "
                    "year. Failure to submit is a ministerial duty violation subject to "
                    "writ of mandate under Code Civ. Proc. § 1085."
                ),
            },
        )
    ]


def _check_writ_exposure(text: str) -> list[dict[str, Any]]:
    """Check for mandatory-language obligations paired with non-performance."""
    if not _MANDATORY_LANG_RE.search(text):
        return []
    if not _NON_PERFORMANCE_RE.search(text):
        return []
    if _DISCRETION_QUALIFIER_RE.search(text):
        return []
    return [
        _make_finding(
            "mandatory_duty_nonperformance",
            "Document contains mandatory statutory obligation language ('shall'/'must'/"
            "'required') alongside non-performance language without discretion "
            "justification — potential writ of mandate exposure",
            "medium",
            {
                "statute": "Code Civ. Proc. § 1085",
                "detail": (
                    "Where a statute imposes a mandatory, nondiscretionary duty ('shall'), "
                    "failure to perform supports a writ of mandate. "
                    "(Transdyn/Cresci JV v. City and County of San Francisco (1999) "
                    "72 Cal.App.4th 746.) The document should clarify whether any "
                    "discretion exception applies."
                ),
                "case": "Transdyn/Cresci JV v. City and County of San Francisco (1999) "
                        "72 Cal.App.4th 746",
            },
        )
    ]


def _check_fee_limitation(text: str) -> list[dict[str, Any]]:
    """Check for CPRA fee charges beyond direct duplication cost."""
    if not _FEE_TRIGGER_RE.search(text):
        return []
    if not _FEE_EXCESS_RE.search(text):
        return []
    if _FEE_EXCEPTION_CITED_RE.search(text):
        return []
    return [
        _make_finding(
            "cpra_fee_exceeds_direct_cost",
            "CPRA fee appears to include costs beyond direct duplication — "
            "agency has ministerial duty to charge only direct cost of copy "
            "(Gov. Code § 7922.570)",
            "low",
            {
                "statute": "Gov. Code § 7922.570",
                "detail": (
                    "Under § 7922.570, agencies may charge only the direct cost of "
                    "duplication (e.g., per-page copy cost). Staff time, overhead, "
                    "and search/retrieval costs may not be charged unless an express "
                    "statutory exception applies (e.g., computer data extraction under "
                    "§ 7922.570(b))."
                ),
            },
        )
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-4 Ministerial Duty Analysis on a single document."""
    text = _get_text(doc)
    if not text:
        return []

    return (
        _check_cpra_deadline(text)
        + _check_extension_abuse(text)
        + _check_ab481_annual_report(text)
        + _check_writ_exposure(text)
        + _check_fee_limitation(text)
    )
