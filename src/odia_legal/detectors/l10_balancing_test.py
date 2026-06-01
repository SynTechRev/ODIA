"""L-10 Balancing Test Analyzer.

Evaluates balancing-test arguments in public-agency documents against
three canonical frameworks:

  1. Mathews v. Eldridge (1976) — due process balancing:
       (a) private interest affected; (b) risk of erroneous deprivation +
       value of additional safeguards; (c) government's interest / fiscal cost.
     Applies to: administrative terminations, benefit denials, license revocations.

  2. CPRA public interest balancing (Gov. Code § 7922.000 / § 6255):
       nondisclosure interest must CLEARLY outweigh disclosure interest.
     Applies to: CPRA catch-all exemption invocations (Times Mirror standard).

  3. Carpenter mosaic theory — Fourth Amendment location privacy:
       comprehensive surveillance that reveals the "privacies of daily life"
       requires individualized suspicion even if each data point is public.
     Applies to: ALPR, geofence, CSLI, persistent tracking.

For each framework, the detector checks whether:
  - The balancing test is invoked / relevant
  - The required elements are addressed
  - The conclusion is supported by the weighing

All L-10 findings are severity="medium" by default (analysis quality flag).
If the balancing result appears to contradict the law, severity="high".
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# --- Mathews v. Eldridge ---
_MATHEWS_TRIGGER_RE = re.compile(
    r"\b(?:mathews\s+v\.?\s+eldridge|due\s+process\s+balanc|"
    r"three.?(?:part|factor|prong)\s+test|"
    r"administrative\s+(?:termination|hearing|procedure)|"
    r"benefit\s+(?:terminat|denial|revok)|"
    r"license\s+(?:revok|suspend)|"
    r"procedural\s+due\s+process)\b",
    re.IGNORECASE,
)

_MATHEWS_PRIVATE_INTEREST_RE = re.compile(
    r"\b(?:private\s+interest|individual\s+interest|"
    r"interest\s+of\s+the\s+(?:individual|person|claimant)|"
    r"deprivat(?:ion|ed)\s+of|loss\s+of\s+(?:benefit|right|license|property))\b",
    re.IGNORECASE,
)

_MATHEWS_ERRONEOUS_RE = re.compile(
    r"\b(?:risk\s+of\s+erroneous\s+deprivation|erroneous\s+deprivation|"
    r"additional\s+(?:procedure|safeguard|protection)|"
    r"value\s+of\s+(?:additional|extra)\s+(?:procedure|process))\b",
    re.IGNORECASE,
)

_MATHEWS_GOVT_INTEREST_RE = re.compile(
    r"\b(?:government(?:al)?\s+interest|fiscal\s+(?:cost|burden)|"
    r"administrative\s+(?:burden|cost|interest)|"
    r"public\s+(?:cost|interest)\s+in\s+(?:the\s+)?(?:procedure|process)|"
    r"countervailing\s+interest)\b",
    re.IGNORECASE,
)

# --- CPRA § 7922.000 / § 6255 balancing ---
_CPRA_BALANCE_TRIGGER_RE = re.compile(
    r"\b(?:7922\.000|6255|catch.all\s+exemption|"
    r"public\s+interest\s+in\s+(?:non)?disclosure|"
    r"nondisclosure|clearly\s+outweigh)\b",
    re.IGNORECASE,
)

_CPRA_BALANCE_ADEQUATE_RE = re.compile(
    r"\b(?:clearly\s+outweigh|specific(?:ally)?\s+demonstrate|"
    r"particularized\s+showing|deliberative\s+process|"
    r"frank\s+(?:internal\s+)?deliberation|inhibit|"
    r"chilling\s+effect)\b",
    re.IGNORECASE,
)

_CPRA_CONCLUSORY_RE = re.compile(
    r"\b(?:in\s+the\s+public\s+interest|public\s+interest\s+(?:requires|demands|dictates)|"
    r"it\s+is\s+in\s+the\s+public\s+interest|public\s+interest\s+justifies)\b",
    re.IGNORECASE,
)

# --- Carpenter mosaic ---
_CARPENTER_TRIGGER_RE = re.compile(
    r"\b(?:carpenter|mosaic\s+theory|mosaic\s+effect|"
    r"privacies\s+of\s+daily\s+life|comprehensive\s+(?:surveillance|tracking)|"
    r"long.term\s+(?:tracking|surveillance|monitoring))\b",
    re.IGNORECASE,
)

_CARPENTER_ELEMENTS_RE = re.compile(
    r"\b(?:individualized\s+suspicion|reasonable\s+expectation\s+of\s+privacy|"
    r"warrant\s+(?:required|needed)|probable\s+cause|"
    r"third.party\s+doctrine\s+(?:does\s+not\s+apply|inapplicable)|"
    r"aggregat(?:ion|ed)\s+(?:data|information)|"
    r"retroactive\s+(?:surveillance|tracking))\b",
    re.IGNORECASE,
)

_ALPR_MOSAIC_RE = re.compile(
    r"\b(?:alpr|license\s+plate\s+reader|lpr|geofence|"
    r"csli|cell.site\s+location|persistent\s+(?:location|surveillance))\b",
    re.IGNORECASE,
)


def _get_text(doc: dict[str, Any]) -> str:
    for key in ("text", "content", "body", "raw_text"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _make_finding(rule_id: str, issue: str, severity: str, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"legal:l10:balancing_test:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l10_balancing_test",
        "details": details,
    }


def _check_mathews(text: str) -> list[dict[str, Any]]:
    """Check Mathews v. Eldridge due process balancing."""
    results: list[dict[str, Any]] = []
    if not _MATHEWS_TRIGGER_RE.search(text):
        return results

    missing: list[str] = []
    if not _MATHEWS_PRIVATE_INTEREST_RE.search(text):
        missing.append("private interest affected")
    if not _MATHEWS_ERRONEOUS_RE.search(text):
        missing.append("risk of erroneous deprivation + value of additional safeguards")
    if not _MATHEWS_GOVT_INTEREST_RE.search(text):
        missing.append("government's interest / fiscal burden")

    if missing:
        results.append(
            _make_finding(
                "mathews_incomplete",
                f"Mathews v. Eldridge due process balancing invoked but {len(missing)} of 3 required elements missing: {'; '.join(missing)}",
                "medium" if len(missing) < 3 else "high",
                {
                    "framework": "Mathews v. Eldridge (1976) 424 U.S. 319",
                    "missing_elements": missing,
                    "detail": "Due process requires analysis of: (1) private interest, (2) risk of erroneous deprivation + value of additional procedure, (3) government's interest",
                },
            )
        )
    return results


def _check_cpra_balancing(text: str) -> list[dict[str, Any]]:
    """Check CPRA § 7922.000 / § 6255 balancing test adequacy."""
    results: list[dict[str, Any]] = []
    if not _CPRA_BALANCE_TRIGGER_RE.search(text):
        return results

    if _CPRA_CONCLUSORY_RE.search(text) and not _CPRA_BALANCE_ADEQUATE_RE.search(text):
        results.append(
            _make_finding(
                "cpra_conclusory_balancing",
                "CPRA catch-all exemption (§ 7922.000) invoked with only conclusory public-interest statement — Times Mirror requires specific showing that nondisclosure CLEARLY outweighs disclosure",
                "high",
                {
                    "framework": "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325",
                    "statute": "Gov. Code § 7922.000",
                    "detail": "A bare assertion that disclosure is 'not in the public interest' is insufficient; agency must specifically demonstrate why nondisclosure clearly outweighs the public's right to know",
                },
            )
        )
    elif _CPRA_BALANCE_TRIGGER_RE.search(text) and not _CPRA_BALANCE_ADEQUATE_RE.search(text) and not _CPRA_CONCLUSORY_RE.search(text):
        results.append(
            _make_finding(
                "cpra_balancing_absent",
                "CPRA § 7922.000 cited but no balancing-test analysis found in document",
                "medium",
                {
                    "framework": "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325",
                    "statute": "Gov. Code § 7922.000",
                    "detail": "Agency must articulate specific reasons why the public interest in nondisclosure clearly outweighs the public interest in disclosure",
                },
            )
        )
    return results


def _check_carpenter_mosaic(text: str) -> list[dict[str, Any]]:
    """Check Carpenter mosaic theory application to location surveillance."""
    results: list[dict[str, Any]] = []

    has_alpr = bool(_ALPR_MOSAIC_RE.search(text))
    has_carpenter = bool(_CARPENTER_TRIGGER_RE.search(text))

    if not (has_alpr or has_carpenter):
        return results

    if has_alpr and not has_carpenter:
        results.append(
            _make_finding(
                "alpr_carpenter_not_analyzed",
                "Comprehensive location surveillance (ALPR/CSLI) present without Carpenter mosaic-theory analysis",
                "medium",
                {
                    "framework": "Carpenter v. United States (2018) 585 U.S. 296",
                    "detail": "Carpenter requires analysis of whether long-term surveillance aggregates into a comprehensive chronicle of daily movements requiring a warrant",
                },
            )
        )
    elif has_carpenter and not _CARPENTER_ELEMENTS_RE.search(text):
        results.append(
            _make_finding(
                "carpenter_elements_missing",
                "Carpenter cited but key mosaic-theory elements not addressed (individualized suspicion, aggregation, reasonable expectation of privacy)",
                "medium",
                {
                    "framework": "Carpenter v. United States (2018) 585 U.S. 296",
                    "detail": "A complete Carpenter analysis requires: individualized suspicion assessment, aggregation analysis, and why the third-party doctrine does not apply",
                },
            )
        )
    return results


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-10 Balancing Test analysis on a single document."""
    text = _get_text(doc)
    if not text:
        return []

    return (
        _check_mathews(text)
        + _check_cpra_balancing(text)
        + _check_carpenter_mosaic(text)
    )
