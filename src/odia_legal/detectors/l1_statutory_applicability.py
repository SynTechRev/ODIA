"""L-1 Statutory Applicability detector.

Identifies which California, federal, and multi-state statutes apply to a
public-agency document based on its content, metadata, and detected document type.

Applicability mapping logic:
  - Documents containing ALPR / license plate reader references
    → Civ. Code §§ 1798.90.51–55 (SB 34) + Veh. Code § 2413
  - Documents referencing surveillance technology acquisition
    → Gov. Code §§ 36000–36010 (AB 481 military equipment ordinance)
  - Documents referencing public records requests / CPRA
    → Gov. Code §§ 7920.000–7931.000 (CPRA)
  - Documents referencing federal grants (JAG, Byrne, OJP, COPS)
    → 34 U.S.C. § 10152 + 2 CFR Part 200
  - Documents referencing body cameras / BWC
    → Gov. Code § 36000 (AB 481) + any existing agency BWC policy
  - Documents referencing peace officer personnel records / discipline
    → Pen. Code §§ 832.7–832.8 + Gov. Code § 7923.625

Finding contract:
  {
    "id":       "legal:l1:statutory_applicability:<statute_key>",
    "issue":    str,
    "severity": "low",
    "layer":    "l1_statutory_applicability",
    "details":  {
      "statute":       str,       # canonical citation
      "corpus_id":     str,
      "trigger_terms": list[str], # terms in document that triggered detection
      "section_title": str | None,
      "relevance":     str,       # explanation of why statute applies
    }
  }

All L-1 findings are informational (severity=low) — they flag applicable law,
not violations. L-2 (Procedural Compliance) and L-3 (Exemption Misapplication)
use L-1 output to scope their own analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Applicability rules — (trigger_patterns, statute_citation, corpus_id, title,
#                         relevance_text)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ApplicabilityRule:
    rule_id: str
    statute: str  # canonical citation
    corpus_id: str
    section_title: str
    relevance: str
    triggers: tuple[str, ...]  # lowercase keyword/phrase triggers
    severity: str = "low"


_RULES: list[ApplicabilityRule] = [
    # --- ALPR / License Plate Reader ---
    ApplicabilityRule(
        rule_id="alpr_sb34_civil",
        statute="Civ. Code § 1798.90.51",
        corpus_id="cal_civ_code",
        section_title="ALPR — definitions (SB 34)",
        relevance="Document references ALPR technology; SB 34 governs operator requirements, retention limits, and sharing restrictions.",
        triggers=(
            "alpr",
            "license plate reader",
            "license plate recognition",
            "lpr",
            "flock safety",
            "vigilant",
            "automated license",
        ),
    ),
    ApplicabilityRule(
        rule_id="alpr_sb34_retention",
        statute="Civ. Code § 1798.90.53",
        corpus_id="cal_civ_code",
        section_title="ALPR — data retention limits (SB 34)",
        relevance="SB 34 limits ALPR data retention to 60 days unless an active investigation or court order exists.",
        triggers=(
            "alpr",
            "license plate reader",
            "lpr",
            "data retention",
            "retention period",
            "plate data",
        ),
    ),
    ApplicabilityRule(
        rule_id="alpr_veh_2413",
        statute="Veh. Code § 2413",
        corpus_id="cal_veh_code",
        section_title="ALPR — law enforcement use restrictions",
        relevance="Vehicle Code § 2413 imposes auditing and purpose limitations on law enforcement use of ALPR data.",
        triggers=(
            "alpr",
            "license plate reader",
            "lpr",
            "plate data",
            "automated license plate",
        ),
    ),
    # --- AB 481 Surveillance Technology ---
    ApplicabilityRule(
        rule_id="ab481_acquisition",
        statute="Gov. Code § 36000",
        corpus_id="cal_gov_code",
        section_title="AB 481 — military equipment definitions",
        relevance="AB 481 requires governing-body approval and annual reporting before acquiring or using specified surveillance technology.",
        triggers=(
            "ab 481",
            "ab481",
            "military equipment",
            "surveillance technology",
            "drones",
            "uas",
            "stingray",
            "imsi catcher",
            "cell site simulator",
            "biometric",
            "facial recognition",
        ),
    ),
    ApplicabilityRule(
        rule_id="ab481_annual_report",
        statute="Gov. Code § 36002",
        corpus_id="cal_gov_code",
        section_title="AB 481 — annual report requirement",
        relevance="AB 481 requires agencies to publish an annual report on the use, complaints, and violations related to military equipment.",
        triggers=(
            "ab 481",
            "ab481",
            "annual report",
            "technology use policy",
            "military equipment",
        ),
    ),
    # --- CPRA ---
    ApplicabilityRule(
        rule_id="cpra_access",
        statute="Gov. Code § 7920.000",
        corpus_id="cal_gov_code",
        section_title="CPRA — legislative findings and intent",
        relevance="CPRA governs public access to government records; any document involving records requests, exemptions, or disclosure decisions is subject to CPRA analysis.",
        triggers=(
            "public records",
            "cpra",
            "california public records act",
            "records request",
            "foia",
            "government code 6250",
            "government code 7920",
            "disclosure",
            "exemption",
        ),
    ),
    ApplicabilityRule(
        rule_id="cpra_ten_day",
        statute="Gov. Code § 7922.535",
        corpus_id="cal_gov_code",
        section_title="CPRA — ten-calendar-day response period",
        relevance="CPRA requires agencies to respond to records requests within 10 calendar days; documents related to response timing implicate § 7922.535.",
        triggers=(
            "ten day",
            "10 day",
            "10-day",
            "response period",
            "records response",
            "request response",
        ),
    ),
    ApplicabilityRule(
        rule_id="cpra_law_enforcement_exemption",
        statute="Gov. Code § 7923.650",
        corpus_id="cal_gov_code",
        section_title="CPRA — law enforcement investigative records",
        relevance="Documents involving law enforcement records, investigations, or withholding claims invoke the § 7923.650 law enforcement exemption.",
        triggers=(
            "investigative record",
            "law enforcement record",
            "police record",
            "6254(f)",
            "7923.650",
            "withhold",
            "investigation",
        ),
    ),
    # --- Federal Grant Compliance ---
    ApplicabilityRule(
        rule_id="jag_grant",
        statute="34 U.S.C. § 10152",
        corpus_id="us_code",
        section_title="JAG — Edward Byrne Memorial Justice Assistance Grant",
        relevance="Documents referencing JAG, Byrne, or OJP grants implicate 34 U.S.C. § 10152 and associated grant conditions.",
        triggers=(
            "jag",
            "justice assistance grant",
            "byrne grant",
            "edward byrne",
            "bjaa",
            "ojp",
            "cops grant",
            "bureau of justice assistance",
            "bja",
        ),
    ),
    ApplicabilityRule(
        rule_id="uniform_guidance",
        statute="2 C.F.R. § 200.303",
        corpus_id="cfr_2_200",
        section_title="Uniform Guidance — internal controls",
        relevance="Entities receiving federal awards must maintain internal controls compliant with 2 CFR § 200.303; documents related to grant expenditures, procurement, or audits are covered.",
        triggers=(
            "federal grant",
            "federal award",
            "uniform guidance",
            "2 cfr",
            "grant compliance",
            "anti-supplanting",
            "supplanting",
        ),
    ),
    # --- Peace Officer Records ---
    ApplicabilityRule(
        rule_id="sb1421_records",
        statute="Pen. Code § 832.7",
        corpus_id="cal_pen_code",
        section_title="Peace officer records — SB 1421 public disclosure categories",
        relevance="SB 1421 (effective 2019) makes specified peace officer misconduct records public; documents involving officer use-of-force, sexual assault findings, or dishonesty determinations are covered.",
        triggers=(
            "sb 1421",
            "sb1421",
            "peace officer",
            "police officer",
            "officer record",
            "use of force",
            "officer discipline",
            "internal affairs",
            "officer misconduct",
        ),
    ),
    # --- Body Cameras ---
    ApplicabilityRule(
        rule_id="bwc_policy",
        statute="Gov. Code § 36000",
        corpus_id="cal_gov_code",
        section_title="AB 481 — military equipment (includes BWC programs)",
        relevance="Body-worn camera programs must comply with AB 481 if cameras are classified as military equipment; also subject to any agency technology use policy.",
        triggers=(
            "body camera",
            "body worn camera",
            "bwc",
            "body-worn",
            "axon",
            "body cam",
        ),
    ),
    # --- Constitutional — Fourth Amendment / Carpenter ---
    ApplicabilityRule(
        rule_id="fourth_amendment_surveillance",
        statute="42 U.S.C. § 1983",
        corpus_id="us_code",
        section_title="Civil action for deprivation of rights",
        relevance="Surveillance programs that collect location data without a warrant may implicate Fourth Amendment rights actionable under 42 U.S.C. § 1983.",
        triggers=(
            "fourth amendment",
            "4th amendment",
            "reasonable expectation of privacy",
            "carpenter",
            "warrant",
            "warrantless",
            "privacy",
            "42 usc 1983",
            "42 u.s.c. 1983",
        ),
    ),
    # ------------------------------------------------------------------
    # Multi-state public records laws (Phase 6)
    # ------------------------------------------------------------------
    ApplicabilityRule(
        rule_id="oregon_pub_records_ors192",
        statute="ORS § 192.314",
        corpus_id="or_pub_records",
        section_title="Oregon Public Records Law — right to inspect",
        relevance=(
            "Oregon's Public Records Law (ORS Ch. 192) grants the public the right "
            "to inspect and copy public records. Response required within 5 business "
            "days. Document references Oregon agency or ORS citation."
        ),
        triggers=(
            "oregon public records",
            "ors 192",
            "ors ch. 192",
            "oregon records request",
            "oregon department",
            "oregon agency",
            "oregon police",
            "oregon sheriff",
        ),
    ),
    ApplicabilityRule(
        rule_id="oregon_pub_records_law_enforcement",
        statute="ORS § 192.345",
        corpus_id="or_pub_records",
        section_title="Oregon Public Records Law — law enforcement exemption",
        relevance=(
            "ORS 192.345 exempts investigatory law enforcement information only "
            "where disclosure would interfere with enforcement proceedings or "
            "endanger law enforcement personnel."
        ),
        triggers=(
            "ors 192.345",
            "oregon law enforcement records",
            "oregon investigative records",
        ),
    ),
    ApplicabilityRule(
        rule_id="washington_pub_records_rcw4256",
        statute="RCW § 42.56.070",
        corpus_id="wa_pub_records",
        section_title="Washington Public Records Act — access and response",
        relevance=(
            "Washington's Public Records Act (RCW 42.56) requires agencies to "
            "respond to public records requests within 5 business days. "
            "Exemptions are narrowly construed. Penalties up to $100/day for "
            "violations (RCW 42.56.565)."
        ),
        triggers=(
            "washington public records",
            "rcw 42.56",
            "washington records request",
            "washington state agency",
            "washington state police",
            "washington state sheriff",
            "wa public records act",
            "pra request",
        ),
    ),
    ApplicabilityRule(
        rule_id="washington_pub_records_law_enforcement",
        statute="RCW § 42.56.240",
        corpus_id="wa_pub_records",
        section_title="Washington Public Records Act — law enforcement exemptions",
        relevance=(
            "RCW 42.56.240 exempts specific law enforcement investigative records "
            "only where nondisclosure is essential to effective law enforcement. "
            "The exemption must be narrowly applied."
        ),
        triggers=(
            "rcw 42.56.240",
            "washington law enforcement records",
            "washington investigative records",
        ),
    ),
    ApplicabilityRule(
        rule_id="texas_pub_info_gc552",
        statute="Tex. Gov't Code § 552.221",
        corpus_id="tx_pub_info",
        section_title="Texas Public Information Act — request and response",
        relevance=(
            "Texas's Public Information Act (Gov. Code Ch. 552) requires agencies "
            "to respond within 10 business days. Unique: agency must request an "
            "AG opinion before withholding records (§ 552.301). Failure to disclose "
            "is a Class B misdemeanor (§ 552.353)."
        ),
        triggers=(
            "texas public information",
            "texas open records",
            "gov. code 552",
            "gov't code 552",
            "texas records request",
            "texas agency",
            "texas police department",
            "texas sheriff",
            "tpia",
        ),
    ),
    ApplicabilityRule(
        rule_id="texas_pub_info_ag_opinion",
        statute="Tex. Gov't Code § 552.301",
        corpus_id="tx_pub_info",
        section_title="Texas Public Information Act — AG opinion required before withholding",
        relevance=(
            "Texas uniquely requires agencies to request an AG opinion before "
            "withholding information. Failure to timely seek an AG opinion "
            "waives the right to withhold."
        ),
        triggers=(
            "texas attorney general opinion",
            "ag opinion",
            "texas ag",
            "gov't code 552.301",
            "gov. code 552.301",
        ),
    ),
]

# Pre-compile trigger patterns for efficiency
_COMPILED_RULES: list[tuple[ApplicabilityRule, re.Pattern]] = [
    (
        rule,
        re.compile(
            r"\b(" + "|".join(re.escape(t) for t in rule.triggers) + r")\b",
            re.IGNORECASE,
        ),
    )
    for rule in _RULES
]


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-1 Statutory Applicability detection on a single document.

    Args:
        doc: Document dict with at least a ``text`` / ``content`` field.

    Returns:
        List of applicability findings (severity=low, informational).
    """
    text = _get_text(doc)
    if not text:
        return []

    findings: list[dict[str, Any]] = []
    seen_statutes: set[str] = set()

    for rule, pattern in _COMPILED_RULES:
        if rule.statute in seen_statutes:
            continue
        matches = pattern.findall(text)
        if not matches:
            continue

        seen_statutes.add(rule.statute)
        trigger_terms = list({m.lower() for m in matches})[:5]

        findings.append(
            {
                "id": f"legal:l1:statutory_applicability:{rule.rule_id}",
                "issue": f"Statute applies: {rule.statute} — {rule.section_title}",
                "severity": rule.severity,
                "layer": "l1_statutory_applicability",
                "details": {
                    "statute": rule.statute,
                    "corpus_id": rule.corpus_id,
                    "section_title": rule.section_title,
                    "trigger_terms": trigger_terms,
                    "relevance": rule.relevance,
                },
            }
        )

    return findings


def detect_applicable_statutes(doc: dict[str, Any]) -> list[str]:
    """Return just the list of applicable statute citation strings."""
    return [f["details"]["statute"] for f in detect(doc)]


def _get_text(doc: dict[str, Any]) -> str:
    for key in ("text", "content", "body", "raw_text"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""
