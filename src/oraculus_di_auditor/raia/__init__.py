"""R.A.I.A. — Recursion Analysis Investigative Audit.

Cross-jurisdictional synthesis service for Oraculus-DI-Auditor. Reads
persisted ``Document``/``Analysis``/``Anomaly`` rows produced by the
Tier 1 webhook pipeline and aggregates them into a ``RAIAResult``
ready for DOCX rendering by n8n WF-010.

Public API::

    from oraculus_di_auditor.raia import RAIAService, RAIAResult

    svc = RAIAService()
    result = svc.synthesize(["woodlake", "lindsay", "porterville"])
    md = render_markdown(result)
"""

from __future__ import annotations

from oraculus_di_auditor.raia.patterns import detect_patterns
from oraculus_di_auditor.raia.raia_service import RAIAService
from oraculus_di_auditor.raia.schemas import (
    AnomalyRow,
    CrossJurisdictionPattern,
    JurisdictionSummary,
    RAIAResult,
)
from oraculus_di_auditor.raia.synthesis_report import render_markdown, write_markdown

__all__ = [
    "RAIAService",
    "RAIAResult",
    "JurisdictionSummary",
    "CrossJurisdictionPattern",
    "AnomalyRow",
    "detect_patterns",
    "render_markdown",
    "write_markdown",
]
