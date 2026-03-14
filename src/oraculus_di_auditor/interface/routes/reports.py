"""FastAPI routes for unified report generation.

Provides POST /reports/generate — accepts raw analysis results and returns
a structured AuditReport in the requested formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    from fastapi import APIRouter
    from pydantic import BaseModel, Field

    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False
    BaseModel = object  # type: ignore[assignment,misc]
    Field = lambda *a, **kw: None  # type: ignore[assignment]  # noqa: E731

if TYPE_CHECKING:
    pass


class GenerateReportRequest(BaseModel):  # type: ignore[misc]
    """Request body for POST /reports/generate."""

    report_type: str = "single"  # "single", "multi", "executive"
    analysis_results: list[dict[str, Any]] = Field(default_factory=list)
    jurisdiction: str | None = None
    formats: list[str] = Field(default_factory=lambda: ["json", "markdown"])


class GenerateReportResponse(BaseModel):  # type: ignore[misc]
    """Response body for POST /reports/generate."""

    report_id: str
    generated_formats: list[str]
    report: dict[str, Any]


def register_report_routes(app: Any) -> None:
    """Register /reports/* endpoints on *app*.

    Safe to call even if FastAPI is not installed — the function is a no-op
    in that case.
    """
    if not _FASTAPI_AVAILABLE:
        return  # pragma: no cover

    router = APIRouter(prefix="/reports", tags=["reports"])

    @router.post("/generate", response_model=GenerateReportResponse)
    async def generate_report(request: GenerateReportRequest) -> GenerateReportResponse:
        """Generate a structured AuditReport from raw analysis pipeline output.

        Args:
            request: Report type, raw analysis results, optional jurisdiction
                and format list.

        Returns:
            GenerateReportResponse with report_id, generated_formats, and the
            full AuditReport serialised as a JSON dict.
        """
        from oraculus_di_auditor.reporting.models import build_report_from_analysis

        # Map "executive" report_type to single_jurisdiction
        rtype = {
            "single": "single_jurisdiction",
            "multi": "multi_jurisdiction",
            "executive": "single_jurisdiction",
        }.get(request.report_type, "single_jurisdiction")

        audit_report = build_report_from_analysis(
            request.analysis_results,
            jurisdiction=request.jurisdiction,
            title="ODIA Audit Report",
            report_type=rtype,
        )

        # Determine which formats were actually generated (always json here;
        # file-based formats require export_report — this endpoint returns JSON only)
        generated_formats = list(
            {fmt for fmt in request.formats if fmt in ("json", "markdown")}
        )
        if "json" not in generated_formats:
            generated_formats.append("json")
        generated_formats = sorted(generated_formats)

        return GenerateReportResponse(
            report_id=audit_report.report_id,
            generated_formats=generated_formats,
            report=audit_report.model_dump(),
        )

    app.include_router(router)
