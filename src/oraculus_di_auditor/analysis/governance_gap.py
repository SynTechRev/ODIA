"""Governance Gap Detector.

Detects documents that deploy or fund surveillance capabilities without the
corresponding governance artefacts.  The ODIA methodology treats governance
absence as structurally equivalent to a finding regardless of the
capability's underlying legality — if the governing body never saw the
technology in a public meeting, the deployment is ungoverned.

This detector builds on the vendor_database module so that vendor
signatures (Flock, Axon, Lexipol, etc.) and statutory triggers (SB 524, AB
481, CJIS, ALPR Privacy Act) are shared with the surveillance detector
rather than duplicated.

Findings emitted:

  governance:capability-without-council-approval  (critical/high)
  governance:data-retention-gap                   (high)
  governance:lexipol-boilerplate                  (medium)
  governance:consent-calendar-placement           (medium)
  governance:sole-source-without-justification    (high)
  governance:auto-renewal-clause                  (medium)
  governance:transparency-portal-absence          (medium)
"""

from __future__ import annotations

from typing import Any

from .text_utils import extract_text_content
from .vendor_database import (
    STATUTE_BY_KEY,
    VENDOR_BY_NAME,
    detect_auto_renewal,
    detect_consent_calendar,
    detect_sole_source,
    detect_statutes,
    detect_technologies,
    detect_vendors,
)


# ---------------------------------------------------------------------------
# Governance artefact vocabulary
# ---------------------------------------------------------------------------

COUNCIL_APPROVAL_KEYWORDS = (
    "council resolution",
    "council approval",
    "approved by city council",
    "approved by the council",
    "council vote",
    "public hearing",
    "adopted by the council",
    "resolution no.",
    "resolution no ",
)

RETENTION_POLICY_KEYWORDS = (
    "retention policy",
    "retention schedule",
    "data retention policy",
    "data purge",
    "deletion policy",
    "records destruction",
    "days of retention",
    "day retention",
)

TRANSPARENCY_PORTAL_KEYWORDS = (
    "transparency portal",
    "public dashboard",
    "surveillance technology report",
    "surveillance inventory",
    "public-facing dashboard",
)


def _has_any(text_lower: str, keywords: tuple[str, ...]) -> bool:
    return any(kw in text_lower for kw in keywords)


def _build(finding_id: str, issue: str, severity: str, **details: Any) -> dict[str, Any]:
    return {
        "id": finding_id,
        "issue": issue,
        "severity": severity,
        "layer": "governance",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def detect_governance_gap_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return findings

    text = extract_text_content(doc) or ""
    if not text.strip():
        return findings

    text_lower = text.lower()
    vendors = detect_vendors(text)
    techs = detect_technologies(text)
    statutes = detect_statutes(text)

    has_surveillance_capability = bool(techs) or any(
        VENDOR_BY_NAME[v].category in {"alpr", "bwc", "drone"} for v in vendors
    )
    has_council_approval = _has_any(text_lower, COUNCIL_APPROVAL_KEYWORDS)
    has_retention_policy = _has_any(text_lower, RETENTION_POLICY_KEYWORDS)

    # -----------------------------------------------------------------------
    # 1. Capability deployed without council approval
    # -----------------------------------------------------------------------
    if has_surveillance_capability and not has_council_approval:
        findings.append(
            _build(
                "governance:capability-without-council-approval",
                (
                    "Surveillance capability referenced without council "
                    "resolution or approval language"
                ),
                "critical",
                vendors=list(vendors.keys()),
                technologies=list(techs.keys()),
            )
        )

    # -----------------------------------------------------------------------
    # 2. Data-retention gap
    # -----------------------------------------------------------------------
    if has_surveillance_capability and not has_retention_policy:
        findings.append(
            _build(
                "governance:data-retention-gap",
                "Surveillance capability without data-retention policy reference",
                "high",
                technologies=list(techs.keys()),
            )
        )

    # -----------------------------------------------------------------------
    # 3. Lexipol boilerplate signature
    # -----------------------------------------------------------------------
    if "Lexipol" in vendors:
        findings.append(
            _build(
                "governance:lexipol-boilerplate",
                (
                    "Lexipol California State Master boilerplate referenced — "
                    "verify vendor-specific provisions present"
                ),
                "medium",
                evidence=vendors["Lexipol"],
            )
        )

    # -----------------------------------------------------------------------
    # 4. Consent-calendar placement of surveillance item
    # -----------------------------------------------------------------------
    if has_surveillance_capability and detect_consent_calendar(text):
        findings.append(
            _build(
                "governance:consent-calendar-placement",
                (
                    "Surveillance technology placed on consent calendar — "
                    "bypasses individual council discussion"
                ),
                "medium",
                vendors=list(vendors.keys()),
            )
        )

    # -----------------------------------------------------------------------
    # 5. Sole-source procurement without Gov Code justification
    # -----------------------------------------------------------------------
    if detect_sole_source(text):
        has_gov_code_just = STATUTE_BY_KEY["gov_code_sole_source"].key in statutes
        if not has_gov_code_just:
            findings.append(
                _build(
                    "governance:sole-source-without-justification",
                    (
                        "Sole-source procurement referenced without California "
                        "Gov Code § 10340 justification citation"
                    ),
                    "high",
                    vendors=list(vendors.keys()),
                )
            )

    # -----------------------------------------------------------------------
    # 6. Auto-renewal clause — raises renewal-deadline risk
    # -----------------------------------------------------------------------
    if detect_auto_renewal(text):
        findings.append(
            _build(
                "governance:auto-renewal-clause",
                (
                    "Auto-renewal clause detected — contract renews without "
                    "affirmative council vote unless non-renewal notice served"
                ),
                "medium",
                vendors=list(vendors.keys()),
            )
        )

    # -----------------------------------------------------------------------
    # 7. Transparency-portal absence for deployed surveillance tech
    # -----------------------------------------------------------------------
    if has_surveillance_capability and not _has_any(
        text_lower, TRANSPARENCY_PORTAL_KEYWORDS
    ):
        findings.append(
            _build(
                "governance:transparency-portal-absence",
                (
                    "Surveillance capability referenced but no public "
                    "transparency-portal or inventory mentioned"
                ),
                "medium",
                technologies=list(techs.keys()),
            )
        )

    return findings
