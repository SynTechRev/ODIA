"""Grant Funding Trails Detector.

Tracks whether federal grant money flowing through a document has a visible,
reconcilable audit trail.  Complements grant_compliance.py (which checks for
missing compliance artefacts) by focusing on the funding chain itself:

  * Grant amount cited without expenditure tracking language
  * Pass-through / subgrant without federal-agency attribution
  * Grant reference without single-audit / Uniform Guidance accountability
  * Multiple dollar amounts in a grant context that do not reconcile
  * JAG award referenced without an award number or tracking identifier
"""

from __future__ import annotations

import re
from typing import Any

from .text_utils import extract_text_content
from .vendor_database import STATUTE_BY_KEY, detect_statutes

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

_GRANT_AMOUNT = re.compile(
    r"grant\s+(?:award|fund|amount|total)[^.]{0,60}"
    r"(\$\s*\d[\d,]*(?:\.\d{2})?(?:\s*[MBT](?:illion)?)?)",
    re.IGNORECASE,
)

_DOLLAR = re.compile(
    r"\$\s*\d[\d,]*(?:\.\d{2})?(?:\s*[MBT](?:illion)?)?",
    re.IGNORECASE,
)

_EXPENDITURE_TRACKING = re.compile(
    r"\b(?:drawdown|expenditure\s+report|quarterly\s+report|"
    r"reimbursement\s+request|disbursement|financial\s+report|"
    r"progress\s+report|grant\s+management)\b",
    re.IGNORECASE,
)

_PASSTHROUGH = re.compile(
    r"\b(?:pass-?through|subgrant|sub-?grant|subrecipient|"
    r"sub-?recipient|flow-?through)\b",
    re.IGNORECASE,
)

_FEDERAL_ATTRIBUTION = re.compile(
    r"\b(?:DOJ|BJA|OJP|COPS\s+Office|HUD|FEMA|NIJ|"
    r"Bureau\s+of\s+Justice|Office\s+of\s+Justice|"
    r"Department\s+of\s+Justice|federal\s+agency)\b",
    re.IGNORECASE,
)

_SINGLE_AUDIT = re.compile(
    r"\b(?:single\s+audit|A-133|uniform\s+guidance|"
    r"2\s+CFR|OMB\s+Circular|financial\s+audit)\b",
    re.IGNORECASE,
)

_AWARD_NUMBER = re.compile(
    r"\b(?:award\s+(?:no|number|#|id)|grant\s+(?:no|number|#|id)|"
    r"BJA[-\s]\d|OJP[-\s]\d|COPS[-\s]\d|"
    r"\d{4}-[A-Z]{2}-[A-Z]{2}-\d{4})\b",
    re.IGNORECASE,
)

_GRANT_REFERENCE = re.compile(
    r"\b(?:grant|federal\s+funds?|award(?:ed)?|"
    r"Edward\s+Byrne|JAG|COPS|ARPA|CDBG|"
    r"pass-?through|subgrant|sub-?grant|subrecipient)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _build(
    finding_id: str, issue: str, severity: str, **details: Any
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "issue": issue,
        "severity": severity,
        "layer": "grant_funding_trails",
        "details": details,
    }


def _dollar_amounts(text: str) -> list[str]:
    return [m.group().strip() for m in _DOLLAR.finditer(text)]


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


def detect_grant_funding_trail_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect missing or broken grant funding trail signals in *doc*."""
    findings: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return findings

    text = extract_text_content(doc) or ""
    if not text.strip():
        return findings

    text_lower = text.lower()
    has_grant_ref = bool(_GRANT_REFERENCE.search(text))
    if not has_grant_ref:
        return findings  # not a grant-related document

    statutes = detect_statutes(text)
    has_jag = STATUTE_BY_KEY["jag"].key in statutes

    has_expenditure_tracking = bool(_EXPENDITURE_TRACKING.search(text))
    has_passthrough = bool(_PASSTHROUGH.search(text))
    has_federal_attribution = bool(_FEDERAL_ATTRIBUTION.search(text))
    has_single_audit = bool(_SINGLE_AUDIT.search(text))
    has_award_number = bool(_AWARD_NUMBER.search(text))
    amounts = _dollar_amounts(text)

    # ------------------------------------------------------------------
    # 1. Grant amount without expenditure tracking
    # ------------------------------------------------------------------
    grant_amount_matches = _GRANT_AMOUNT.findall(text)
    if grant_amount_matches and not has_expenditure_tracking:
        findings.append(
            _build(
                "grant_trail:amount-without-tracking",
                "Grant amount referenced without expenditure tracking language — "
                "no drawdown, disbursement, or quarterly-report reference found",
                "high",
                grant_amounts=grant_amount_matches[:3],
            )
        )

    # ------------------------------------------------------------------
    # 2. Pass-through grant without federal-agency attribution
    # ------------------------------------------------------------------
    if has_passthrough and not has_federal_attribution:
        findings.append(
            _build(
                "grant_trail:passthrough-without-attribution",
                "Pass-through / subgrant language present without federal-agency "
                "attribution — origin agency and CFDA/ALN number cannot be traced",
                "high",
            )
        )

    # ------------------------------------------------------------------
    # 3. Grant reference without single-audit accountability language
    # ------------------------------------------------------------------
    if has_grant_ref and not has_single_audit and len(amounts) >= 3:
        findings.append(
            _build(
                "grant_trail:no-single-audit-reference",
                "Multiple dollar amounts in a grant-referenced document with no "
                "single-audit or Uniform Guidance (2 CFR) accountability language",
                "medium",
                amount_count=len(amounts),
            )
        )

    # ------------------------------------------------------------------
    # 4. JAG award without award number / tracking identifier
    # ------------------------------------------------------------------
    if has_jag and not has_award_number:
        findings.append(
            _build(
                "grant_trail:jag-without-award-number",
                "JAG/Edward Byrne grant referenced without an award number or "
                "tracking identifier — BJA requires award-number citation in "
                "all procurement and budget documents",
                "medium",
                statute="34 U.S.C. § 10152",
            )
        )

    # ------------------------------------------------------------------
    # 5. Dollar-amount reconciliation gap
    #    Flag when the largest amount is >5× the smallest and there are
    #    3+ distinct amounts — suggests unreconciled grant vs. local funds.
    # ------------------------------------------------------------------
    if len(amounts) >= 3:
        parsed: list[float] = []
        for raw in amounts:
            clean = re.sub(r"[,$\s]", "", raw)
            multiplier = 1.0
            if clean.upper().endswith("M"):
                multiplier, clean = 1_000_000, clean[:-1]
            elif clean.upper().endswith("B"):
                multiplier, clean = 1_000_000_000, clean[:-1]
            try:
                parsed.append(float(clean) * multiplier)
            except ValueError:
                pass
        if len(parsed) >= 3:
            lo, hi = min(parsed), max(parsed)
            if lo > 0 and hi / lo > 5:
                findings.append(
                    _build(
                        "grant_trail:amount-reconciliation-gap",
                        "Dollar amounts in grant-referenced document span more than "
                        "5× range — possible unreconciled grant vs. local-fund "
                        "amounts or missing expenditure-to-award reconciliation",
                        "medium",
                        min_amount=lo,
                        max_amount=hi,
                        ratio=round(hi / lo, 1),
                    )
                )

    return findings
