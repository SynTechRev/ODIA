"""Day 7: Neurosymbolic Integration -- L-1 through L-10 as callable LangGraph tools.

Each detector is exposed as a @tool-decorated function for use with LangGraph ToolNode.
A DetectorRegistry holds singleton instances of all 10 detectors for batch use.
legal_scan_node runs all detectors on retrieved passages and adds legal_findings to state.

Tool calling pattern (B-7 checkpoint):
  Each tool accepts doc_context_json: str (JSON-encoded DocContext fields).
  Each tool returns findings_json: str (JSON array of anomaly dicts).
  DETECTOR_TOOLS list is the complete set for ToolNode registration.
  legal_scan_node(state, resolver=None) -> dict is the RAIA graph integration point.

Graph wiring (deferred to Day 9 after B-7 sign-off):
  builder.add_node("legal_scan", lambda s: legal_scan_node(s))
  builder.add_edge("cross_reference", "legal_scan")
  builder.add_edge("legal_scan", "deepen")
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date
from typing import Any

from langchain_core.tools import tool

from oraculus_di_auditor.legal.detectors._base import DocContext, LegalFinding
from oraculus_di_auditor.legal.detectors.l1_statutory_applicability import (
    L1StatutoryApplicability,
)
from oraculus_di_auditor.legal.detectors.l2_procedural_compliance import (
    L2ProceduralCompliance,
)
from oraculus_di_auditor.legal.detectors.l3_exemption_misapplication import (
    L3ExemptionMisapplication,
)
from oraculus_di_auditor.legal.detectors.l4_ministerial_duty import L4MinisterialDuty
from oraculus_di_auditor.legal.detectors.l5_federal_grant_compliance import (
    L5FederalGrantCompliance,
)
from oraculus_di_auditor.legal.detectors.l6_constitutional_implication import (
    L6ConstitutionalImplication,
)
from oraculus_di_auditor.legal.detectors.l7_regulatory_authority import (
    L7RegulatoryAuthority,
)
from oraculus_di_auditor.legal.detectors.l8_case_law_currency import L8CaseLawCurrency
from oraculus_di_auditor.legal.detectors.l9_statute_citation_auditor import (
    L9StatuteCitationAuditor,
)
from oraculus_di_auditor.legal.detectors.l10_balancing_test import L10BalancingTest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Null resolver sentinel
# ---------------------------------------------------------------------------


class _NullResolver:
    """Sentinel passed when no LegalResolver is available.

    Detectors must not call resolver methods on the hot path -- they receive
    this sentinel and fall back to static analysis only. Satisfies the resolver
    parameter without requiring legal corpus initialization at tool-call time.
    """


_NULL_RESOLVER = _NullResolver()


# ---------------------------------------------------------------------------
# DocContext helpers
# ---------------------------------------------------------------------------


def _derive_hash(document_id: str) -> str:
    return hashlib.sha256(document_id.encode()).hexdigest()


def build_doc_context_from_passage(passage: dict, text: str = "") -> DocContext:
    """Convert a RAIA retriever passage dict to a DocContext for detector input.

    Passages from HybridRetriever carry document_id and metadata; text may be
    a separate field or embedded. Falls back to empty strings for missing fields
    so detectors can still run (L-1 Tier 1 always fires on any passage).
    """
    document_id = str(passage.get("document_id", ""))
    document_hash = str(passage.get("document_hash", "") or _derive_hash(document_id))

    raw_date = passage.get("version_date") or passage.get("date")
    version_date: date | None = None
    if isinstance(raw_date, date):
        version_date = raw_date
    elif isinstance(raw_date, str) and raw_date:
        try:
            version_date = date.fromisoformat(raw_date[:10])
        except ValueError:
            pass

    doc_text = text or str(passage.get("text", "") or "")
    if not doc_text:
        findings_list = passage.get("findings", [])
        doc_text = " ".join(
            str(f.get("issue", "")) for f in findings_list if f.get("issue")
        )

    return DocContext(
        document_id=document_id,
        document_hash=document_hash,
        document_type=str(passage.get("document_type", "") or ""),
        jurisdiction=str(passage.get("jurisdiction", "") or ""),
        authority=passage.get("authority") or passage.get("issuer"),
        version_date=version_date,
        text=doc_text,
        source_finding=passage.get("source_finding"),
    )


def _parse_doc_context_json(doc_context_json: str) -> DocContext:
    """Deserialize a JSON string into a DocContext for @tool wrappers."""
    data: dict[str, Any] = json.loads(doc_context_json)

    raw_date = data.get("version_date")
    version_date: date | None = None
    if isinstance(raw_date, str) and raw_date:
        try:
            version_date = date.fromisoformat(raw_date[:10])
        except ValueError:
            pass

    document_id = str(data.get("document_id", ""))
    document_hash = str(data.get("document_hash", "") or _derive_hash(document_id))

    return DocContext(
        document_id=document_id,
        document_hash=document_hash,
        document_type=str(data.get("document_type", "") or ""),
        jurisdiction=str(data.get("jurisdiction", "") or ""),
        authority=data.get("authority"),
        version_date=version_date,
        text=str(data.get("text", "") or ""),
        source_finding=data.get("source_finding"),
    )


def _safe_run(detector_cls: type, doc_context_json: str) -> str:
    """Shared error boundary for @tool wrappers."""
    try:
        ctx = _parse_doc_context_json(doc_context_json)
        findings: list[LegalFinding] = detector_cls().detect(ctx, _NULL_RESOLVER)
        return json.dumps([f.to_anomaly_dict() for f in findings])
    except Exception:
        logger.exception("%s tool call failed", detector_cls.__name__)
        return json.dumps([])


# ---------------------------------------------------------------------------
# @tool wrappers -- L-1 through L-10
# ---------------------------------------------------------------------------

_TOOL_DESCRIPTION_SUFFIX = (
    " Input: doc_context_json is a JSON string with keys: "
    "document_id (str), document_hash (str), document_type (str), "
    "jurisdiction (str), text (str); optional: authority (str), "
    "version_date (YYYY-MM-DD str), source_finding (dict). "
    "Returns: JSON array of anomaly dicts with keys id, issue, severity, layer, details."
)


@tool(
    description=(
        "Run L-1 Statutory Applicability: identify which California and federal statutes apply. "
        "Applies Tier 1 (CPRA baseline), Tier 2 (document-type triggers: Brown Act, CPRA response, "
        "JAG/COPS grants, contracts), and Tier 3 (content signals: surveillance, ALPR, body camera, "
        "AI/ADMT, arbitration)." + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l1_statutory_applicability(doc_context_json: str) -> str:
    return _safe_run(L1StatutoryApplicability, doc_context_json)


@tool(
    description=(
        "Run L-2 Procedural Compliance: detect Brown Act and CPRA procedural defects. "
        "Checks agenda posting timelines, closed session notice requirements, public comment "
        "procedures, and CPRA 10/14-day response window compliance."
        + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l2_procedural_compliance(doc_context_json: str) -> str:
    return _safe_run(L2ProceduralCompliance, doc_context_json)


@tool(
    description=(
        "Run L-3 Exemption Misapplication: flag improperly invoked CPRA exemptions. "
        "Detects blanket exemption claims, missing exemption specificity, failure to segregate "
        "exempt from non-exempt records, and burden-shifting errors under Cal. Gov. 7923.000."
        + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l3_exemption_misapplication(doc_context_json: str) -> str:
    return _safe_run(L3ExemptionMisapplication, doc_context_json)


@tool(
    description=(
        "Run L-4 Ministerial Duty: identify non-discretionary obligations violated or unmet. "
        "Flags ministerial acts treated as discretionary, including mandatory agenda posting, "
        "mandatory response windows, and mandatory disclosure obligations where no balancing "
        "test applies." + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l4_ministerial_duty(doc_context_json: str) -> str:
    return _safe_run(L4MinisterialDuty, doc_context_json)


@tool(
    description=(
        "Run L-5 Federal Grant Compliance: check JAG/COPS/2 CFR 200 grant conditions. "
        "Detects missing use-of-force policy attachments, absent civil rights assurances, "
        "improper equipment re-transfer, and 2 CFR Part 200 Uniform Guidance documentation "
        "gaps in grant agreements and amendments." + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l5_federal_grant_compliance(doc_context_json: str) -> str:
    return _safe_run(L5FederalGrantCompliance, doc_context_json)


@tool(
    description=(
        "Run L-6 Constitutional Implication: surface Fourth, Fifth, and Fourteenth Amendment signals. "
        "Flags warrantless surveillance authorizations, due process gaps in disciplinary procedures, "
        "equal protection anomalies in enforcement patterns, and First Amendment retaliation risk signals."
        + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l6_constitutional_implication(doc_context_json: str) -> str:
    return _safe_run(L6ConstitutionalImplication, doc_context_json)


@tool(
    description=(
        "Run L-7 Regulatory Authority: check whether an agency acted within its statutory grant. "
        "Detects ultra vires directives, unenacted policy references, delegation without authority, "
        "and exercises of power not conferred by the agency organic statute or charter."
        + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l7_regulatory_authority(doc_context_json: str) -> str:
    return _safe_run(L7RegulatoryAuthority, doc_context_json)


@tool(
    description=(
        "Run L-8 Case Law Currency: detect stale or superseded legal authority citations. "
        "Flags citations to overruled, depublished, or superseded decisions and statutes. "
        "Checks AB 481 / SB 34 / PC 13663 effective dates against document version_date "
        "to detect pre-amendment reliance on repealed text." + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l8_case_law_currency(doc_context_json: str) -> str:
    return _safe_run(L8CaseLawCurrency, doc_context_json)


@tool(
    description=(
        "Run L-9 Statute Citation Auditor: validate statute citation format and existence. "
        "Checks canonical California and federal citation format, that section numbers are "
        "within known ranges, and that referenced amendments or subdivisions exist. "
        "Flags malformed, truncated, or invented citation strings."
        + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l9_statute_citation_auditor(doc_context_json: str) -> str:
    return _safe_run(L9StatuteCitationAuditor, doc_context_json)


@tool(
    description=(
        "Run L-10 Balancing Test Analyzer: apply Mathews v. Eldridge and CPRA public interest tests. "
        "Evaluates whether the agency correctly applied the three-factor Mathews balancing test for "
        "due process and the CPRA public interest / privacy balancing framework. Flags conclusions "
        "that skip required factors or misweight competing interests. Supports compilation_mode for "
        "multi-document synthesis (Carpenter v. United States framework)."
        + _TOOL_DESCRIPTION_SUFFIX
    )
)
def run_l10_balancing_test(doc_context_json: str) -> str:
    return _safe_run(L10BalancingTest, doc_context_json)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

DETECTOR_TOOLS = [
    run_l1_statutory_applicability,
    run_l2_procedural_compliance,
    run_l3_exemption_misapplication,
    run_l4_ministerial_duty,
    run_l5_federal_grant_compliance,
    run_l6_constitutional_implication,
    run_l7_regulatory_authority,
    run_l8_case_law_currency,
    run_l9_statute_citation_auditor,
    run_l10_balancing_test,
]


# ---------------------------------------------------------------------------
# Batch runner (used by legal_scan_node)
# ---------------------------------------------------------------------------


class DetectorRegistry:
    """Holds singleton instances of all L-1 through L-10 detectors for batch runs."""

    def __init__(self) -> None:
        self._detectors = [
            L1StatutoryApplicability(),
            L2ProceduralCompliance(),
            L3ExemptionMisapplication(),
            L4MinisterialDuty(),
            L5FederalGrantCompliance(),
            L6ConstitutionalImplication(),
            L7RegulatoryAuthority(),
            L8CaseLawCurrency(),
            L9StatuteCitationAuditor(),
            L10BalancingTest(),
        ]

    def run_all(self, ctx: DocContext, resolver: Any = None) -> list[LegalFinding]:
        r = resolver if resolver is not None else _NULL_RESOLVER
        findings: list[LegalFinding] = []
        for detector in self._detectors:
            try:
                findings.extend(detector.detect(ctx, r))
            except Exception:
                logger.exception(
                    "Detector %s failed on document %s",
                    getattr(detector, "detector_id", type(detector).__name__),
                    ctx.document_id,
                )
        return findings


_REGISTRY = DetectorRegistry()


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------


def legal_scan_node(state: dict, resolver: Any = None) -> dict:
    """LangGraph node: run all L-1 through L-10 detectors on retrieved passages.

    Reads state["retrieved_passages"] (list of passage dicts populated by
    cross_reference_node). Writes state["legal_findings"] (list of anomaly dicts
    from all detectors across all passages).

    Compatible with RAIAState and any superset TypedDict. Adds legal_findings
    without modifying any existing key. Never raises; logs per-document failures.

    Graph wiring (Day 9, after B-7 sign-off):
        builder.add_node("legal_scan", lambda s: legal_scan_node(s))
        builder.add_edge("cross_reference", "legal_scan")
        builder.add_edge("legal_scan", "deepen")

    State contract:
        Input: state["retrieved_passages"] -> list[dict]
        Output: state + {"legal_findings": list[dict]}
        Each legal_finding dict: {"id", "issue", "severity", "layer", "details"}
    """
    passages: list[dict] = state.get("retrieved_passages", [])
    r = resolver if resolver is not None else _NULL_RESOLVER
    all_findings: list[dict] = []

    for passage in passages:
        if not passage.get("document_id"):
            continue
        ctx = build_doc_context_from_passage(passage)
        findings = _REGISTRY.run_all(ctx, r)
        all_findings.extend(f.to_anomaly_dict() for f in findings)

    state_out = dict(state)
    state_out["legal_findings"] = all_findings
    state_out.setdefault("trace", []).append(
        {
            "node": "legal_scan",
            "passages_scanned": len(passages),
            "findings_produced": len(all_findings),
        }
    )
    return state_out
