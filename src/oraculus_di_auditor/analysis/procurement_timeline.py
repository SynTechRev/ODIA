"""Procurement Timeline Detector.

Two-mode detector:

  1. Single-document mode (doc: dict) — invoked by audit_engine.  Looks for
     procurement-irregularity signals within one document's text: consent
     calendar placement of a vendor contract, sole-source language without
     statutory justification, auto-renewal clauses, and execution dates that
     precede the same document's authorization date (when both are present
     as fields).

  2. Multi-document mode (documents: list[dict]) — invoked by workflows that
     compare execution_date to authorization_date across a corpus (legacy
     behaviour, preserved for backwards compatibility with existing tests).

The single-document shape is what the packaged desktop app's audit_engine
actually calls.  The prior implementation only handled the multi-document
shape and silently returned [] for every call from audit_engine — the root
cause of zero procurement findings in desktop audits.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .text_utils import extract_text_content
from .vendor_database import (
    STATUTE_BY_KEY,
    detect_auto_renewal,
    detect_consent_calendar,
    detect_sole_source,
    detect_statutes,
    detect_vendors,
)


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def _build(
    finding_id: str, issue: str, severity: str, **details: Any
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "issue": issue,
        "severity": severity,
        "layer": "procurement",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Single-document analysis
# ---------------------------------------------------------------------------


def _analyze_single_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    # Structural date check (if fields are present)
    exec_date = _parse_date(doc.get("execution_date"))
    auth_date = _parse_date(doc.get("authorization_date"))
    if exec_date and auth_date and exec_date < auth_date:
        findings.append(
            _build(
                "procurement:execution-precedes-authorization",
                f"Contract executed {(auth_date - exec_date).days} day(s) "
                "before council authorization",
                "high",
                document_id=doc.get("document_id"),
                title=doc.get("title"),
                execution_date=doc.get("execution_date"),
                authorization_date=doc.get("authorization_date"),
                days_early=(auth_date - exec_date).days,
            )
        )

    # Text-based signals
    text = extract_text_content(doc) or ""
    if not text.strip():
        return findings

    vendors = detect_vendors(text)
    statutes = detect_statutes(text)

    # Consent calendar + named vendor
    if vendors and detect_consent_calendar(text):
        findings.append(
            _build(
                "procurement:consent-calendar-placement",
                (
                    "Vendor contract placed on consent calendar — bypasses "
                    "public discussion of surveillance technology"
                ),
                "medium",
                vendors=list(vendors.keys()),
            )
        )

    # Sole-source language without Gov Code § 10340 justification
    if detect_sole_source(text):
        has_gov_code = STATUTE_BY_KEY["gov_code_sole_source"].key in statutes
        if not has_gov_code:
            findings.append(
                _build(
                    "procurement:sole-source-without-gov-code-citation",
                    (
                        "Sole-source procurement referenced without California "
                        "Gov Code § 10340 / § 10300–10334 justification"
                    ),
                    "high",
                    vendors=list(vendors.keys()),
                )
            )

    # Auto-renewal clause
    if detect_auto_renewal(text):
        findings.append(
            _build(
                "procurement:auto-renewal-clause",
                (
                    "Contract contains auto-renewal clause — renewal obligation "
                    "attaches without affirmative council vote"
                ),
                "medium",
                vendors=list(vendors.keys()),
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Multi-document analysis (legacy)
# ---------------------------------------------------------------------------


def _analyze_corpus(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for idx, d in enumerate(documents):
        if not isinstance(d, dict):
            continue
        exec_d = _parse_date(d.get("execution_date"))
        auth_d = _parse_date(d.get("authorization_date"))
        if exec_d is None or auth_d is None:
            continue
        if exec_d < auth_d:
            findings.append(
                _build(
                    "procurement:execution-precedes-authorization",
                    f"Contract executed {(auth_d - exec_d).days} day(s) "
                    "before council authorization",
                    "high",
                    document_id=d.get("document_id") or d.get("id") or f"doc[{idx}]",
                    title=d.get("title", ""),
                    execution_date=d.get("execution_date"),
                    authorization_date=d.get("authorization_date"),
                    days_early=(auth_d - exec_d).days,
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Public entry point — dual-mode dispatcher
# ---------------------------------------------------------------------------


def detect_procurement_timeline_anomalies(
    arg: dict[str, Any] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Dispatch on argument shape — single doc (dict) or corpus (list)."""
    if isinstance(arg, dict):
        return _analyze_single_doc(arg)
    if isinstance(arg, list):
        return _analyze_corpus(arg)
    return []
