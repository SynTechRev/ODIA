"""Grant Compliance Detector.

Flags federal-grant documents (JAG / Edward Byrne, COPS hiring, ARPA) that
reference equipment purchases or sworn-officer hiring without the
corresponding compliance artefacts the grant programs require:

  * JAG anti-supplanting certification   (grant-funded positions must not
                                         replace locally-funded positions)
  * COPS cost-itemisation                (technology must be itemised
                                         separately from personnel)
  * 28 CFR Part 23                       (criminal intelligence system rules)

This detector runs on single documents and emits findings when grant
references appear without the corresponding compliance language.
"""

from __future__ import annotations

from typing import Any

from .text_utils import extract_text_content
from .vendor_database import STATUTE_BY_KEY, detect_statutes, detect_vendors


def _build(
    finding_id: str, issue: str, severity: str, **details: Any
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "issue": issue,
        "severity": severity,
        "layer": "grant_compliance",
        "details": details,
    }


def detect_grant_compliance_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return findings

    text = extract_text_content(doc) or ""
    if not text.strip():
        return findings

    statutes = detect_statutes(text)
    has_jag = STATUTE_BY_KEY["jag"].key in statutes
    has_cops = STATUTE_BY_KEY["cops"].key in statutes
    has_antisupplanting = STATUTE_BY_KEY["anti_supplanting"].key in statutes
    has_28cfr23 = STATUTE_BY_KEY["28_cfr_23"].key in statutes

    vendors = detect_vendors(text)

    # -----------------------------------------------------------------------
    # 1. JAG without anti-supplanting certification
    # -----------------------------------------------------------------------
    if has_jag and not has_antisupplanting:
        findings.append(
            _build(
                "grant:jag-without-anti-supplanting",
                (
                    "JAG/Edward Byrne grant referenced without anti-supplanting "
                    "certification — 34 U.S.C. § 10152 requires certification "
                    "that grant funds do not supplant local appropriations"
                ),
                "critical",
                statute="34 U.S.C. § 10152(a)(1)(G)",
            )
        )

    # -----------------------------------------------------------------------
    # 2. JAG + surveillance vendor in the same document (flag for review)
    # -----------------------------------------------------------------------
    if has_jag and vendors:
        findings.append(
            _build(
                "grant:jag-funded-surveillance",
                (
                    "JAG grant referenced alongside surveillance vendor — "
                    "JAG-funded technology purchases must be itemised and "
                    "reported to BJA"
                ),
                "high",
                vendors=list(vendors.keys()),
            )
        )

    # -----------------------------------------------------------------------
    # 3. COPS grant without cost itemisation indicator
    # -----------------------------------------------------------------------
    cops_itemisation_markers = (
        "itemised",
        "itemized",
        "line item",
        "line-item",
        "equipment cost",
        "technology cost",
    )
    text_lower = text.lower()
    if has_cops and not any(m in text_lower for m in cops_itemisation_markers):
        findings.append(
            _build(
                "grant:cops-without-itemisation",
                (
                    "COPS grant referenced without technology cost itemisation — "
                    "hiring and technology expenditures must be separated"
                ),
                "medium",
            )
        )

    # -----------------------------------------------------------------------
    # 4. Criminal-intelligence references without 28 CFR Part 23
    # -----------------------------------------------------------------------
    crim_intel_markers = (
        "criminal intelligence",
        "intelligence database",
        "intelligence file",
        "gang database",
        "gang intelligence",
    )
    if any(m in text_lower for m in crim_intel_markers) and not has_28cfr23:
        findings.append(
            _build(
                "grant:crim-intel-without-28-cfr-23",
                (
                    "Criminal-intelligence reference without 28 CFR Part 23 "
                    "compliance citation"
                ),
                "high",
                statute="28 CFR Part 23",
            )
        )

    return findings
