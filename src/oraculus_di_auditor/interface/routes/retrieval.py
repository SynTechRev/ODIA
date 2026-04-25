"""FastAPI routes for Legistar document retrieval.

Endpoints:
  POST /api/v1/retrieve/legistar        Start a retrieval job
  GET  /api/v1/retrieve/status/{job_id} Poll retrieval job progress
  GET  /api/v1/retrieve/cities          List known Legistar cities

v2.7.6 X3 — two changes that turn the long-latent button into a
working feature on the desktop install:

  1. The default ``output_dir`` resolves via the same per-user data
     dir helper as jurisdiction discovery (Windows ``%APPDATA%/ODIA``,
     macOS ``~/Library/Application Support/ODIA``, Linux XDG). The
     pre-X3 default of ``"data/retrieved"`` was relative to CWD, which
     on a frozen Electron app pointed at the PyInstaller extraction
     dir — usually not user-writable, so the background thread failed
     silently.

  2. After ``LegistarAdapter.retrieve_corpus`` finishes, every
     downloaded file is registered into the upload-staging store via
     :func:`oraculus_di_auditor.interface.routes.upload.register_uploaded_path`.
     The frontend's ``listUploadedFiles()`` poll then picks them up
     and they appear in the Upload page's "files ready" table — same
     as drag-and-drop. Pre-X3 they were written to a separate dir and
     never surfaced anywhere the user could click "Run Audit" against.
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_RETRIEVAL_JOBS: dict[str, dict[str, Any]] = {}
_JOB_LOCK = threading.Lock()

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment, misc]


def _default_retrieval_dir() -> Path:
    """Cross-platform writable staging dir for Legistar downloads.

    Reuses the user-data root the jurisdiction loader resolves so a
    desktop user only has one ODIA-owned directory tree.
    """
    from oraculus_di_auditor.config.jurisdiction_loader import _user_data_root

    return _user_data_root() / "retrieved"


class _RetrievalRequest(BaseModel):  # type: ignore[misc]
    client_id: str
    start_date: str
    end_date: str
    output_dir: str | None = None
    matter_types: list[str] | None = None


def _run_retrieval(job_id: str, request: _RetrievalRequest) -> None:
    """Background thread: run LegistarAdapter.retrieve_corpus, then
    register every downloaded file into the upload-staging store."""

    def _update(patch: dict) -> None:
        with _JOB_LOCK:
            _RETRIEVAL_JOBS[job_id].update(patch)

    _update({"status": "running"})
    try:
        from oraculus_di_auditor.adapters.legistar_adapter import LegistarAdapter

        adapter = LegistarAdapter(request.client_id)
        output = (
            Path(request.output_dir) if request.output_dir else _default_retrieval_dir()
        )
        output.mkdir(parents=True, exist_ok=True)

        manifest = adapter.retrieve_corpus(
            start_date=request.start_date,
            end_date=request.end_date,
            output_dir=output,
            matter_types=request.matter_types,
        )

        # X3: surface downloaded files in the Upload page's table.
        registered: list[dict[str, Any]] = []
        registration_errors: list[dict[str, str]] = []
        try:
            from oraculus_di_auditor.interface.routes.upload import (
                register_uploaded_path,
            )
        except ImportError as exc:
            logger.warning(
                "Cannot register Legistar files into upload store: %s", exc
            )
            register_uploaded_path = None  # type: ignore[assignment]

        if register_uploaded_path is not None:
            for entry in manifest.get("files", []):
                local = Path(entry.get("local_path", ""))
                if not local.exists():
                    continue
                try:
                    meta = register_uploaded_path(
                        local,
                        source=entry.get("source_url"),
                        move=True,
                    )
                    registered.append(meta)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Registration of %s failed: %s", local.name, exc
                    )
                    registration_errors.append(
                        {"path": str(local), "error": str(exc)}
                    )

        manifest["registered_count"] = len(registered)
        manifest["registration_errors"] = registration_errors
        _update({"status": "complete", "manifest": manifest})
    except Exception as exc:
        logger.error("Retrieval job %s failed: %s", job_id, exc, exc_info=True)
        _update({"status": "error", "error": str(exc)})


def register_retrieval_routes(app: Any) -> None:
    """Register Legistar retrieval endpoints on *app*."""
    if not _FASTAPI_AVAILABLE:
        return

    router = APIRouter(tags=["retrieval"])

    @router.post("/api/v1/retrieve/legistar")
    async def start_retrieval(request: _RetrievalRequest) -> dict[str, Any]:
        """Start a Legistar document retrieval job."""
        job_id = str(uuid.uuid4())
        with _JOB_LOCK:
            _RETRIEVAL_JOBS[job_id] = {
                "job_id": job_id,
                "status": "pending",
                "client_id": request.client_id,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "manifest": None,
                "error": None,
                "created_at": datetime.now(UTC).isoformat(),
            }
        threading.Thread(
            target=_run_retrieval,
            args=(job_id, request),
            daemon=True,
        ).start()
        return {"job_id": job_id, "status": "pending"}

    @router.get("/api/v1/retrieve/status/{job_id}")
    async def retrieval_status(job_id: str) -> dict[str, Any]:
        """Get the status of a retrieval job."""
        with _JOB_LOCK:
            job = _RETRIEVAL_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        return {
            "job_id": job_id,
            "status": job["status"],
            "client_id": job["client_id"],
            "manifest": job.get("manifest"),
            "error": job.get("error"),
        }

    @router.get("/api/v1/retrieve/cities")
    async def list_cities() -> dict[str, Any]:
        """Return the curated list of known Legistar cities."""
        try:
            from oraculus_di_auditor.adapters.legistar_adapter import load_cities

            cities = load_cities()
        except Exception:
            cities = []
        return {"cities": cities, "count": len(cities)}

    app.include_router(router)
