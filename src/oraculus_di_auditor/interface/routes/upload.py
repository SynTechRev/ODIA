"""FastAPI routes for file upload and audit pipeline execution.

Provides a complete web-based audit workflow:
  - Upload documents (PDF, JSON, TXT, XML)
  - Upload images with OCR extraction (JPEG, PNG)
  - List / delete uploaded files
  - Run the full audit pipeline in a background thread
  - Poll job progress and retrieve results
  - Download reports (Markdown, HTML, PDF, DOCX) and evidence packets (ZIP)

Endpoints:
  POST   /api/v1/upload                         upload single file
  POST   /api/v1/upload/batch                   upload multiple files
  POST   /api/v1/upload/image                   upload image and extract text via OCR
  GET    /api/v1/upload/files                   list uploaded files
  DELETE /api/v1/upload/files/{file_id}         remove a file
  POST   /api/v1/audit/run                      start audit job
  GET    /api/v1/audit/status/{job_id}          poll job progress
  GET    /api/v1/audit/results/{job_id}         retrieve job results
  GET    /api/v1/audit/export/{job_id}          download report
  GET    /api/v1/audit/evidence-packet/{job_id} download evidence ZIP
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import tempfile
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory stores — process-lifetime; suitable for local/single-user deployment
# ---------------------------------------------------------------------------
_FILES: dict[str, dict[str, Any]] = {}
_JOBS: dict[str, dict[str, Any]] = {}
_STORE_LOCK = threading.Lock()

# Temp directory — created once at import
_UPLOAD_DIR: Path = Path(tempfile.gettempdir()) / "odia_uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

_ALLOWED_EXTENSIONS = frozenset({".pdf", ".json", ".txt", ".xml"})
_ALLOWED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})

try:
    from fastapi import APIRouter, File, HTTPException, UploadFile
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    from pydantic import Field as PydanticField

    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment, misc]
    PydanticField = lambda *a, **kw: None  # type: ignore[assignment]  # noqa: E731


# ---------------------------------------------------------------------------
# File ingestion helpers
# ---------------------------------------------------------------------------


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ingest_uploaded_file(path: Path) -> dict[str, Any]:
    """Read an uploaded file and return a minimal document dict for analysis.

    Exported for testing.
    """
    ext = path.suffix.lower()
    text = ""

    if ext == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")

    elif ext == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                text = (
                    data.get("raw_text")
                    or data.get("text")
                    or data.get("content")
                    or data.get("body")
                    or ""
                )
                if not text:
                    text = json.dumps(data, indent=2)
            else:
                text = json.dumps(data, indent=2)
        except Exception:
            text = path.read_text(encoding="utf-8", errors="replace")

    elif ext == ".xml":
        try:
            import xml.etree.ElementTree as ET  # noqa: N814

            tree = ET.parse(str(path))
            text = " ".join(
                (el.text or "").strip() for el in tree.iter() if el.text and el.text.strip()
            )
        except Exception:
            text = path.read_text(encoding="utf-8", errors="replace")

    elif ext == ".pdf":
        try:
            import pypdf  # type: ignore[import]

            reader = pypdf.PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            text = f"[PDF: {path.name} — install pypdf to extract text]"
        except Exception as exc:
            text = f"[PDF: {path.name} — extraction error: {exc}]"

    return {
        "document_id": path.stem,
        "raw_text": text,
        "title": path.name,
        "source": str(path),
    }


def _ocr_image(path: Path) -> tuple[str, str]:
    """Extract text from an image file.

    Returns ``(raw_text, ocr_method)`` where *ocr_method* is one of
    ``"tesseract"``, ``"pillow_stub"``, or ``"unavailable"``.

    Exported for testing.
    """
    try:
        import pytesseract  # type: ignore[import]
        from PIL import Image  # type: ignore[import]

        img = Image.open(str(path))
        text = pytesseract.image_to_string(img)
        return text.strip(), "tesseract"
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("tesseract OCR failed for %s: %s", path.name, exc)

    # Fallback: return filename as stub text so the document is still auditable
    return f"[Image: {path.name} — install pytesseract for OCR text extraction]", "unavailable"


def _flatten_findings(result: dict[str, Any], document_id: str) -> list[dict[str, Any]]:
    """Flatten the nested findings dict from analyze_document into a flat list."""
    flat: list[dict[str, Any]] = []
    raw = result.get("findings", {})

    if isinstance(raw, dict):
        for detector, items in raw.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        f = dict(item)
                        f.setdefault("layer", detector)
                        f["document_id"] = document_id
                        flat.append(f)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                f = dict(item)
                f["document_id"] = document_id
                flat.append(f)

    return flat


def _build_markdown_report(results: dict[str, Any]) -> str:
    """Build a Markdown audit report from job results."""
    doc_count = results.get("document_count", 0)
    finding_count = results.get("finding_count", 0)
    generated = results.get("generated_at", "N/A")
    sev = results.get("severity_summary", {})

    lines: list[str] = [
        "# O.D.I.A. Audit Report",
        "",
        f"**Generated**: {generated}  ",
        f"**Documents analyzed**: {doc_count}  ",
        f"**Total findings**: {finding_count}  ",
        "",
        "## Severity Summary",
        "",
    ]
    for level in ("critical", "high", "medium", "low"):
        count = sev.get(level, 0)
        if count:
            lines.append(f"- **{level.upper()}**: {count}")

    lines += ["", "---", "", "## Findings", ""]

    findings = sorted(
        results.get("findings", []),
        key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
            f.get("severity", "low"), 3
        ),
    )

    for i, f in enumerate(findings, 1):
        severity = f.get("severity", "unknown").upper()
        lines += [
            f"### Finding {i:03d} — [{severity}] {f.get('issue', 'Unknown issue')}",
            "",
            f"**Detector**: `{f.get('layer', 'unknown')}`  ",
            f"**Document**: `{f.get('document_id', 'unknown')}`  ",
            f"**Severity**: {severity}  ",
            "",
        ]
        if "plain_summary" in f:
            lines += [
                f"**Summary**: {f['plain_summary']}  ",
                "",
                f"**Why it matters**: {f.get('plain_impact', '')}  ",
                "",
                f"**Recommended action**: {f.get('plain_action', '')}  ",
                "",
            ]
        lines += ["---", ""]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Background audit executor
# ---------------------------------------------------------------------------


def _execute_audit_job(
    job_id: str, file_ids: list[str], config_overrides: dict[str, Any]
) -> None:
    """Run the full audit pipeline for all specified files and update job state."""

    def _update(patch: dict[str, Any]) -> None:
        with _STORE_LOCK:
            _JOBS[job_id].update(patch)

    _update({"status": "running"})
    all_findings: list[dict[str, Any]] = []
    doc_manifests: list[dict[str, Any]] = []
    docs_processed = 0

    try:
        from oraculus_di_auditor.analysis import analyze_document

        with _STORE_LOCK:
            files_snapshot = [_FILES[fid] for fid in file_ids if fid in _FILES]

        total = len(files_snapshot)

        for i, file_meta in enumerate(files_snapshot):
            _update({
                "progress": {
                    "phase": f"Analyzing {file_meta['name']} ({i + 1}/{total})",
                    "docs_processed": i,
                    "findings_count": len(all_findings),
                    "total_docs": total,
                }
            })

            path = Path(file_meta["path"])
            doc = ingest_uploaded_file(path)
            result = analyze_document(doc)
            findings = _flatten_findings(result, doc["document_id"])
            all_findings.extend(findings)
            docs_processed += 1

            doc_manifests.append({
                "document_id": doc["document_id"],
                "filename": file_meta["name"],
                "sha256": file_meta["sha256"],
                "size": file_meta["size"],
                "format": file_meta["format"],
                "finding_count": len(findings),
            })

        # Apply plain-language translations
        try:
            from oraculus_di_auditor.reporting.plain_language import translate_report

            all_findings = translate_report(all_findings)
        except Exception as exc:
            logger.warning("Plain-language translation failed: %s", exc)

        severity_counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in all_findings:
            sev = f.get("severity", "low")
            if sev in severity_counts:
                severity_counts[sev] += 1

        _update({
            "status": "complete",
            "results": {
                "job_id": job_id,
                "document_count": docs_processed,
                "finding_count": len(all_findings),
                "severity_summary": severity_counts,
                "findings": all_findings,
                "document_manifest": doc_manifests,
                "generated_at": datetime.now(UTC).isoformat(),
            },
            "progress": {
                "phase": "Complete",
                "docs_processed": docs_processed,
                "findings_count": len(all_findings),
                "total_docs": total,
            },
        })

    except Exception as exc:
        logger.error("Audit job %s failed: %s", job_id, exc, exc_info=True)
        _update({"status": "error", "error": str(exc)})


# ---------------------------------------------------------------------------
# Request model (defined at module level for FastAPI schema generation)
# ---------------------------------------------------------------------------


class _AuditRunRequest(BaseModel):  # type: ignore[misc]
    file_ids: list[str] = PydanticField(default_factory=list)
    jurisdiction: str | None = None
    agencies: list[str] | None = None


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def register_upload_routes(app: Any) -> None:
    """Register all upload and audit endpoints on *app*.

    Safe to call when FastAPI is unavailable — silently does nothing.
    """
    if not _FASTAPI_AVAILABLE:
        return  # pragma: no cover

    router = APIRouter(tags=["upload", "audit"])

    # -- Upload endpoints -------------------------------------------------------

    @router.post("/api/v1/upload")
    async def upload_file(file: UploadFile = File(...)) -> dict[str, Any]:
        """Upload a single document (PDF, JSON, TXT, XML)."""
        ext = Path(file.filename or "").suffix.lower()
        if ext not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type '{ext}'. "
                    f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
                ),
            )
        content = await file.read()
        file_id = str(uuid.uuid4())[:8]
        safe_name = Path(file.filename or "document").name
        dest = _UPLOAD_DIR / f"{file_id}_{safe_name}"
        dest.write_bytes(content)
        meta: dict[str, Any] = {
            "file_id": file_id,
            "name": safe_name,
            "size": len(content),
            "sha256": _sha256_bytes(content),
            "format": ext.lstrip("."),
            "path": str(dest),
            "uploaded_at": datetime.now(UTC).isoformat(),
        }
        with _STORE_LOCK:
            _FILES[file_id] = meta
        return meta

    @router.post("/api/v1/upload/batch")
    async def upload_batch(files: list[UploadFile] = File(...)) -> dict[str, Any]:
        """Upload multiple documents at once."""
        uploaded: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for file in files:
            ext = Path(file.filename or "").suffix.lower()
            if ext not in _ALLOWED_EXTENSIONS:
                errors.append({"name": file.filename or "", "error": f"Unsupported type '{ext}'"})
                continue
            content = await file.read()
            file_id = str(uuid.uuid4())[:8]
            safe_name = Path(file.filename or "document").name
            dest = _UPLOAD_DIR / f"{file_id}_{safe_name}"
            dest.write_bytes(content)
            meta = {
                "file_id": file_id,
                "name": safe_name,
                "size": len(content),
                "sha256": _sha256_bytes(content),
                "format": ext.lstrip("."),
                "path": str(dest),
                "uploaded_at": datetime.now(UTC).isoformat(),
            }
            with _STORE_LOCK:
                _FILES[file_id] = meta
            uploaded.append(meta)
        return {"uploaded": uploaded, "errors": errors}

    @router.post("/api/v1/upload/image")
    async def upload_image(file: UploadFile = File(...)) -> dict[str, Any]:
        """Upload a JPEG or PNG image and extract text via OCR.

        Returns the extracted text plus a file_id that can be used in
        POST /api/v1/audit/run just like any other uploaded file.
        """
        ext = Path(file.filename or "").suffix.lower()
        if ext not in _ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported image type '{ext}'. "
                    f"Allowed: {', '.join(sorted(_ALLOWED_IMAGE_EXTENSIONS))}"
                ),
            )
        content = await file.read()
        file_id = str(uuid.uuid4())[:8]
        safe_name = Path(file.filename or "image").name
        dest = _UPLOAD_DIR / f"{file_id}_{safe_name}"
        dest.write_bytes(content)

        raw_text, ocr_method = _ocr_image(dest)

        # Store as a TXT-format document so the audit pipeline can ingest it
        txt_path = _UPLOAD_DIR / f"{file_id}_{Path(safe_name).stem}.txt"
        txt_path.write_text(raw_text, encoding="utf-8")

        meta: dict[str, Any] = {
            "file_id": file_id,
            "name": safe_name,
            "size": len(content),
            "sha256": _sha256_bytes(content),
            "format": ext.lstrip("."),
            "path": str(txt_path),  # point pipeline at the extracted text
            "uploaded_at": datetime.now(UTC).isoformat(),
            "ocr_method": ocr_method,
        }
        with _STORE_LOCK:
            _FILES[file_id] = meta

        return {**meta, "raw_text": raw_text[:500] if raw_text else ""}

    @router.get("/api/v1/upload/files")
    async def list_files() -> dict[str, Any]:
        """List all files uploaded in this server session."""
        with _STORE_LOCK:
            files = list(_FILES.values())
        return {"files": files, "count": len(files)}

    @router.delete("/api/v1/upload/files/{file_id}")
    async def delete_file(file_id: str) -> dict[str, str]:
        """Remove an uploaded file by ID."""
        with _STORE_LOCK:
            if file_id not in _FILES:
                raise HTTPException(status_code=404, detail=f"File '{file_id}' not found")
            meta = _FILES.pop(file_id)
        path = Path(meta["path"])
        if path.exists():
            path.unlink()
        return {"status": "deleted", "file_id": file_id}

    # -- Audit endpoints --------------------------------------------------------

    @router.post("/api/v1/audit/run")
    async def run_audit(request: _AuditRunRequest) -> dict[str, Any]:
        """Start an audit job. Uses all uploaded files if file_ids is empty."""
        with _STORE_LOCK:
            available_ids = list(_FILES.keys())

        file_ids = request.file_ids if request.file_ids else available_ids
        if not file_ids:
            raise HTTPException(
                status_code=400,
                detail="No files available. Upload documents first.",
            )

        with _STORE_LOCK:
            missing = [fid for fid in file_ids if fid not in _FILES]
        if missing:
            raise HTTPException(status_code=404, detail=f"Files not found: {missing}")

        job_id = str(uuid.uuid4())
        with _STORE_LOCK:
            _JOBS[job_id] = {
                "job_id": job_id,
                "status": "pending",
                "file_ids": file_ids,
                "progress": {
                    "phase": "Queued",
                    "docs_processed": 0,
                    "findings_count": 0,
                    "total_docs": len(file_ids),
                },
                "results": None,
                "error": None,
                "created_at": datetime.now(UTC).isoformat(),
            }

        threading.Thread(
            target=_execute_audit_job,
            args=(job_id, file_ids, {"jurisdiction": request.jurisdiction}),
            daemon=True,
        ).start()

        return {"job_id": job_id, "status": "pending", "file_count": len(file_ids)}

    @router.get("/api/v1/audit/status/{job_id}")
    async def audit_status(job_id: str) -> dict[str, Any]:
        """Return current status and progress for a job."""
        with _STORE_LOCK:
            job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        return {
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "error": job.get("error"),
        }

    @router.get("/api/v1/audit/results/{job_id}")
    async def audit_results(job_id: str) -> dict[str, Any]:
        """Return complete audit results. Returns status-only dict if not yet complete."""
        with _STORE_LOCK:
            job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        if job["status"] == "error":
            raise HTTPException(status_code=500, detail=job.get("error", "Audit failed"))
        if job["status"] != "complete":
            return {"job_id": job_id, "status": job["status"], "results": None}
        return {"job_id": job_id, "status": "complete", "results": job["results"]}

    @router.get("/api/v1/audit/export/{job_id}")
    async def export_audit(job_id: str, format: str = "markdown") -> Any:  # noqa: A002
        """Download the audit report. format: markdown | html | pdf | docx"""
        with _STORE_LOCK:
            job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        if job["status"] != "complete":
            raise HTTPException(status_code=409, detail="Job not yet complete")

        report_md = _build_markdown_report(job["results"])
        short_id = job_id[:8]

        if format == "markdown":
            return StreamingResponse(
                io.BytesIO(report_md.encode("utf-8")),
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f'attachment; filename="audit_report_{short_id}.md"'
                },
            )

        if format == "html":
            try:
                import markdown as md_lib  # type: ignore[import]

                body = md_lib.markdown(report_md, extensions=["tables"])
            except ImportError:
                body = f"<pre>{report_md}</pre>"
            html = f"<!DOCTYPE html><html><body>{body}</body></html>"
            return StreamingResponse(
                io.BytesIO(html.encode("utf-8")),
                media_type="text/html",
                headers={
                    "Content-Disposition": f'attachment; filename="audit_report_{short_id}.html"'
                },
            )

        if format in ("pdf", "docx"):
            try:
                from oraculus_di_auditor.reporting.format_converters import (
                    markdown_to_docx,
                    markdown_to_pdf,
                )

                if format == "pdf":
                    content = markdown_to_pdf(report_md)
                    mime = "application/pdf"
                else:
                    content = markdown_to_docx(report_md)
                    mime = (
                        "application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document"
                    )
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type=mime,
                    headers={
                        "Content-Disposition": (
                            f'attachment; filename="audit_report_{short_id}.{format}"'
                        )
                    },
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=501,
                    detail=f"{format.upper()} export not available: {exc}",
                ) from exc

        raise HTTPException(
            status_code=400,
            detail=f"Unknown format '{format}'. Supported: markdown, html, pdf, docx",
        )

    @router.get("/api/v1/audit/evidence-packet/{job_id}")
    async def evidence_packet(job_id: str) -> Any:
        """Download a ZIP evidence packet containing the full audit materials."""
        with _STORE_LOCK:
            job = _JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        if job["status"] != "complete":
            raise HTTPException(status_code=409, detail="Job not yet complete")

        try:
            from oraculus_di_auditor.reporting.evidence_packet import generate_evidence_packet

            zip_bytes = generate_evidence_packet(job["results"])
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"Evidence packet error: {exc}"
            ) from exc

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="evidence_packet_{job_id[:8]}.zip"'
                )
            },
        )

    app.include_router(router)
