"""R.A.I.A. (Recursion Analysis Investigative Audit) synthesis service.

The single highest-leverage addition in the v2.7.1 enhancement plan:
aggregates persisted ``Document``/``Analysis``/``Anomaly`` rows across
the requested jurisdictions and produces a ``RAIAResult`` suitable for
DOCX rendering by WF-010.

The service is deliberately DB-centric (reads already-persisted rows)
rather than re-running the detectors. Two reasons:

  1. Webhook ingests happen continuously over days/weeks; re-running
     detectors at synthesis time would re-pay the cost and might hit
     different results if a detector was updated mid-cycle. Reading
     the persisted findings gives "what was true at analysis time".
  2. The webhook path (see ``interface/routes/webhook.py::
     _persist_tier1_result``) is already writing every Tier 1 run to
     the DB. Synthesis just joins on ``Document.jurisdiction``.

Tier 3 scaffolding (``include_tier3=True``) currently records a stub
note pointing at the experimental engines (rec17/rgk18/aei19/aer20);
full wire-up is deferred until those engines expose a stable
synthesize() surface.
"""

from __future__ import annotations

import json
import logging
import secrets
from collections import Counter
from typing import TYPE_CHECKING, Any

from oraculus_di_auditor.raia.patterns import detect_patterns
from oraculus_di_auditor.raia.schemas import (
    AnomalyRow,
    JurisdictionSummary,
    RAIAResult,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Anomaly sort key: severity rank descending, then layer alpha for
# deterministic output. Unknown severities go to the bottom.
_SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _severity_weight(severity: str) -> int:
    return _SEVERITY_RANK.get((severity or "").lower(), 0)


def _decode_details(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        decoded = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


class RAIAService:
    """Recursion Analysis Investigative Audit synthesis service.

    Usage::

        svc = RAIAService()
        result = svc.synthesize(
            jurisdictions=["woodlake", "lindsay", "porterville"],
            include_tier3=False,
        )
        result.to_dict()  # ready to persist or pass to the template
    """

    def __init__(
        self,
        *,
        top_anomalies_per_jurisdiction: int = 10,
    ) -> None:
        """``top_anomalies_per_jurisdiction`` caps how many anomaly rows
        the service loads per jurisdiction for the summary. The cap
        only affects the ``top_anomalies`` field on ``JurisdictionSummary``
        (highest severity first); total counts, averages, and pattern
        detection always see the full anomaly set.
        """
        self.top_n = top_anomalies_per_jurisdiction

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(
        self,
        jurisdictions: list[str],
        *,
        include_tier3: bool = False,
    ) -> RAIAResult:
        """Build a ``RAIAResult`` for the requested jurisdictions.

        Empty ``jurisdictions`` raises ``ValueError`` — callers must
        always provide an explicit list. Unknown jurisdictions don't
        raise; they appear in ``missing_jurisdictions`` on the result.
        """
        if not jurisdictions:
            raise ValueError("jurisdictions must be a non-empty list")

        summaries, missing = self._load_jurisdictions(jurisdictions)
        patterns = detect_patterns(summaries)

        tier3_notes: dict[str, Any] | None = None
        if include_tier3:
            tier3_notes = self._tier3_stub(summaries, patterns)

        return RAIAResult(
            synthesis_id=secrets.token_hex(8),
            generated_at=RAIAResult._now_iso(),
            jurisdictions=summaries,
            patterns=patterns,
            include_tier3=include_tier3,
            tier3_notes=tier3_notes,
            missing_jurisdictions=missing,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load_jurisdictions(
        self,
        jurisdictions: list[str],
    ) -> tuple[list[JurisdictionSummary], list[str]]:
        """Load rows for each jurisdiction. Returns (summaries, missing).

        The DB layer might not be installed or initialised — in either
        case the service degrades gracefully: every requested
        jurisdiction lands in ``missing`` and we return empty summaries.
        """
        try:
            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError:
            logger.warning(
                "RAIAService: DB layer not available — returning empty synthesis."
            )
            return [], list(jurisdictions)

        summaries: list[JurisdictionSummary] = []
        missing: list[str] = []
        try:
            with get_db() as session:
                for jid in jurisdictions:
                    summary = self._build_summary(session, db_models, jid)
                    if summary.document_count == 0:
                        missing.append(jid)
                    summaries.append(summary)
        except Exception:
            logger.exception(
                "RAIAService: DB query failed — returning empty summaries."
            )
            return [
                JurisdictionSummary(jurisdiction_id=j) for j in jurisdictions
            ], list(jurisdictions)

        return summaries, missing

    def _build_summary(
        self,
        session: Session,
        db_models: Any,
        jurisdiction_id: str,
    ) -> JurisdictionSummary:
        """Query Document → Analysis → Anomaly for one jurisdiction."""
        # PascalCase to mirror the SQLAlchemy class names they alias —
        # keeps the query call sites readable (Document.document_id,
        # Analysis.document_id, etc.).
        Document = db_models.Document  # noqa: N806
        Analysis = db_models.Analysis  # noqa: N806
        Anomaly = db_models.Anomaly  # noqa: N806

        doc_ids = [
            row[0]
            for row in session.query(Document.document_id)
            .filter(Document.jurisdiction == jurisdiction_id)
            .all()
        ]
        if not doc_ids:
            return JurisdictionSummary(jurisdiction_id=jurisdiction_id)

        analyses = (
            session.query(Analysis).filter(Analysis.document_id.in_(doc_ids)).all()
        )
        if not analyses:
            return JurisdictionSummary(
                jurisdiction_id=jurisdiction_id,
                document_count=len(doc_ids),
            )

        analysis_ids = [a.id for a in analyses]
        anomalies_rows = (
            session.query(Anomaly).filter(Anomaly.analysis_id.in_(analysis_ids)).all()
        )

        # Flatten anomalies to the dataclass shape so downstream code
        # doesn't touch SQLAlchemy.
        flat: list[AnomalyRow] = [
            AnomalyRow(
                anomaly_id=a.anomaly_id,
                issue=a.issue or "",
                severity=a.severity or "medium",
                layer=a.layer or "unknown",
                details=_decode_details(a.details_json),
            )
            for a in anomalies_rows
        ]

        severity_counts = Counter((a.severity or "unknown").lower() for a in flat)
        layer_counts = Counter((a.layer or "unknown").lower() for a in flat)

        scores = [float(a.scalar_score) for a in analyses if a.scalar_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Sort anomalies by severity desc, then layer alpha for deterministic
        # ordering even when severities tie.
        sorted_flat = sorted(
            flat,
            key=lambda a: (-_severity_weight(a.severity), a.layer, a.anomaly_id),
        )
        top = sorted_flat[: self.top_n]

        return JurisdictionSummary(
            jurisdiction_id=jurisdiction_id,
            document_count=len(doc_ids),
            analysis_count=len(analyses),
            total_anomalies=len(flat),
            scalar_score_avg=avg_score,
            severity_counts=dict(severity_counts),
            layer_counts=dict(layer_counts),
            top_anomalies=top,
        )

    def _tier3_stub(
        self,
        summaries: list[JurisdictionSummary],
        patterns: list[Any],
    ) -> dict[str, Any]:
        """Placeholder for Tier 3 engine integration.

        Full wire-up routes through ``rec17.ethical_cognition`` and
        ``aer20.composite_feature_vector`` once those engines expose a
        stable ``synthesize`` surface. For now, we emit a structured
        note so the report renderer and WF-010 can distinguish a
        Tier-3-requested-but-stubbed synthesis from a plain Tier-1-only
        one.
        """
        return {
            "status": "stub",
            "note": (
                "Tier 3 recursive synthesis is scaffolding-only in v2.7.1; "
                "this record marks the synthesis as Tier-3-requested so "
                "downstream renderers can flag it for review."
            ),
            "jurisdiction_count": len(summaries),
            "pattern_count": len(patterns),
            "engines_planned": [
                "oraculus_di_auditor.rec17",
                "oraculus_di_auditor.rgk18",
                "oraculus_di_auditor.aei19",
                "oraculus_di_auditor.aer20",
            ],
        }


__all__ = ["RAIAService"]
