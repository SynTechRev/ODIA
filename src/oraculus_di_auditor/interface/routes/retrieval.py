"""FastAPI routes for Legistar document retrieval.

Endpoints:
  POST /api/v1/retrieve/legistar        Start a retrieval job
  GET  /api/v1/retrieve/status/{job_id} Poll retrieval job progress
  GET  /api/v1/retrieve/cities          List known Legistar cities
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
    from pydantic import Field as PydanticField

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment, misc]
    PydanticField = lambda *a, **kw: None  # type: ignore[assignment]  # noqa: E731


class _RetrievalRequest(BaseModel):  # type: ignore[misc]
    client_id: str
    start_date: str
    end_date: str
    output_dir: str = "data/retrieved"
    matter_types: list[str] | None = None


def _run_retrieval(job_id: str, request: _RetrievalRequest) -> None:
    """Background thread: run LegistarAdapter.retrieve_corpus and update job state."""

    def _update(patch: dict) -> None:
        with _JOB_LOCK:
            _RETRIEVAL_JOBS[job_id].update(patch)

    _update({"status": "running"})
    try:
        from oraculus_di_auditor.adapters.legistar_adapter import LegistarAdapter

        adapter = LegistarAdapter(request.client_id)
        output = Path(request.output_dir)
        output.mkdir(parents=True, exist_ok=True)

        manifest = adapter.retrieve_corpus(
            start_date=request.start_date,
            end_date=request.end_date,
            output_dir=output,
            matter_types=request.matter_types,
        )
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
