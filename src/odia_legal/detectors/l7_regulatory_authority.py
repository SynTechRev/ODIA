"""L-7 Regulatory Authority Chains detector.

Identifies gaps, breaks, or overreaches in the chain of regulatory authority
that authorizes a public agency's action.

Core doctrine:
  An agency may act only within the authority expressly delegated to it by the
  legislature or governing body. Action beyond that grant is ultra vires and
  void. (City of Anaheim v. City of Los Angeles (2000) 83 Cal.App.4th 1117.)
  Sub-delegation is permissible only where expressly authorized.
  (Cal. Gov. Code § 53060; Yee v. City of Escondido (1992) 503 U.S. 519.)

Checks performed:
  1. Ultra vires action — agency action without traceable statutory or
     ordinance authority; document references agency power without citing
     an enabling statute, charter provision, or governing-body resolution.
  2. Sub-delegation without authorization — agency delegates authority to
     a subunit, contractor, or subordinate without citing express authority
     to sub-delegate (Gov. Code § 53060 or equivalent).
  3. Chain-of-authority gap — document references a directive, policy, or
     MOU that itself derives authority from another instrument, but the
     chain is broken (intermediate authority not cited or not in effect).
  4. Ordinance/resolution exceeding state law — local agency action that
     conflicts with or attempts to supersede preemptive state law without
     a Home Rule finding (Cal. Const., art. XI, § 5).
  5. Federal grant authority scope — agency action funded by a federal
     grant (JAG, COPS, UASI) that exceeds the permissible scope of the
     grant award without a scope-change amendment (2 CFR § 200.308).

Severity:
  high   — ultra vires action; ordinance exceeding state preemption
  medium — sub-delegation without authorization; chain-of-authority gap
  low    — federal grant scope question; authority-citation missing only

Finding contract follows the ODIA anomaly dict standard.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# --- Ultra vires ---
# Action verbs that imply affirmative agency exercise of power
_ACTION_VERB_RE = re.compile(
    r"\b(?:adopted?|enacted?|promulgated?|issued?|authorized?|approved?|"
    r"established?|created?|implemented?|deployed?|purchased?|acquired?|"
    r"entered\s+into|executed?|awarded?|contracted?)\b",
    re.IGNORECASE,
)

# Authority citation — statute, ordinance, resolution, charter
_AUTHORITY_CITE_RE = re.compile(
    r"\b(?:pursuant\s+to|under\s+(?:the\s+)?authority\s+of|"
    r"authorized\s+(?:by|under)|as\s+authorized\s+(?:by|under)|"
    r"in\s+accordance\s+with|under\s+(?:Gov(?:ernment)?\.?\s+Code|"
    r"Cal(?:ifornia)?\.?\s+(?:Gov|Pen|Civ|Veh|Ed)|"
    r"(?:the\s+)?(?:Municipal\s+)?Code|(?:the\s+)?Charter|"
    r"Ordinance\s+(?:No\.?\s*)?\d+|Resolution\s+(?:No\.?\s*)?\d+|"
    r"(?:the\s+)?(?:City|County|Board)\s+(?:Charter|Ordinance|Resolution)|"
    r"§\s*\d+|section\s+\d+|title\s+\d+))\b",
    re.IGNORECASE,
)

_ULTRA_VIRES_TRIGGER_RE = re.compile(
    r"\b(?:ultra\s+vires|beyond\s+(?:its|the\s+agency'?s?|their)\s+"
    r"(?:authority|power|jurisdiction|scope)|"
    r"without\s+(?:statutory|legal|legislative)\s+authority|"
    r"not\s+authorized\s+(?:by|under)\s+(?:law|statute|code)|"
    r"lacked?\s+(?:authority|jurisdiction|power)\s+to|"
    r"exceeded?\s+(?:its|the\s+agency'?s?|their)\s+(?:authority|jurisdiction|power))\b",
    re.IGNORECASE,
)

# --- Sub-delegation ---
_DELEGATION_TRIGGER_RE = re.compile(
    r"\b(?:delegated?\s+(?:to|authority)|sub.?delegat(?:ed?|ion)|"
    r"assigned?\s+(?:authority|responsibility|power)\s+to|"
    r"(?:contractor|vendor|third.?party|subcontractor|officer|director)\s+"
    r"(?:was|is|are|were)\s+authorized|"
    r"authority\s+(?:was|is|are|were)\s+(?:delegated?|assigned?|transferred?))\b",
    re.IGNORECASE,
)

_DELEGATION_AUTH_RE = re.compile(
    r"\b(?:"
    r"(?:pursuant\s+to|under|per)\s+(?:Gov(?:ernment)?\.?\s+Code\s+)?(?:§\s*)?53060"
    r"|express(?:ly)?\s+authorized\s+(?:by|under|to\s+sub.?delegat)"
    r"|delegat(?:ion|ing)\s+authority\s+(?:pursuant\s+to|under|per)\s+"
    r"|(?:authorized|authoriz\w+)\s+under\s+Charter\s+(?:section|§)\s*\d+"
    r"|Charter\s+(?:section|§)\s*\d+\s+(?:authoriz|delegat|permit)"
    r"|(?:ordinance|resolution)\s+(?:no\.?\s*)?\d+\s+(?:authoriz|delegat)"
    r")\b",
    re.IGNORECASE,
)

# --- Chain-of-authority gap ---
_CHAIN_TRIGGER_RE = re.compile(
    r"\b(?:memorandum\s+of\s+(?:understanding|agreement)|"
    r"\bMOU\b|\bMOA\b|interagency\s+agreement|"
    r"(?:board|council|commission)\s+(?:directive|policy|resolution)|"
    r"administrative\s+(?:directive|order|policy)|"
    r"general\s+order|department\s+policy|standing\s+order)\b",
    re.IGNORECASE,
)

_CHAIN_AUTHORITY_CITED_RE = re.compile(
    r"(?:"
    # word-boundary anchored forms
    r"\bpursuant\s+to\b"
    r"|\bauthorized\s+(?:by|under)\b"
    r"|\bunder\s+(?:the\s+authority\s+of\s+)?section\s+\d+"
    r"|\bGov(?:ernment)?\.?\s+Code\b"
    r"|\bPen(?:al)?\.?\s+Code\b"
    r"|\bOrdinance\s+(?:No\.?\s*)?\d+"
    r"|\bResolution\s+(?:No\.?\s*)?\d+"
    r"|\bCharter\s+(?:section|art(?:icle)?)\s*\d+"
    # § can appear mid-sentence, no word-boundary needed
    r"|§\s*\d+"
    r")",
    re.IGNORECASE,
)

# --- State law preemption ---
_LOCAL_ACTION_RE = re.compile(
    r"\b(?:(?:city|county|district|local)\s+(?:ordinance|resolution|policy|rule|regulation)|"
    r"municipal\s+(?:code|ordinance|regulation)|"
    r"(?:adopted|enacted|passed)\s+(?:an?\s+)?(?:ordinance|resolution|regulation))\b",
    re.IGNORECASE,
)

_PREEMPTION_CONFLICT_RE = re.compile(
    r"\b(?:notwithstanding\s+(?:state|California)\s+(?:law|code)|"
    r"in\s+lieu\s+of\s+(?:state|California)\s+(?:law|requirement)|"
    r"supersedes?\s+(?:state|California)|"
    r"conflicts?\s+with\s+(?:state|California)|"
    r"more\s+restrictive\s+than\s+(?:state|California)|"
    r"stricter\s+than\s+(?:state|California)\s+(?:law|requirement))\b",
    re.IGNORECASE,
)

_HOME_RULE_CITED_RE = re.compile(
    r"\b(?:home\s+rule|art(?:icle)?\.?\s*XI|charter\s+city|"
    r"municipal\s+affairs\s+doctrine|"
    r"Cal(?:ifornia)?\.?\s+Const(?:itution)?\.?\s*art(?:icle)?\.?\s*XI)\b",
    re.IGNORECASE,
)

# --- Federal grant scope ---
_FEDERAL_GRANT_RE = re.compile(
    r"\b(?:JAG|COPS|UASI|Byrne\s+grant|federal\s+grant|"
    r"grant\s+(?:award|funds?|funding)|"
    r"(?:DOJ|DHS|BJA|FEMA)\s+(?:grant|funding|award))\b",
    re.IGNORECASE,
)

_GRANT_SCOPE_EXCEED_RE = re.compile(
    r"\b(?:not\s+included\s+in\s+(?:the\s+)?(?:grant|award|budget)|"
    r"outside\s+(?:the\s+)?(?:scope|purpose)\s+of\s+(?:the\s+)?(?:grant|award)|"
    r"unallowable\s+(?:under|per)\s+(?:the\s+)?grant|"
    r"beyond\s+(?:the\s+)?(?:grant|award)\s+(?:scope|purpose|terms?)|"
    r"not\s+authorized\s+(?:under|by)\s+(?:the\s+)?(?:grant|award))\b",
    re.IGNORECASE,
)

_GRANT_AMENDMENT_RE = re.compile(
    r"\b(?:scope\s+change\s+amendment|grant\s+modification|"
    r"200\.308|prior\s+approval\s+(?:from|of)\s+(?:the\s+)?(?:awarding|federal)|"
    r"amended\s+(?:award|grant))\b",
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
        "id": f"legal:l7:regulatory_authority:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l7_regulatory_authority",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def _check_ultra_vires(text: str) -> list[dict[str, Any]]:
    """Check for explicit ultra vires language or action without authority cite."""
    if _ULTRA_VIRES_TRIGGER_RE.search(text):
        return [
            _make_finding(
                "ultra_vires_action",
                "Document references action beyond agency's delegated authority "
                "(ultra vires) — action may be void",
                "high",
                {
                    "statute": "Cal. Const., art. XI, § 5; Gov. Code § 53060",
                    "case": "City of Anaheim v. City of Los Angeles (2000) "
                            "83 Cal.App.4th 1117",
                    "detail": (
                        "An agency has only those powers expressly granted by the "
                        "legislature or governing body. Action beyond that grant is "
                        "ultra vires and may be declared void by a court."
                    ),
                },
            )
        ]

    # Action verbs without any authority citation
    if _ACTION_VERB_RE.search(text) and not _AUTHORITY_CITE_RE.search(text):
        return [
            _make_finding(
                "action_without_authority_cite",
                "Agency action described without traceable statutory or "
                "ordinance authority citation",
                "low",
                {
                    "statute": "Gov. Code § 53060",
                    "detail": (
                        "Documents describing affirmative agency actions (adoption, "
                        "procurement, deployment) should cite the enabling statute, "
                        "ordinance, or resolution that authorizes the action. "
                        "Absence of an authority citation raises an ultra vires risk."
                    ),
                },
            )
        ]
    return []


def _check_subdelegation(text: str) -> list[dict[str, Any]]:
    """Check for delegation without express sub-delegation authority."""
    if not _DELEGATION_TRIGGER_RE.search(text):
        return []
    if _DELEGATION_AUTH_RE.search(text):
        return []
    return [
        _make_finding(
            "subdelegation_no_authority",
            "Authority delegated to subordinate, contractor, or subunit without "
            "citing express sub-delegation authorization (Gov. Code § 53060)",
            "medium",
            {
                "statute": "Gov. Code § 53060",
                "detail": (
                    "Sub-delegation of authority is permissible only where expressly "
                    "authorized by statute, charter, or ordinance. A general grant of "
                    "administrative authority does not carry an implied power to "
                    "sub-delegate. (Gov. Code § 53060.)"
                ),
            },
        )
    ]


def _check_chain_gap(text: str) -> list[dict[str, Any]]:
    """Check for MOUs, directives, or policies without authority chain citation."""
    if not _CHAIN_TRIGGER_RE.search(text):
        return []
    if _CHAIN_AUTHORITY_CITED_RE.search(text):
        return []
    return [
        _make_finding(
            "authority_chain_gap",
            "MOU, interagency agreement, or administrative directive present without "
            "citation to the statutory authority that authorizes it",
            "medium",
            {
                "statute": "Gov. Code § 53060",
                "detail": (
                    "Every interagency agreement, MOU, or administrative directive "
                    "must trace back to an enabling statute, charter provision, or "
                    "duly adopted ordinance/resolution. A gap in that chain renders "
                    "actions taken under the instrument legally vulnerable."
                ),
            },
        )
    ]


def _check_preemption(text: str) -> list[dict[str, Any]]:
    """Check for local ordinance that may conflict with preemptive state law."""
    if not _LOCAL_ACTION_RE.search(text):
        return []
    if not _PREEMPTION_CONFLICT_RE.search(text):
        return []
    if _HOME_RULE_CITED_RE.search(text):
        return []
    return [
        _make_finding(
            "ordinance_exceeds_state_preemption",
            "Local ordinance or regulation appears to conflict with or supersede "
            "state law without a Home Rule (art. XI, § 5) finding",
            "high",
            {
                "statute": "Cal. Const., art. XI, § 5",
                "detail": (
                    "California's preemption doctrine bars local agencies from "
                    "enacting ordinances that conflict with general state law, "
                    "unless the agency is a charter city acting on a 'municipal "
                    "affair' (Cal. Const., art. XI, § 5). An ordinance that "
                    "conflicts with state law without that finding may be void."
                ),
            },
        )
    ]


def _check_grant_scope(text: str) -> list[dict[str, Any]]:
    """Check for agency actions that may exceed federal grant scope."""
    if not _FEDERAL_GRANT_RE.search(text):
        return []
    if not _GRANT_SCOPE_EXCEED_RE.search(text):
        return []
    if _GRANT_AMENDMENT_RE.search(text):
        return []
    return [
        _make_finding(
            "federal_grant_scope_exceeded",
            "Agency action appears to exceed the authorized scope of the federal "
            "grant award without a scope-change amendment (2 CFR § 200.308)",
            "low",
            {
                "regulation": "2 C.F.R. § 200.308",
                "detail": (
                    "Federal grant recipients may not use grant funds for purposes "
                    "outside the approved scope of work. Significant scope changes "
                    "require prior approval from the federal awarding agency "
                    "(2 CFR § 200.308). Unauthorized scope changes may trigger "
                    "disallowed costs and repayment obligations."
                ),
            },
        )
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-7 Regulatory Authority Chains analysis on a single document."""
    text = _get_text(doc)
    if not text:
        return []

    return (
        _check_ultra_vires(text)
        + _check_subdelegation(text)
        + _check_chain_gap(text)
        + _check_preemption(text)
        + _check_grant_scope(text)
    )
