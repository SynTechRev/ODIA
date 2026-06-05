"""FastAPI routes for the legal-corpus subsystem (v3.7.1).

Exposes:
  GET  /api/v1/legal/status      — installed corpora + detector inventory
  POST /api/v1/legal/analyze     — run L-1 through L-10 on a document
  POST /api/v1/legal/memorandum  — generate litigation memorandum from findings
  POST /api/v1/legal/explain     — generate plain-language explainer
  POST /api/v1/legal/reeval      — Vector 3 temporal re-evaluation of prior findings
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models — must be at module level so FastAPI can resolve them
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel, Field

    class AnalyzeRequest(BaseModel):
        text: str = Field(..., description="Document text to analyze")
        document_id: str | None = Field(
            None, description="Optional document identifier"
        )
        layers: list[str] | None = Field(
            None,
            description=(
                "Detector layer IDs to run "
                "(e.g. ['l3_exemption_misapplication']). "
                "Omit to run all L-1 through L-10 detectors."
            ),
        )

    class MemorandumRequest(BaseModel):
        text: str = Field(..., description="Document text (used for TOA extraction)")
        findings: list[dict[str, Any]] = Field(
            ..., description="ODIA finding dicts (id/issue/severity/layer/details)"
        )
        doc_meta: dict[str, Any] = Field(
            default_factory=dict,
            description="Document metadata: title, agency, date",
        )
        to_field: str = Field(
            "Oversight Body / Responsible Agency",
            description="Memo recipient line",
        )
        recommended_actions: list[str] | None = Field(
            None, description="Optional bullet list for Conclusion section"
        )
        format: str = Field(
            "text",
            description="Output format: 'text' (default) or 'markdown'",
        )

    class ExplainRequest(BaseModel):
        findings: list[dict[str, Any]] = Field(
            ..., description="ODIA finding dicts (id/issue/severity/layer/details)"
        )
        doc_meta: dict[str, Any] = Field(
            default_factory=dict,
            description="Document metadata: title, agency, date",
        )
        audience: str = Field(
            "community",
            description="Target audience: 'community', 'council', or 'media'",
        )
        format: str = Field(
            "text",
            description="Output format: 'text' (default) or 'html'",
        )

    class ReevalRequest(BaseModel):
        document_id: str = Field(..., description="Document ID to re-evaluate")
        prior_run_date: str = Field(
            ...,
            description="ISO date (YYYY-MM-DD) of the previous analysis run",
        )
        run_date: str | None = Field(
            None, description="ISO date of this run; defaults to today"
        )

except ImportError:
    BaseModel = object  # type: ignore[assignment,misc]
    AnalyzeRequest = object  # type: ignore[assignment,misc]
    MemorandumRequest = object  # type: ignore[assignment,misc]
    ExplainRequest = object  # type: ignore[assignment,misc]
    ReevalRequest = object  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Detector registry — imported from single source of truth in odia_legal
# ---------------------------------------------------------------------------

try:
    from odia_legal.pipeline import LEGAL_DETECTOR_MODULES as _DETECTOR_MODULES
except ImportError:
    _DETECTOR_MODULES = [  # type: ignore[assignment]
        "odia_legal.detectors.l1_statutory_applicability",
        "odia_legal.detectors.l2_procedural_compliance",
        "odia_legal.detectors.l3_exemption_misapplication",
        "odia_legal.detectors.l4_ministerial_duty",
        "odia_legal.detectors.l5_federal_grant_compliance",
        "odia_legal.detectors.l6_constitutional_implication",
        "odia_legal.detectors.l7_regulatory_authority",
        "odia_legal.detectors.l9_recodification",
        "odia_legal.detectors.l10_balancing_test",
    ]  # fallback only; normally overridden by pipeline import above


def register_legal_routes(app: Any) -> None:
    """Register legal-corpus endpoints on *app*.

    Safe to call when FastAPI or the resolver are unavailable —
    silently does nothing.
    """
    try:
        from fastapi import APIRouter, HTTPException
    except ImportError:
        return

    router = APIRouter(tags=["legal"])

    # ------------------------------------------------------------------
    # GET /api/v1/legal/status
    # ------------------------------------------------------------------

    @router.get("/api/v1/legal/status")
    async def legal_status() -> dict[str, Any]:
        """Report on installed legal corpora and detector inventory."""
        import importlib

        detectors: dict[str, str] = {}
        for mod_path in _DETECTOR_MODULES:
            layer = mod_path.split(".")[-1]
            try:
                importlib.import_module(mod_path)
                detectors[layer] = "ok"
            except ImportError as exc:
                detectors[layer] = f"unavailable: {exc}"

        corpus_status: dict[str, Any] = {}
        try:
            from oraculus_di_auditor.legal.legal_resolver import get_resolver

            resolver = get_resolver()
            corpus_status = resolver.statistics()
        except Exception as exc:  # noqa: BLE001
            corpus_status = {"error": str(exc)}

        return {
            "status": "ok",
            "detectors": detectors,
            "detectors_available": sum(1 for v in detectors.values() if v == "ok"),
            "corpora": corpus_status,
        }

    # ------------------------------------------------------------------
    # POST /api/v1/legal/analyze
    # ------------------------------------------------------------------

    @router.post("/api/v1/legal/analyze")
    async def legal_analyze(request: AnalyzeRequest) -> dict[str, Any]:  # type: ignore[valid-type]
        """Run L-1 through L-10 legal detectors on a document."""
        import importlib

        doc = {
            "text": request.text,
            "document_id": request.document_id or "",
        }

        findings: list[dict[str, Any]] = []
        errors: list[str] = []

        for mod_path in _DETECTOR_MODULES:
            layer = mod_path.split(".")[-1]
            if request.layers and layer not in request.layers:
                continue
            try:
                mod = importlib.import_module(mod_path)
                findings.extend(mod.detect(doc))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{layer}: {exc}")
                logger.warning("legal_analyze: detector %s failed: %s", layer, exc)

        counts = {
            "high": sum(1 for f in findings if f.get("severity") == "high"),
            "medium": sum(1 for f in findings if f.get("severity") == "medium"),
            "low": sum(1 for f in findings if f.get("severity") == "low"),
            "total": len(findings),
        }

        return {
            "document_id": request.document_id,
            "findings": findings,
            "counts": counts,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # POST /api/v1/legal/memorandum
    # ------------------------------------------------------------------

    @router.post("/api/v1/legal/memorandum")
    async def legal_memorandum(request: MemorandumRequest) -> dict[str, Any]:  # type: ignore[valid-type]
        """Generate a litigation-grade memorandum from ODIA legal findings."""
        try:
            from odia_legal.reports.memorandum import generate_memorandum
        except ImportError as exc:
            raise HTTPException(
                status_code=503, detail=f"odia_legal not available: {exc}"
            ) from exc

        memo = generate_memorandum(
            doc_meta=request.doc_meta,
            findings=request.findings,
            to_field=request.to_field,
            recommended_actions=request.recommended_actions,
        )

        output = memo.to_markdown() if request.format == "markdown" else memo.to_text()

        return {
            "format": request.format,
            "output": output,
            "finding_count": len(request.findings),
            "toa_citations": memo.toa,
        }

    # ------------------------------------------------------------------
    # POST /api/v1/legal/explain
    # ------------------------------------------------------------------

    @router.post("/api/v1/legal/explain")
    async def legal_explain(request: ExplainRequest) -> dict[str, Any]:  # type: ignore[valid-type]
        """Generate a plain-language explainer for community education."""
        try:
            from odia_legal.reports.explainer import generate_explainer
        except ImportError as exc:
            raise HTTPException(
                status_code=503, detail=f"odia_legal not available: {exc}"
            ) from exc

        audience = request.audience
        if audience not in ("community", "council", "media"):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid audience '{audience}'. Must be community, council, or media.",
            )

        explainer = generate_explainer(
            doc_meta=request.doc_meta,
            findings=request.findings,
            audience=audience,  # type: ignore[arg-type]
        )

        output = (
            explainer.to_html() if request.format == "html" else explainer.to_text()
        )

        return {
            "audience": audience,
            "format": request.format,
            "output": output,
            "finding_count": len(request.findings),
            "summary": explainer.summary_table,
        }

    # ------------------------------------------------------------------
    # POST /api/v1/legal/reeval
    # ------------------------------------------------------------------

    @router.post("/api/v1/legal/reeval")
    async def legal_reeval(request: ReevalRequest) -> dict[str, Any]:  # type: ignore[valid-type]
        """Vector 3 temporal re-evaluation of prior findings for a document.

        Fetches the document from the DB, loads its prior legal findings,
        runs all L-1..L-10 detectors, and diffs against the prior run to
        surface NEW / RESOLVED / UPGRADED / DOWNGRADED / UNCHANGED findings
        plus any case-law treatment changes since prior_run_date.
        """
        try:
            from odia_legal.vector3 import LegalVector3
        except ImportError as exc:
            raise HTTPException(
                status_code=503, detail=f"odia_legal not available: {exc}"
            ) from exc

        try:
            import json as _json

            from oraculus_di_auditor.db.models import (
                Analysis,
                Anomaly,
                Document,
            )
            from oraculus_di_auditor.db.session import get_db, init_db

            init_db()
            db = next(get_db())

            doc = (
                db.query(Document)
                .filter(Document.document_id == request.document_id)
                .first()
            )
            if doc is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document '{request.document_id}' not found",
                )

            doc_text = doc.text or ""

            # Load prior legal-layer findings from DB
            legal_layers = {
                "l1_statutory_applicability",
                "l2_procedural_compliance",
                "l3_exemption_misapplication",
                "l4_ministerial_duty",
                "l5_federal_grant_compliance",
                "l6_constitutional_implication",
                "l7_regulatory_authority",
                "l9_recodification",
                "l10_balancing_test",
            }
            prior_findings: list[dict[str, Any]] = []
            analyses = (
                db.query(Analysis)
                .filter(Analysis.document_id == request.document_id)
                .all()
            )
            for analysis in analyses:
                for anomaly in (
                    db.query(Anomaly)
                    .filter(Anomaly.analysis_id == analysis.id)
                    .filter(Anomaly.layer.in_(legal_layers))
                    .all()
                ):
                    details: dict[str, Any] = {}
                    if anomaly.details_json:
                        try:
                            details = _json.loads(anomaly.details_json)
                        except Exception:  # noqa: BLE001
                            pass
                    prior_findings.append(
                        {
                            "id": anomaly.anomaly_id,
                            "issue": anomaly.issue,
                            "severity": anomaly.severity,
                            "layer": anomaly.layer,
                            "details": details,
                        }
                    )

        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=503, detail=f"DB unavailable: {exc}"
            ) from exc

        result = LegalVector3().reeval(
            doc={"text": doc_text, "document_id": request.document_id},
            prior_findings=prior_findings,
            prior_run_date=request.prior_run_date,
            run_date=request.run_date,
            doc_id=request.document_id,
        )

        return {
            **result.to_dict(),
            "prior_findings_count": len(prior_findings),
        }

    app.include_router(router)
    logger.info("Legal routes registered (/api/v1/legal/*)")
