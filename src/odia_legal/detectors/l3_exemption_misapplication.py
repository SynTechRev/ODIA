"""L-3 Exemption Misapplication detector.

Identifies improper or unsupported invocations of CPRA exemptions and
related privilege claims in public-agency documents.

Checks performed:
  1. Blanket § 6254(f) / § 7923.650 claim without investigation nexus
     — "law enforcement records" claimed for bulk surveillance / ALPR data
       without any reference to an active investigation (CBS v. Block; ACLU
       v. Superior Court (2011))
  2. § 6254(c) / § 7923.625 (personnel files) — post-SB 1421 misapplication
     — Officer records withheld under the categorical personnel-file exemption
       after January 1, 2019 without accounting for SB 1421 categories
       (Copley Press v. Superior Court, partially overruled by SB 1421)
  3. § 6255 / § 7922.000 (catch-all) — insufficient balancing test statement
     — Catch-all exemption invoked without the required specific showing that
       the public interest in nondisclosure CLEARLY outweighs disclosure
       (Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325)
  4. Civil Code § 1798.90.55 (ALPR CPRA exemption) — claimed outside scope
     — ALPR data CPRA exemption claimed for non-operator or non-SB-34 context
  5. Attorney-client privilege (§ 6254(k) / § 7923.700) — overbroad claim
     — Attorney-client privilege invoked for factual records or business
       documents not constituting legal advice (LA County Board of Supervisors
       v. Superior Court (2016) 2 Cal.5th 282)

Severity:
  high   — blanket § 6254(f) claim for ALPR/bulk; § 6255 no balancing test
  medium — post-SB 1421 § 7923.625 misapplication; overbroad § 7923.700
  low    — Civil Code § 1798.90.55 scope issue

Finding contract follows the ODIA anomaly dict standard.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# § 6254(f) / § 7923.650 — law enforcement investigative exemption invoked
_LAW_ENFORCE_EXEMPT_RE = re.compile(
    r"\b(?:6254\(f\)|7923\.650|law\s+enforcement\s+(?:record|exemption|investigat))\b",
    re.IGNORECASE,
)

# Investigation nexus — any reference to a specific case or ongoing investigation
_INVESTIGATION_NEXUS_RE = re.compile(
    r"\b(?:active\s+investigation|ongoing\s+investigation|pending\s+investigation|"
    r"case\s+(?:number|no\.?)\s*\d+|case\s+file|criminal\s+investigation|"
    r"under\s+investigation|investigative\s+file|specific\s+investigation)\b",
    re.IGNORECASE,
)

# ALPR / bulk surveillance context (without investigation nexus = § 6254(f) problem)
_ALPR_CONTEXT_RE = re.compile(
    r"\b(?:alpr|license\s+plate\s+reader|lpr|flock|surveillance\s+data|"
    r"bulk\s+(?:data|record|collection)|mass\s+(?:data|surveillance))\b",
    re.IGNORECASE,
)

# Personnel file exemption § 6254(c) / § 7923.625
_PERSONNEL_EXEMPT_RE = re.compile(
    r"\b(?:6254\(c\)|7923\.625|personnel\s+(?:file|record)|"
    r"peace\s+officer\s+record|officer\s+personnel)\b",
    re.IGNORECASE,
)

# SB 1421 categories (use of force, sexual assault, dishonesty)
_SB1421_CATEGORIES_RE = re.compile(
    r"\b(?:sb\s*1421|use\s+of\s+force|835a|sexual\s+assault|dishonesty|"
    r"832\.7|officer\s+misconduct|sustained\s+(?:complaint|finding))\b",
    re.IGNORECASE,
)

# Catch-all exemption § 6255 / § 7922.000
_CATCH_ALL_EXEMPT_RE = re.compile(
    r"\b(?:6255|7922\.000|catch.?all|public\s+interest\s+(?:in\s+)?nondisclosure|"
    r"balancing\s+test|clearly\s+outweigh)\b",
    re.IGNORECASE,
)

# Specific balancing-test language (required by Times Mirror)
_BALANCING_LANGUAGE_RE = re.compile(
    r"\b(?:clearly\s+outweigh|outweigh(?:s)?\s+the\s+public\s+interest|"
    r"specific(?:ally)?\s+demonstrate|particularize[d]?\s+showing|"
    r"frank\s+(?:internal\s+)?deliberation|deliberative\s+process)\b",
    re.IGNORECASE,
)

# Civil Code § 1798.90.55 — ALPR CPRA exemption
_ALPR_CPRA_EXEMPT_RE = re.compile(
    r"\b(?:1798\.90\.55|alpr\s+(?:cpra\s+)?exemption|civil\s+code\s+1798)\b",
    re.IGNORECASE,
)

# § 6254(k) / § 7923.700 — attorney-client privilege
_AC_PRIVILEGE_RE = re.compile(
    r"\b(?:6254\(k\)|7923\.700|attorney.client\s+privilege|"
    r"attorney.client\s+communication|privileged\s+communication)\b",
    re.IGNORECASE,
)

# Factual records (not legal advice) — signals overbroad § 7923.700 claim
_FACTUAL_RECORD_RE = re.compile(
    r"\b(?:incident\s+report|police\s+report|case\s+report|financial\s+record|"
    r"contract|invoice|purchase\s+order|settlement\s+amount|payment|"
    r"budget|expenditure|factual\s+(?:summary|report|record))\b",
    re.IGNORECASE,
)

# Whether document is post-2019 (for SB 1421 analysis)
_POST_SB1421_DATE_RE = re.compile(r"\b20(?:19|2\d)\b")


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
        "id": f"legal:l3:exemption_misapplication:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l3_exemption_misapplication",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Sub-checks
# ---------------------------------------------------------------------------


def _check_law_enforcement_blanket(text: str) -> list[dict[str, Any]]:
    """Check 1: blanket § 6254(f) / § 7923.650 claim over ALPR/bulk data."""
    results: list[dict[str, Any]] = []
    if not _LAW_ENFORCE_EXEMPT_RE.search(text):
        return results
    if not _ALPR_CONTEXT_RE.search(text):
        return results
    if _INVESTIGATION_NEXUS_RE.search(text):
        return results  # Specific investigation cited — exemption may be valid
    results.append(
        _make_finding(
            "law_enforcement_blanket_alpr_claim",
            "§ 6254(f) / § 7923.650 law enforcement exemption claimed for ALPR or bulk surveillance data without investigation nexus",
            "high",
            {
                "statute": "Gov. Code § 7923.650",
                "case_law": "ACLU v. Superior Court (2011) 202 Cal.App.4th 55",
                "detail": "The § 7923.650 exemption requires a particularized showing of harm to a specific investigation; bulk ALPR data is not automatically exempt",
            },
        )
    )
    return results


def _check_personnel_post_sb1421(text: str) -> list[dict[str, Any]]:
    """Check 2: § 7923.625 (personnel file) claimed after SB 1421 for covered categories."""
    results: list[dict[str, Any]] = []
    if not _PERSONNEL_EXEMPT_RE.search(text):
        return results
    if not _SB1421_CATEGORIES_RE.search(text):
        return results
    is_post_sb1421 = bool(_POST_SB1421_DATE_RE.search(text))
    if not is_post_sb1421:
        return results  # Pre-2019 document — old rule may have applied
    results.append(
        _make_finding(
            "personnel_file_post_sb1421_misapplication",
            "Personnel-file exemption (§ 7923.625) applied to SB 1421 categories (use of force, sexual assault, or dishonesty) — these records are now public under Pen. Code § 832.7",
            "medium",
            {
                "statute": "Pen. Code § 832.7",
                "case_law": "Copley Press v. Superior Court (2006) 39 Cal.4th 1272 (partially overruled by SB 1421, eff. Jan 1 2019)",
                "detail": "SB 1421 (effective January 1, 2019) made records of officer use of force, sexual assault, and dishonesty findings publicly disclosable; § 7923.625 no longer applies to those categories",
            },
        )
    )
    return results


def _check_catch_all_no_balancing(text: str) -> list[dict[str, Any]]:
    """Check 3: § 6255 / § 7922.000 invoked without adequate balancing test statement."""
    results: list[dict[str, Any]] = []
    if not _CATCH_ALL_EXEMPT_RE.search(text):
        return results
    if _BALANCING_LANGUAGE_RE.search(text):
        return results  # Adequate balancing language present
    results.append(
        _make_finding(
            "catch_all_no_balancing_test",
            "§ 6255 / § 7922.000 catch-all exemption invoked without the required specific balancing-test demonstration",
            "high",
            {
                "statute": "Gov. Code § 7922.000",
                "case_law": "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325",
                "detail": "The catch-all exemption requires a specific showing that the public interest in nondisclosure CLEARLY outweighs the interest in disclosure; conclusory statements are insufficient",
            },
        )
    )
    return results


def _check_attorney_client_overbroad(text: str) -> list[dict[str, Any]]:
    """Check 4 (merged with §1798.90.55): attorney-client overbroad claim for factual records."""
    results: list[dict[str, Any]] = []
    if not _AC_PRIVILEGE_RE.search(text):
        return results
    if not _FACTUAL_RECORD_RE.search(text):
        return results
    results.append(
        _make_finding(
            "attorney_client_overbroad_factual",
            "Attorney-client privilege (§ 7923.700) claimed for what appears to be factual records rather than confidential legal advice",
            "medium",
            {
                "statute": "Gov. Code § 7923.700",
                "case_law": "LA County Board of Supervisors v. Superior Court (2016) 2 Cal.5th 282",
                "detail": "§ 7923.700 protects attorney-client communications, not underlying facts or business records routed through counsel",
            },
        )
    )
    return results


def _check_alpr_cpra_exemption_scope(text: str) -> list[dict[str, Any]]:
    """Check 5: Civil Code § 1798.90.55 ALPR exemption applied outside SB 34 scope."""
    results: list[dict[str, Any]] = []
    if not _ALPR_CPRA_EXEMPT_RE.search(text):
        return results
    # The exemption under § 1798.90.55 applies only to ALPR operators
    # covered by SB 34 — non-operator agencies invoking it have a problem
    alpr_operator_re = re.compile(
        r"\b(?:alpr\s+operator|fixed\s+alpr|mobile\s+alpr|flock\s+safety|vigilant"
        r"|1798\.90\.51|1798\.90\.52)\b",
        re.IGNORECASE,
    )
    if alpr_operator_re.search(text):
        return results  # Operator context found — plausible claim
    results.append(
        _make_finding(
            "alpr_cpra_exemption_scope",
            "Civil Code § 1798.90.55 ALPR-CPRA exemption invoked outside apparent SB 34 operator context",
            "low",
            {
                "statute": "Civ. Code § 1798.90.55",
                "detail": "§ 1798.90.55 exempts ALPR data from CPRA only for operators governed by SB 34 (Civ. Code §§ 1798.90.51–55); verify operator status",
            },
        )
    )
    return results


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-3 Exemption Misapplication detection on a single document."""
    text = _get_text(doc)
    if not text:
        return []

    return (
        _check_law_enforcement_blanket(text)
        + _check_personnel_post_sb1421(text)
        + _check_catch_all_no_balancing(text)
        + _check_attorney_client_overbroad(text)
        + _check_alpr_cpra_exemption_scope(text)
    )
