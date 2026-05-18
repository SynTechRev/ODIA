"""DB-backed list query routes for the UI listing pages (v3.2.0).

Pre-v3.2 the Documents / Anomalies / Analysis / Synthesis pages all
read from a browser localStorage Zustand store that ONLY captured
audits initiated via the UI's drag-and-drop Upload flow. Webhook-
driven ingests (the entire scraper pipeline introduced in v3.0.x)
never touched that store, so the operator-facing UI was empty even
when the DB held hundreds of audited documents. The only DB-backed
view was the Dashboard's summary card.

This module fills that gap. It exposes paginated, filterable
read-only GET endpoints over the persisted Document / Analysis /
Anomaly rows so the listing pages can render real data regardless
of whether the underlying audit was triggered via UI upload,
n8n webhook, direct curl, or any future ingestion path.

Endpoints
---------
    GET /api/v1/documents
        Paginated list of Document rows. Filter by jurisdiction or
        document_type. Joined to Analysis for scalar_score and to
        Anomaly counts for findings_count.

    GET /api/v1/anomalies
        Paginated list of Anomaly rows joined through Analysis to
        Document for jurisdiction + title. Filter by severity,
        layer, jurisdiction, or document_id.

    GET /api/v1/analyses
        Paginated list of Analysis rows joined to documents.
        Filter by jurisdiction.

    GET /api/v1/jurisdictions
        Non-paginated. Returns DISTINCT jurisdictions from the
        Documents table with per-jurisdiction counts (docs,
        analyses, anomalies) and last-audit timestamp. Used by the
        Dashboard JURISDICTION card multi-jurisdiction view and by
        filter dropdowns throughout the UI.

    GET /api/v1/synthesis/aggregates
        Cross-document aggregations matching the Master Audit
        Synthesis page's shape: findings grouped by anomaly_id,
        vendor keyword hits, statute citations. Optional
        ``jurisdictions=a,b,c`` query string to scope the
        aggregation; default is all jurisdictions in the DB.

Pagination contract (uniform across paginated endpoints)
--------------------------------------------------------
    Query params:
        page:     1-indexed, default 1, min 1
        per_page: default 50, min 1, max 200
        Plus endpoint-specific filter params.

    Response shape:
        {
          "items":    [...],
          "total":    int,       # total matching rows
          "page":     int,       # echoed
          "per_page": int,       # echoed
          "has_more": bool,      # (page * per_page) < total
        }

Fail-open: if the DB layer is unavailable or a query throws, each
endpoint returns a structurally-valid empty response with a
top-level ``available: false`` (or, for paginated endpoints,
``items=[], total=0``) so the UI degrades cleanly rather than
crashing.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, Query

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]
    Query = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Vendor + statute keyword catalogues (mirror raia.patterns where possible)
# ---------------------------------------------------------------------------

_VENDOR_KEYWORDS = (
    "flock",
    "axon",
    "motorola",
    "palantir",
    "clearview",
    "vigilant",
    "shotspotter",
    "fusus",
    "cellhawk",
    "genetec",
    "lexipol",
    "verkada",
    "t-mobile",
)


def register_query_routes(app: Any) -> None:  # noqa: C901 — route registrar
    """Attach DB-backed list query routes to a FastAPI application."""
    if not _FASTAPI_AVAILABLE:
        logger.warning("FastAPI not installed — query routes will not be registered.")
        return

    router = APIRouter(tags=["query"])

    # -------------------------------------------------------------------
    # GET /api/v1/documents
    # -------------------------------------------------------------------
    @router.get("/api/v1/documents")
    async def list_documents(
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=200),
        jurisdiction: str | None = None,
        document_type: str | None = None,
    ) -> dict[str, Any]:
        """List Document rows, paginated and joined for finding counts."""
        empty = _empty_page(page, per_page)
        try:
            from sqlalchemy import func

            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError as exc:
            logger.warning("query.list_documents: DB layer unavailable (%s)", exc)
            return empty

        try:
            with get_db() as session:
                Document = db_models.Document  # noqa: N806
                Analysis = db_models.Analysis  # noqa: N806
                Anomaly = db_models.Anomaly  # noqa: N806

                base = session.query(Document)
                if jurisdiction:
                    base = base.filter(Document.jurisdiction == jurisdiction)
                if document_type:
                    base = base.filter(Document.document_type == document_type)

                total = base.count()
                rows = (
                    base.order_by(Document.created_at.desc())
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )

                # For each doc fetch its latest analysis + anomaly count.
                # N+1 in the worst case but doc lists are bounded by per_page
                # (<=200), so a single round-trip with subqueries would buy
                # very little while complicating the join shape.
                items = []
                for d in rows:
                    analysis = (
                        session.query(Analysis)
                        .filter(Analysis.document_id == d.document_id)
                        .order_by(Analysis.analysis_timestamp.desc())
                        .first()
                    )
                    anomaly_count = 0
                    if analysis is not None:
                        anomaly_count = (
                            session.query(func.count(Anomaly.id))
                            .filter(Anomaly.analysis_id == analysis.id)
                            .scalar()
                            or 0
                        )
                    items.append(
                        {
                            "id": d.id,
                            "document_id": d.document_id,
                            "title": d.title,
                            "document_type": d.document_type,
                            "jurisdiction": d.jurisdiction,
                            "authority": d.authority,
                            "version_date": (
                                d.version_date.isoformat() if d.version_date else None
                            ),
                            "signatory": d.signatory,
                            "created_at": (
                                d.created_at.isoformat() if d.created_at else None
                            ),
                            "updated_at": (
                                d.updated_at.isoformat() if d.updated_at else None
                            ),
                            "latest_analysis_id": (
                                analysis.id if analysis is not None else None
                            ),
                            "latest_analysis_at": (
                                analysis.analysis_timestamp.isoformat()
                                if analysis is not None
                                and analysis.analysis_timestamp is not None
                                else None
                            ),
                            "scalar_score": (
                                float(analysis.scalar_score)
                                if analysis is not None
                                and analysis.scalar_score is not None
                                else None
                            ),
                            "anomaly_count": int(anomaly_count),
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning("query.list_documents: query failed (%s)", exc)
            return empty

        return {
            "items": items,
            "total": int(total),
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < int(total),
        }

    # -------------------------------------------------------------------
    # GET /api/v1/anomalies
    # -------------------------------------------------------------------
    @router.get("/api/v1/anomalies")
    async def list_anomalies(
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=200),
        severity: str | None = None,
        layer: str | None = None,
        jurisdiction: str | None = None,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        """List Anomaly rows joined to Document for jurisdiction + title."""
        empty = _empty_page(page, per_page)
        try:
            import json

            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError as exc:
            logger.warning("query.list_anomalies: DB layer unavailable (%s)", exc)
            return empty

        try:
            with get_db() as session:
                Document = db_models.Document  # noqa: N806
                Analysis = db_models.Analysis  # noqa: N806
                Anomaly = db_models.Anomaly  # noqa: N806

                base = (
                    session.query(Anomaly, Analysis, Document)
                    .join(Analysis, Analysis.id == Anomaly.analysis_id)
                    .join(Document, Document.document_id == Analysis.document_id)
                )
                if severity:
                    base = base.filter(Anomaly.severity == severity.lower())
                if layer:
                    base = base.filter(Anomaly.layer == layer.lower())
                if jurisdiction:
                    base = base.filter(Document.jurisdiction == jurisdiction)
                if document_id:
                    base = base.filter(Document.document_id == document_id)

                total = base.count()
                rows = (
                    base.order_by(
                        # severity order: critical > high > medium > low
                        Analysis.analysis_timestamp.desc(),
                        Anomaly.id.desc(),
                    )
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )

                items = []
                for a, an, d in rows:
                    try:
                        details = json.loads(a.details_json) if a.details_json else {}
                    except Exception:  # noqa: BLE001
                        details = {}
                    items.append(
                        {
                            "id": a.id,
                            "anomaly_id": a.anomaly_id,
                            "issue": a.issue,
                            "severity": a.severity,
                            "layer": a.layer,
                            "details": details,
                            "analysis_id": an.id,
                            "analysis_timestamp": (
                                an.analysis_timestamp.isoformat()
                                if an.analysis_timestamp
                                else None
                            ),
                            "document_id": d.document_id,
                            "document_title": d.title,
                            "jurisdiction": d.jurisdiction,
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning("query.list_anomalies: query failed (%s)", exc)
            return empty

        return {
            "items": items,
            "total": int(total),
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < int(total),
        }

    # -------------------------------------------------------------------
    # GET /api/v1/analyses
    # -------------------------------------------------------------------
    @router.get("/api/v1/analyses")
    async def list_analyses(
        page: int = Query(1, ge=1),
        per_page: int = Query(50, ge=1, le=200),
        jurisdiction: str | None = None,
    ) -> dict[str, Any]:
        """List Analysis rows joined to documents."""
        empty = _empty_page(page, per_page)
        try:
            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError as exc:
            logger.warning("query.list_analyses: DB layer unavailable (%s)", exc)
            return empty

        try:
            with get_db() as session:
                Document = db_models.Document  # noqa: N806
                Analysis = db_models.Analysis  # noqa: N806

                base = session.query(Analysis, Document).join(
                    Document, Document.document_id == Analysis.document_id
                )
                if jurisdiction:
                    base = base.filter(Document.jurisdiction == jurisdiction)

                total = base.count()
                rows = (
                    base.order_by(Analysis.analysis_timestamp.desc())
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )

                items = []
                for an, d in rows:
                    items.append(
                        {
                            "id": an.id,
                            "document_id": d.document_id,
                            "document_title": d.title,
                            "document_type": d.document_type,
                            "jurisdiction": d.jurisdiction,
                            "analysis_timestamp": (
                                an.analysis_timestamp.isoformat()
                                if an.analysis_timestamp
                                else None
                            ),
                            "anomaly_count": int(an.anomaly_count or 0),
                            "scalar_score": (
                                float(an.scalar_score)
                                if an.scalar_score is not None
                                else None
                            ),
                            "severity_score": (
                                float(an.severity_score)
                                if an.severity_score is not None
                                else None
                            ),
                            "engine_version": an.engine_version,
                            "summary": an.summary,
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning("query.list_analyses: query failed (%s)", exc)
            return empty

        return {
            "items": items,
            "total": int(total),
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < int(total),
        }

    # -------------------------------------------------------------------
    # GET /api/v1/jurisdictions
    # -------------------------------------------------------------------
    @router.get("/api/v1/jurisdictions")
    async def list_jurisdictions() -> dict[str, Any]:
        """Distinct jurisdictions with per-jurisdiction roll-up counts.

        Non-paginated: jurisdictions are assumed <100 in any realistic
        deployment. Used by the Dashboard's multi-jurisdiction tile
        and by filter dropdowns throughout the UI.
        """
        empty = {"available": False, "items": []}
        try:
            from sqlalchemy import func

            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError as exc:
            logger.warning("query.list_jurisdictions: DB layer unavailable (%s)", exc)
            return empty

        try:
            with get_db() as session:
                Document = db_models.Document  # noqa: N806
                Analysis = db_models.Analysis  # noqa: N806
                Anomaly = db_models.Anomaly  # noqa: N806

                # Per-jurisdiction document counts.
                doc_rows = (
                    session.query(
                        Document.jurisdiction,
                        func.count(Document.id),
                    )
                    .filter(Document.jurisdiction.isnot(None))
                    .group_by(Document.jurisdiction)
                    .all()
                )

                items = []
                for jur, doc_count in doc_rows:
                    if not jur:
                        continue
                    # Analyses + anomalies via join.
                    analysis_count = (
                        session.query(func.count(Analysis.id))
                        .join(Document, Document.document_id == Analysis.document_id)
                        .filter(Document.jurisdiction == jur)
                        .scalar()
                        or 0
                    )
                    anomaly_count = (
                        session.query(func.count(Anomaly.id))
                        .join(Analysis, Analysis.id == Anomaly.analysis_id)
                        .join(Document, Document.document_id == Analysis.document_id)
                        .filter(Document.jurisdiction == jur)
                        .scalar()
                        or 0
                    )
                    last_audit = (
                        session.query(Analysis.analysis_timestamp)
                        .join(Document, Document.document_id == Analysis.document_id)
                        .filter(Document.jurisdiction == jur)
                        .order_by(Analysis.analysis_timestamp.desc())
                        .limit(1)
                        .scalar()
                    )
                    items.append(
                        {
                            "jurisdiction": jur,
                            "document_count": int(doc_count),
                            "analysis_count": int(analysis_count),
                            "anomaly_count": int(anomaly_count),
                            "last_audit_at": (
                                last_audit.isoformat() if last_audit else None
                            ),
                        }
                    )
                # Stable order: by descending doc count, then alpha.
                items.sort(key=lambda x: (-x["document_count"], x["jurisdiction"]))
        except Exception as exc:  # noqa: BLE001
            logger.warning("query.list_jurisdictions: query failed (%s)", exc)
            return empty

        return {"available": True, "items": items}

    # -------------------------------------------------------------------
    # GET /api/v1/synthesis/aggregates
    # -------------------------------------------------------------------
    @router.get("/api/v1/synthesis/aggregates")
    async def synthesis_aggregates(  # noqa: C901 — aggregation has many branches
        jurisdictions: str | None = None,
    ) -> dict[str, Any]:
        """Cross-document aggregations for the Master Audit Synthesis page.

        Returns finding-id rollups, vendor keyword hits, and severity
        distribution across all (or a filtered subset of) jurisdictions.
        Mirrors what the v3.1-era Synthesis page was computing client-side
        from localStorage, but sourced from the actual persisted corpus.
        """
        empty = {
            "available": False,
            "jurisdictions_scope": [],
            "total_documents": 0,
            "total_anomalies": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_finding_id": [],
            "by_vendor": [],
            "by_layer": [],
        }
        try:
            from oraculus_di_auditor.db import models as db_models
            from oraculus_di_auditor.db.session import get_db
        except ImportError as exc:
            logger.warning("query.synthesis_aggregates: DB layer unavailable (%s)", exc)
            return empty

        raw_jurisdictions = jurisdictions.split(",") if jurisdictions else []
        jurisdiction_filter = [j.strip() for j in raw_jurisdictions if j.strip()]

        try:
            with get_db() as session:
                Document = db_models.Document  # noqa: N806
                Analysis = db_models.Analysis  # noqa: N806
                Anomaly = db_models.Anomaly  # noqa: N806

                doc_query = session.query(Document)
                if jurisdiction_filter:
                    doc_query = doc_query.filter(
                        Document.jurisdiction.in_(jurisdiction_filter)
                    )
                total_docs = doc_query.count()

                # Distinct jurisdictions in scope (echoed back in response).
                scope_rows = (
                    session.query(Document.jurisdiction)
                    .filter(Document.jurisdiction.isnot(None))
                    .distinct()
                    .all()
                )
                jurisdictions_in_scope = (
                    sorted(
                        {r[0] for r in scope_rows if r[0]}
                        & (set(jurisdiction_filter) if jurisdiction_filter else set())
                    )
                    if jurisdiction_filter
                    else sorted({r[0] for r in scope_rows if r[0]})
                )

                # Pull all anomalies in scope. For sane corpora (<100k
                # anomalies) this is fine; would paginate or stream for
                # larger.
                anomaly_query = (
                    session.query(Anomaly, Document.jurisdiction)
                    .join(Analysis, Analysis.id == Anomaly.analysis_id)
                    .join(Document, Document.document_id == Analysis.document_id)
                )
                if jurisdiction_filter:
                    anomaly_query = anomaly_query.filter(
                        Document.jurisdiction.in_(jurisdiction_filter)
                    )
                anomalies = anomaly_query.all()
                total_anomalies = len(anomalies)

                by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                by_finding_id: dict[str, dict[str, Any]] = {}
                by_vendor: dict[str, dict[str, Any]] = {}
                by_layer: dict[str, int] = {}

                for a, jur in anomalies:
                    sev = (a.severity or "").lower()
                    if sev in by_severity:
                        by_severity[sev] += 1

                    aid = a.anomaly_id or "unknown"
                    bucket = by_finding_id.setdefault(
                        aid,
                        {
                            "anomaly_id": aid,
                            "count": 0,
                            "severity": sev,
                            "layer": (a.layer or "").lower(),
                            "jurisdictions": set(),
                            "example_issue": a.issue or "",
                        },
                    )
                    bucket["count"] += 1
                    if jur:
                        bucket["jurisdictions"].add(jur)

                    layer_key = (a.layer or "unknown").lower()
                    by_layer[layer_key] = by_layer.get(layer_key, 0) + 1

                    # Vendor keyword scan over issue + details_json (string-
                    # ified so we don't have to recurse the dict).
                    haystack = (a.issue or "") + " "
                    if a.details_json:
                        haystack += a.details_json
                    hay_lower = haystack.lower()
                    for vendor in _VENDOR_KEYWORDS:
                        if vendor in hay_lower:
                            v_bucket = by_vendor.setdefault(
                                vendor,
                                {
                                    "vendor": vendor,
                                    "count": 0,
                                    "jurisdictions": set(),
                                },
                            )
                            v_bucket["count"] += 1
                            if jur:
                                v_bucket["jurisdictions"].add(jur)

                # Materialise sets to sorted lists for JSON-serialisability.
                finding_items = sorted(
                    (
                        {
                            "anomaly_id": v["anomaly_id"],
                            "count": v["count"],
                            "severity": v["severity"],
                            "layer": v["layer"],
                            "jurisdictions": sorted(v["jurisdictions"]),
                            "jurisdiction_count": len(v["jurisdictions"]),
                            "example_issue": v["example_issue"][:240],
                        }
                        for v in by_finding_id.values()
                    ),
                    key=lambda x: (-x["count"], x["anomaly_id"]),
                )
                vendor_items = sorted(
                    (
                        {
                            "vendor": v["vendor"],
                            "count": v["count"],
                            "jurisdictions": sorted(v["jurisdictions"]),
                            "jurisdiction_count": len(v["jurisdictions"]),
                        }
                        for v in by_vendor.values()
                    ),
                    key=lambda x: (-x["count"], x["vendor"]),
                )
                layer_items = sorted(
                    ({"layer": k, "count": v} for k, v in by_layer.items()),
                    key=lambda x: (-x["count"], x["layer"]),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("query.synthesis_aggregates: query failed (%s)", exc)
            return empty

        return {
            "available": True,
            "jurisdictions_scope": jurisdictions_in_scope,
            "total_documents": int(total_docs),
            "total_anomalies": int(total_anomalies),
            "by_severity": by_severity,
            "by_finding_id": finding_items,
            "by_vendor": vendor_items,
            "by_layer": layer_items,
        }

    app.include_router(router)
    logger.info(
        "Query routes registered at /api/v1/{documents,anomalies,analyses,"
        "jurisdictions,synthesis/aggregates}"
    )


def _empty_page(page: int, per_page: int) -> dict[str, Any]:
    """Structurally-valid empty response for paginated endpoints."""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "per_page": per_page,
        "has_more": False,
    }


__all__ = ["register_query_routes"]
