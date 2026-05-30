"""Analysis modules for Oraculus-DI-Auditor.

Provides cross-reference auditing and a multi-detector audit engine spanning
fiscal, constitutional, and surveillance layers.
"""

from .administrative_integrity import (
    detect_administrative_anomalies,
    find_blank_required_fields,
)
from .audit_engine import analyze_document
from .constitutional import detect_constitutional_anomalies
from .cross_entity import detect_cross_entity_anomalies
from .cross_reference import cross_reference_audit, detect_cross_jurisdiction_refs
from .fiscal import detect_fiscal_anomalies
from .governance_gap import detect_governance_gap_anomalies
from .pipeline import run_full_analysis
from .grant_funding_trails import detect_grant_funding_trail_anomalies
from .procurement_timeline import detect_procurement_timeline_anomalies
from .scope_expansion import detect_scope_expansion_anomalies
from .signature_chain import detect_signature_anomalies
from .surveillance import detect_surveillance_anomalies
from .vote_date_alignment import detect_vote_date_alignment_anomalies

__all__ = [
    "analyze_document",
    "cross_reference_audit",
    "detect_administrative_anomalies",
    "detect_constitutional_anomalies",
    "detect_cross_entity_anomalies",
    "detect_cross_jurisdiction_refs",
    "detect_fiscal_anomalies",
    "detect_governance_gap_anomalies",
    "detect_grant_funding_trail_anomalies",
    "detect_procurement_timeline_anomalies",
    "detect_scope_expansion_anomalies",
    "detect_signature_anomalies",
    "detect_surveillance_anomalies",
    "detect_vote_date_alignment_anomalies",
    "find_blank_required_fields",
    "run_full_analysis",
]
