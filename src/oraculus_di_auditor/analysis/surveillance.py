"""Surveillance Outsourcing Detector.

Detects surveillance-technology deployment patterns using the ODIA vendor
signature database.  Unlike the previous placeholder implementation, this
detector is calibrated against the Master Audit Synthesis methodology used
to produce the VPD / PPD / Tulare / Lindsay / Farmersville / Woodlake /
Exeter / Dinuba audits, where 7+ surveillance layers (Flock ALPR, Axon BWC,
Spartan Camera, interview-room cameras, TASER, etc.) are routinely
documented in municipal records without governance artefacts.

Findings emitted (severity in parens):

  surveillance:vendor-detected                         (info/low)
    One-per-vendor finding listing every surveillance vendor that appears
    in the document, with evidence snippets.  Establishes the vendor
    footprint that downstream findings build on.

  surveillance:alpr-without-sb524-policy               (critical when post-2026)
    ALPR vendor present (Flock, generic ALPR, vehicle fingerprint) but no
    SB 524 policy citation in the document.  SB 524 became effective
    2026-01-01 and requires a written AI-transparency policy before ALPR
    use.

  surveillance:bwc-without-cjis-addendum               (high)
    Body-worn camera vendor (Axon, Motorola WatchGuard) referenced without
    a CJIS Security Addendum reference.  CJIS compliance is required for
    criminal-justice data storage.

  surveillance:ai-report-writing-without-policy        (critical)
    Axon Draft One or equivalent AI report-writing tool referenced with
    neither SB 524 nor any policy/oversight language.

  surveillance:drone-without-ab481-report              (high)
    Drone / UAS program referenced without AB 481 military equipment
    annual-report language.  AB 481 requires annual reporting to the
    governing body.

  surveillance:multilayer-architecture                 (high)
    Three or more distinct surveillance technology categories referenced
    in the same document (e.g. ALPR + BWC + drone, or BWC + interview
    room + AI report writing).  Signals an integrated surveillance
    architecture that warrants CCOPS-style oversight.

  surveillance:alpr-privacy-act-gap                    (high)
    ALPR deployment referenced without Civil Code § 1798.90.5 (ALPR
    Privacy Act) usage-and-privacy-policy citation.

Every finding includes a ``details`` payload with the matched excerpts so
the ODIA analyst can audit the detector's reasoning.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .text_utils import extract_text_content
from .vendor_database import (
    STATUTE_BY_KEY,
    VENDOR_BY_NAME,
    detect_statutes,
    detect_technologies,
    detect_vendors,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _document_date(doc: dict[str, Any]) -> date | None:
    """Best-effort extraction of a reference date from the document."""
    for key in ("document_date", "date", "effective_date", "meeting_date"):
        v = doc.get(key)
        if isinstance(v, str):
            try:
                return date.fromisoformat(v[:10])
            except ValueError:
                continue
        if isinstance(v, date):
            return v
    return None


def _build_finding(
    finding_id: str,
    issue: str,
    severity: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "issue": issue,
        "severity": severity,
        "layer": "surveillance",
        "details": details,
    }


def _check_alpr_gaps(
    techs: dict[str, list[str]],
    vendors: dict[str, list[str]],
    statutes: set[str],
    doc_date: date | None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    has_alpr = "alpr" in techs or any(
        VENDOR_BY_NAME[v].category == "alpr" for v in vendors
    )
    if not has_alpr:
        return findings
    sb524 = STATUTE_BY_KEY["sb_524"]
    if sb524.key not in statutes:
        sb524_effective = date.fromisoformat(sb524.effective_date)
        severity = (
            "critical" if (doc_date is None or doc_date >= sb524_effective) else "high"
        )
        findings.append(
            _build_finding(
                "surveillance:alpr-without-sb524-policy",
                "ALPR system referenced without SB 524 AI-transparency policy citation",
                severity,
                statute=sb524.citation,
                effective_date=sb524.effective_date,
                document_date=doc_date.isoformat() if doc_date else None,
                alpr_evidence=list(techs.get("alpr", []))[:3],
            )
        )
    alpr_priv = STATUTE_BY_KEY["alpr_privacy"]
    if alpr_priv.key not in statutes:
        findings.append(
            _build_finding(
                "surveillance:alpr-privacy-act-gap",
                (
                    "ALPR deployment without Civil Code § 1798.90.5 "
                    "usage-and-privacy policy citation"
                ),
                "high",
                statute=alpr_priv.citation,
            )
        )
    return findings


def _check_bwc_drone_ai_gaps(
    techs: dict[str, list[str]],
    vendors: dict[str, list[str]],
    statutes: set[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    cjis = STATUTE_BY_KEY["cjis"]
    has_bwc = "bwc" in techs or any(
        VENDOR_BY_NAME[v].category == "bwc" for v in vendors
    )
    if has_bwc and cjis.key not in statutes:
        findings.append(
            _build_finding(
                "surveillance:bwc-without-cjis-addendum",
                "Body-worn camera program without CJIS Security Policy reference",
                "high",
                statute=cjis.citation,
                bwc_evidence=list(techs.get("bwc", []))[:3],
            )
        )
    sb524 = STATUTE_BY_KEY["sb_524"]
    if "ai_report_writing" in techs and sb524.key not in statutes:
        findings.append(
            _build_finding(
                "surveillance:ai-report-writing-without-policy",
                (
                    "AI-generated report writing (Draft One or equivalent) "
                    "without SB 524 AI-transparency policy"
                ),
                "critical",
                statute=sb524.citation,
                ai_evidence=techs["ai_report_writing"][:3],
            )
        )
    ab481 = STATUTE_BY_KEY["ab_481"]
    if "drone_uas" in techs and ab481.key not in statutes:
        findings.append(
            _build_finding(
                "surveillance:drone-without-ab481-report",
                "Drone/UAS program referenced without AB 481 annual-report language",
                "high",
                statute=ab481.citation,
                drone_evidence=techs["drone_uas"][:3],
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def detect_surveillance_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the full ODIA surveillance detector rule-set against a document."""
    findings: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return findings

    text = extract_text_content(doc) or ""
    if not text.strip():
        return findings

    vendors = detect_vendors(text)
    techs = detect_technologies(text)
    statutes = detect_statutes(text)
    doc_date = _document_date(doc)

    # -----------------------------------------------------------------------
    # 1. One low/info finding per vendor detected — establishes footprint
    # -----------------------------------------------------------------------
    for vendor_name, evidence in vendors.items():
        sig = VENDOR_BY_NAME[vendor_name]
        findings.append(
            _build_finding(
                f"surveillance:vendor-detected:{vendor_name.lower().replace(' ', '-')}",
                f"Surveillance vendor '{vendor_name}' ({sig.category}) referenced",
                "low",
                vendor=vendor_name,
                category=sig.category,
                evidence=evidence,
            )
        )

    # -----------------------------------------------------------------------
    # 2–3. ALPR statutory gaps (SB 524 + ALPR Privacy Act)
    # -----------------------------------------------------------------------
    findings.extend(_check_alpr_gaps(techs, vendors, statutes, doc_date))

    # -----------------------------------------------------------------------
    # 4–6. BWC / AI report-writing / drone gaps
    # -----------------------------------------------------------------------
    findings.extend(_check_bwc_drone_ai_gaps(techs, vendors, statutes))

    # -----------------------------------------------------------------------
    # 7. Multi-layer surveillance architecture (≥3 categories)
    # -----------------------------------------------------------------------
    layer_categories = set(techs.keys())
    # Add vendor-derived categories (alpr/bwc) in case the generic tech
    # matcher missed them but a specific vendor was named
    for vendor_name in vendors:
        cat = VENDOR_BY_NAME[vendor_name].category
        if cat in {"alpr", "bwc"}:
            layer_categories.add(cat)
    if len(layer_categories) >= 3:
        findings.append(
            _build_finding(
                "surveillance:multilayer-architecture",
                (
                    f"Multi-layer surveillance architecture detected "
                    f"({len(layer_categories)} categories)"
                ),
                "high",
                layer_count=len(layer_categories),
                layers=sorted(layer_categories),
            )
        )

    # -----------------------------------------------------------------------
    # 8. Facial recognition — always-critical regardless of governance
    #    (California AB 1215 bans law-enforcement biometric use on BWCs)
    # -----------------------------------------------------------------------
    if "facial_recognition" in techs:
        findings.append(
            _build_finding(
                "surveillance:facial-recognition-reference",
                "Facial recognition referenced — AB 1215 restrictions apply",
                "critical",
                evidence=techs["facial_recognition"][:3],
            )
        )

    return findings
