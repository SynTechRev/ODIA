"""Analysis modules for Oraculus-DI-Auditor.

Provides cross-reference auditing and a multi-detector audit engine spanning
fiscal, constitutional, and surveillance layers.
"""

from .audit_engine import analyze_document
from .constitutional import detect_constitutional_anomalies
from .cross_reference import cross_reference_audit, detect_cross_jurisdiction_refs
from .fiscal import detect_fiscal_anomalies
from .pipeline import run_full_analysis
from .surveillance import detect_surveillance_anomalies

__all__ = [
    "analyze_document",
    "cross_reference_audit",
    "detect_cross_jurisdiction_refs",
    "detect_fiscal_anomalies",
    "detect_constitutional_anomalies",
    "detect_surveillance_anomalies",
    "run_full_analysis",
]
