"""L-5 Federal Grant Compliance detector.

Identifies potential compliance failures in federal grant administration,
focused on JAG/Byrne Memorial Justice Assistance Grants (34 U.S.C. § 10152)
and the Uniform Guidance (2 CFR Part 200).

Checks performed:
  1. Supplanting — federal funds used to replace (rather than supplement)
     state/local funds that would otherwise be spent on the same program.
  2. Sole-source procurement — equipment or services purchased without
     competitive bidding in violation of 2 CFR § 200.318-319.
  3. Unapproved equipment purchase — equipment over the capitalization
     threshold ($5,000) without prior approval (2 CFR § 200.313).
  4. Missing subrecipient monitoring — grant passed to subrecipient without
     documented monitoring (2 CFR §§ 200.330-332).
  5. Unallowable costs — costs not permitted under Uniform Guidance
     (defense of criminal proceedings, lobbying, etc.).

Severity:
  high   — supplanting; unallowable costs
  medium — sole-source without justification; missing subrecipient monitoring
  low    — equipment threshold; documentation gaps
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# JAG / federal grant context
_JAG_RE = re.compile(
    r"\b(?:jag|justice\s+assistance\s+grant|byrne\s+grant|edward\s+byrne|"
    r"ojp|bja|bureau\s+of\s+justice\s+assistance|federal\s+grant|"
    r"federal\s+award|grant\s+fund(?:s|ing)?)\b",
    re.IGNORECASE,
)

# Supplanting language
_SUPPLANTING_RE = re.compile(
    r"\b(?:replac(?:e|ing|ed)\s+(?:state|local|county|city)\s+funds?"
    r"|substitut(?:e|ing|ed)\s+(?:state|local)\s+(?:funds?|budget|appropriat\w*)"
    r"|used\s+(?:in\s+place\s+of|instead\s+of)\s+(?:state|local)\s+funds?"
    r"|would\s+have\s+been\s+funded\s+by\s+(?:state|local)"
    r"|free(?:d|ing|s)\s+up\s+(?:state|local)\s+funds?)\b",
    re.IGNORECASE,
)

# Supplement language (good — not supplanting)
_SUPPLEMENT_RE = re.compile(
    r"\b(?:supplement(?:al|ing|s)?\s+(?:state|local|existing)\s+fund|"
    r"in\s+addition\s+to\s+(?:state|local)\s+fund|"
    r"anti.supplant|non.supplant|not\s+replac(?:e|ing))\b",
    re.IGNORECASE,
)

# Sole-source procurement
_SOLE_SOURCE_RE = re.compile(
    r"\b(?:sole\s+source|sole-source|single\s+source|sole\s+vendor|"
    r"no-bid|no\s+bid|without\s+competitive\s+bid|"
    r"direct\s+award|waiver\s+of\s+competition)\b",
    re.IGNORECASE,
)

# Sole-source justification present
_SOLE_SOURCE_JUSTIFICATION_RE = re.compile(
    r"\b(?:sole\s+source\s+justification|proprietary|unique\s+capabilit|"
    r"only\s+(?:one|1)\s+(?:vendor|source)|emergency\s+purchase|"
    r"200\.320|200\.319)\b",
    re.IGNORECASE,
)

# Equipment purchase / capital expenditure
_EQUIPMENT_RE = re.compile(
    r"\b(?:equipment\s+purchase|purchase(?:d)?\s+equipment|"
    r"capital\s+(?:outlay|equipment|expenditure)|"
    r"\$\s*(?:[5-9]\d{3}|[1-9]\d{4,})|"  # >= $5,000
    r"axon|flock\s+safety|motorola|body\s+(?:camera|worn)|"
    r"license\s+plate\s+reader|alpr|surveillance\s+system)\b",
    re.IGNORECASE,
)

# Prior approval language
_PRIOR_APPROVAL_RE = re.compile(
    r"\b(?:prior\s+approv(?:al|ed)|grantor\s+approv|ojp\s+approv|"
    r"prior\s+written\s+consent|200\.313|equipment\s+approv)\b",
    re.IGNORECASE,
)

# Subrecipient / pass-through language
_SUBRECIPIENT_RE = re.compile(
    r"\b(?:subrecipient|sub-recipient|pass.through|sub\s+award|subaward|"
    r"subgrant|sub.grant)\b",
    re.IGNORECASE,
)

# Monitoring language
_MONITORING_RE = re.compile(
    r"\b(?:monitor(?:ing|ed)?|site\s+visit|audit|compliance\s+review|"
    r"performance\s+report|programmatic\s+review|200\.330|200\.331|200\.332)\b",
    re.IGNORECASE,
)

# Unallowable costs
_UNALLOWABLE_RE = re.compile(
    r"\b(?:criminal\s+defense\s+(?:cost|fee|expense)|"
    r"lobbying\s+(?:cost|expense)|lobbied|"
    r"alcohol(?:ic\s+beverage)?|"
    r"entertain(?:ment|ing)?\s+(?:cost|expense)|"
    r"bad\s+debt|interest\s+(?:cost|expense)|"
    r"fund-raising|fundrais(?:ing|er))\b",
    re.IGNORECASE,
)


def _get_text(doc: dict[str, Any]) -> str:
    for key in ("text", "content", "body", "raw_text"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _make_finding(
    rule_id: str, issue: str, severity: str, details: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": f"legal:l5:federal_grant_compliance:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l5_federal_grant_compliance",
        "details": details,
    }


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-5 Federal Grant Compliance detection on a single document."""
    text = _get_text(doc)
    if not text:
        return []

    if not _JAG_RE.search(text):
        return []  # No federal grant context — skip all checks

    findings: list[dict[str, Any]] = []

    # 1. Supplanting
    if _SUPPLANTING_RE.search(text) and not _SUPPLEMENT_RE.search(text):
        findings.append(
            _make_finding(
                "supplanting",
                "Federal grant funds may be supplanting (replacing) rather than supplementing state/local funds — prohibited by 34 U.S.C. § 10152 grant conditions",
                "high",
                {
                    "statute": "34 U.S.C. § 10152",
                    "regulation": "2 C.F.R. § 200.303",
                    "detail": "Anti-supplanting requirement prohibits using federal funds to replace state/local funds that would otherwise support the same program",
                },
            )
        )

    # 2. Sole-source without justification
    if _SOLE_SOURCE_RE.search(text) and not _SOLE_SOURCE_JUSTIFICATION_RE.search(text):
        findings.append(
            _make_finding(
                "sole_source_no_justification",
                "Sole-source procurement referenced without documented justification — violates 2 C.F.R. §§ 200.318-319 competition requirements",
                "medium",
                {
                    "statute": "34 U.S.C. § 10152",
                    "regulation": "2 C.F.R. § 200.318",
                    "detail": "Full and open competition is required; sole-source exceptions must be documented with written justification",
                },
            )
        )

    # 3. Equipment without prior approval
    if _EQUIPMENT_RE.search(text) and not _PRIOR_APPROVAL_RE.search(text):
        findings.append(
            _make_finding(
                "equipment_no_prior_approval",
                "Equipment purchase with federal grant funds referenced without prior approval documentation (2 C.F.R. § 200.313)",
                "low",
                {
                    "statute": "34 U.S.C. § 10152",
                    "regulation": "2 C.F.R. § 200.313",
                    "detail": "Equipment purchases over capitalization threshold ($5,000) require prior written approval from the federal awarding agency",
                },
            )
        )

    # 4. Subrecipient without monitoring
    if _SUBRECIPIENT_RE.search(text) and not _MONITORING_RE.search(text):
        findings.append(
            _make_finding(
                "subrecipient_no_monitoring",
                "Subrecipient or pass-through award referenced without monitoring documentation (2 C.F.R. §§ 200.330-332)",
                "medium",
                {
                    "statute": "34 U.S.C. § 10152",
                    "regulation": "2 C.F.R. § 200.330",
                    "detail": "Pass-through entities must monitor subrecipient compliance and performance; documentation of monitoring activities required",
                },
            )
        )

    # 5. Unallowable costs
    if _UNALLOWABLE_RE.search(text):
        findings.append(
            _make_finding(
                "unallowable_cost",
                "Document references costs that may be unallowable under Uniform Guidance for federal grants",
                "high",
                {
                    "statute": "34 U.S.C. § 10152",
                    "regulation": "2 C.F.R. § 200.403",
                    "detail": "Costs for criminal defense, lobbying, entertainment, alcohol, and bad debts are unallowable under 2 CFR Part 200",
                },
            )
        )

    return findings
