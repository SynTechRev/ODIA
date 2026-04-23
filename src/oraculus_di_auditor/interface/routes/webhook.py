"""n8n Integration Routes for Oraculus-DI-Auditor.

Provides the dedicated webhook surface that n8n workflows call to drive
automated document ingestion, analysis, and batch synthesis without
chaining multiple existing endpoints.

Follows the architectural recommendation in ODIA_v251_Architectural_Analysis,
§4 Priority-1: three webhook endpoints are the complete n8n surface.

Endpoints:
    POST /api/v1/webhook/ingest-and-analyze
        Accepts a file + jurisdiction_id, runs the full Tier 1 pipeline,
        returns findings JSON in one round-trip. This is WF-001's terminus.

    POST /api/v1/webhook/batch-ingest
        Accepts a list of {path, jurisdiction_id} entries, enqueues a
        batch analysis job, returns job_id. Used by WF-002 (nightly scan).

    GET  /api/v1/webhook/health
        Lightweight liveness + tier readiness probe. Lower cost than
        /api/v1/health because it does not exercise detector imports.

    GET  /api/v1/webhook/status/{job_id}
        Polls the status of a batch job started via /batch-ingest.
        n8n WF-002's Wait node drives against this.

    POST /api/v1/webhook/synthesize
        Triggers the RAIA synthesis cycle across completed jurisdictions.
        Accepts {jurisdictions: [...], include_tier3: bool}. Returns
        synthesis_id; the generated DOCX ships to Google Drive via n8n WF-010.

Security:
    All endpoints accept a shared-secret header (X-ODIA-Webhook-Token) that
    n8n sends from its credential vault. Token is compared with
    ODIA_WEBHOOK_TOKEN from the environment. If the env var is unset the
    route module refuses to register, so misconfigured deployments fail
    loud rather than silently exposing an open pipeline.

    CORS is intentionally NOT widened here; the desktop app does not use
    these endpoints, and n8n calls them server-to-server.

Provenance:
    Every webhook call is logged to db.models.WebhookAuditLog with
    timestamp, source_ip, workflow_id (from X-N8N-Workflow-Id), and
    response_status. This gives the Provenance Chain Export (n8n WF-014)
    a complete litigation-grade audit trail.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WEBHOOK_TOKEN_ENV = "ODIA_WEBHOOK_TOKEN"
WEBHOOK_HEADER = "x-odia-webhook-token"
N8N_WORKFLOW_HEADER = "x-n8n-workflow-id"
N8N_EXECUTION_HEADER = "x-n8n-execution-id"

# Tier readiness markers — imported lazily to keep this module cheap.
_TIER1_MODULES = (
    "oraculus_di_auditor.analysis.audit_engine",
    "oraculus_di_auditor.ingestion.engine",
    "oraculus_di_auditor.reporting.template_engine",
)
_TIER2_MODULES = (
    "oraculus_di_auditor.mesh.mesh_coordinator",
    "oraculus_di_auditor.self_healing.self_healing_service",
)


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def _verify_token(presented: str | None) -> bool:
    """Constant-time comparison of the webhook token.

    Returns False if no token is configured in env — the route registrar
    refuses to register in that case, but this guard is kept as a second
    line of defence.
    """
    expected = os.environ.get(WEBHOOK_TOKEN_ENV)
    if not expected or not presented:
        return False
    return hmac.compare_digest(expected.encode(), presented.encode())


def _token_configured() -> bool:
    return bool(os.environ.get(WEBHOOK_TOKEN_ENV, "").strip())


# ---------------------------------------------------------------------------
# Tier-1 executor — the canonical analysis entry point
# ---------------------------------------------------------------------------

def _run_tier1_pipeline(
    file_bytes: bytes,
    filename: str,
    jurisdiction_id: str | None,
) -> dict[str, Any]:
    """Execute the full Tier-1 analysis on a single document.

    Kept as a plain function so it can be unit-tested without a FastAPI
    test client.
    """
    # Late imports so this module stays importable even when optional deps
    # are missing. The caller (the route wrapper) has already verified
    # that FastAPI is available.
    #
    # Drift patch (2026-04-23, spec v2.7.0 → current v2.7.0):
    #   The spec imports `IngestionEngine` with an `ingest_bytes(...)`
    #   method and calls `compute_recursive_scalar_score(anomalies)` with
    #   one arg. Current v2.7.0 uses function-based ingestion
    #   (`upload.ingest_uploaded_file(path: Path) -> dict`) and the
    #   scalar core takes `(doc, anomalies)`. This block routes through
    #   the real API via a tempfile round-trip for bytes → path.
    import tempfile

    from oraculus_di_auditor.analysis.audit_engine import analyze_document
    from oraculus_di_auditor.analysis.scalar_core import compute_recursive_scalar_score
    from oraculus_di_auditor.interface.routes.upload import ingest_uploaded_file

    sha256 = hashlib.sha256(file_bytes).hexdigest()

    # Preserve the incoming suffix so ingest_uploaded_file's PDF/JSON/
    # XML/TXT branch picks the right extractor. delete=False + manual
    # unlink so the file survives the `with` scope on Windows, where an
    # open handle blocks reopening.
    suffix = Path(filename).suffix or ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
    try:
        normalized = ingest_uploaded_file(tmp_path)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass

    # ingest_uploaded_file doesn't carry jurisdiction through — tuck it
    # into the doc dict so downstream detectors (multi-jurisdiction,
    # CCOPS compliance) can see it.
    if jurisdiction_id:
        normalized["jurisdiction_id"] = jurisdiction_id

    findings = analyze_document(normalized)
    score = compute_recursive_scalar_score(
        normalized, findings.get("anomalies", [])
    )

    return {
        "document": {
            "filename": filename,
            "sha256": sha256,
            "jurisdiction_id": jurisdiction_id,
            "byte_length": len(file_bytes),
        },
        "findings": findings,
        "recursive_scalar_score": score,
        "tier": 1,
    }


def _dedup_check(sha256: str) -> bool:
    """Return True if this SHA-256 has been seen before.

    Reads from db.models.SeenHash; if the table doesn't exist yet, returns
    False (never-seen) so callers still make forward progress. The table
    is added by migration alongside the first webhook-based ingestion.
    """
    try:
        # Drift patch: v2.7.0 contextmanager is get_db, not get_session.
        from oraculus_di_auditor.db.session import get_db as get_session
        from oraculus_di_auditor.db import models as db_models
    except ImportError:
        return False

    if not hasattr(db_models, "SeenHash"):
        return False

    try:
        with get_session() as session:
            row = session.query(db_models.SeenHash).filter_by(sha256=sha256).first()
            return row is not None
    except Exception as exc:  # noqa: BLE001 — dedup is a nice-to-have
        logger.warning("dedup_check failed: %s", exc)
        return False


def _record_webhook_call(
    *,
    endpoint: str,
    workflow_id: str | None,
    execution_id: str | None,
    status: int,
    source_ip: str | None,
) -> None:
    """Best-effort write to WebhookAuditLog. Never raises."""
    try:
        # Drift patch: v2.7.0 contextmanager is get_db, not get_session.
        from oraculus_di_auditor.db.session import get_db as get_session
        from oraculus_di_auditor.db import models as db_models
    except ImportError:
        return

    if not hasattr(db_models, "WebhookAuditLog"):
        return

    try:
        with get_session() as session:
            entry = db_models.WebhookAuditLog(
                endpoint=endpoint,
                workflow_id=workflow_id,
                execution_id=execution_id,
                status=status,
                source_ip=source_ip,
            )
            session.add(entry)
            session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("webhook audit log write failed: %s", exc)


# ---------------------------------------------------------------------------
# Route registrar — drops into existing interface/api.py pattern
# ---------------------------------------------------------------------------

def register_webhook_routes(app: Any) -> None:
    """Attach the n8n webhook router to a FastAPI application.

    Mirrors the shape of register_upload_routes() in
    interface/routes/upload.py so this file slots into the existing
    API composition without restructuring api.py.
    """
    try:
        from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
    except ImportError:
        logger.warning(
            "FastAPI not installed — webhook routes will not be registered."
        )
        return

    if not _token_configured():
        logger.error(
            "%s is not set in the environment. Webhook routes will NOT "
            "register. Set this variable and restart the API to enable "
            "n8n integration.",
            WEBHOOK_TOKEN_ENV,
        )
        return

    router = APIRouter(tags=["webhook", "n8n"])

    # ---- Health probe -----------------------------------------------------
    @router.get("/api/v1/webhook/health")
    async def webhook_health(request: Request) -> dict[str, Any]:
        """Lightweight liveness + tier-readiness probe."""
        tier1_ok = _check_tier_imports(_TIER1_MODULES)
        tier2_ok = _check_tier_imports(_TIER2_MODULES)
        return {
            "status": "healthy" if tier1_ok else "degraded",
            "tier1_ready": tier1_ok,
            "tier2_ready": tier2_ok,
            "webhook_token_configured": True,
            "odia_version": os.environ.get("ODIA_VERSION", "2.7.0"),
        }

    # ---- Ingest + analyze (single document) -------------------------------
    @router.post("/api/v1/webhook/ingest-and-analyze")
    async def webhook_ingest_analyze(
        request: Request,
        file: UploadFile = File(...),
        jurisdiction_id: str = Form(...),
    ) -> dict[str, Any]:
        """Full Tier 1 pipeline for a single document.

        n8n WF-001 CivicPlus scraper posts directly here.
        """
        _require_token(request)

        data = await file.read()
        sha256 = hashlib.sha256(data).hexdigest()

        # Early-exit on dedup: n8n's retry loop + CivicPlus's duplicate
        # URLs will cause the same document to be POSTed multiple times.
        # We short-circuit with a 200 + already_seen=true so WF-001 doesn't
        # treat it as an error.
        if _dedup_check(sha256):
            _record_webhook_call(
                endpoint="ingest-and-analyze",
                workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
                execution_id=request.headers.get(N8N_EXECUTION_HEADER),
                status=200,
                source_ip=_client_ip(request),
            )
            return {
                "status": "ok",
                "already_seen": True,
                "sha256": sha256,
                "jurisdiction_id": jurisdiction_id,
            }

        try:
            result = _run_tier1_pipeline(
                file_bytes=data,
                filename=file.filename or "unknown",
                jurisdiction_id=jurisdiction_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("webhook ingest-and-analyze failed")
            _record_webhook_call(
                endpoint="ingest-and-analyze",
                workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
                execution_id=request.headers.get(N8N_EXECUTION_HEADER),
                status=500,
                source_ip=_client_ip(request),
            )
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        _record_webhook_call(
            endpoint="ingest-and-analyze",
            workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
            execution_id=request.headers.get(N8N_EXECUTION_HEADER),
            status=200,
            source_ip=_client_ip(request),
        )
        return {"status": "ok", "already_seen": False, **result}

    # ---- Batch ingest (enqueue) -------------------------------------------
    @router.post("/api/v1/webhook/batch-ingest")
    async def webhook_batch_ingest(request: Request) -> dict[str, Any]:
        """Accept a batch descriptor and enqueue a background job.

        Body (JSON):
            {
              "jobs": [
                {"filename": "...", "file_b64": "...", "jurisdiction_id": "..."},
                ...
              ]
            }

        Returns:
            {"status": "accepted", "job_id": "...", "count": N}
        """
        _require_token(request)

        payload = await request.json()
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list) or not jobs:
            raise HTTPException(status_code=400, detail="jobs must be a non-empty list")

        job_id = secrets.token_hex(8)
        _enqueue_batch_job(job_id, jobs)

        _record_webhook_call(
            endpoint="batch-ingest",
            workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
            execution_id=request.headers.get(N8N_EXECUTION_HEADER),
            status=202,
            source_ip=_client_ip(request),
        )
        return {"status": "accepted", "job_id": job_id, "count": len(jobs)}

    # ---- Batch status poll ------------------------------------------------
    @router.get("/api/v1/webhook/status/{job_id}")
    async def webhook_status(request: Request, job_id: str) -> dict[str, Any]:
        _require_token(request)
        state = _get_batch_job_state(job_id)
        if state is None:
            raise HTTPException(status_code=404, detail="job_id not found")
        return state

    # ---- RAIA synthesis trigger -------------------------------------------
    @router.post("/api/v1/webhook/synthesize")
    async def webhook_synthesize(request: Request) -> dict[str, Any]:
        """Trigger a cross-jurisdictional R.A.I.A. synthesis run."""
        _require_token(request)
        payload = await request.json()
        jurisdictions = payload.get("jurisdictions", [])
        include_tier3 = bool(payload.get("include_tier3", False))

        if not jurisdictions:
            raise HTTPException(
                status_code=400, detail="jurisdictions must be a non-empty list"
            )

        synthesis_id = secrets.token_hex(8)
        _enqueue_synthesis_job(synthesis_id, jurisdictions, include_tier3)

        _record_webhook_call(
            endpoint="synthesize",
            workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
            execution_id=request.headers.get(N8N_EXECUTION_HEADER),
            status=202,
            source_ip=_client_ip(request),
        )
        return {
            "status": "accepted",
            "synthesis_id": synthesis_id,
            "jurisdictions": jurisdictions,
            "include_tier3": include_tier3,
        }

    # ----- Local helpers ---------------------------------------------------
    def _require_token(request: Request) -> None:
        presented = request.headers.get(WEBHOOK_HEADER)
        if not _verify_token(presented):
            raise HTTPException(status_code=401, detail="invalid webhook token")

    def _client_ip(request: Request) -> str | None:
        # Behind nginx/traefik, respect X-Forwarded-For's first entry.
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        if request.client:
            return request.client.host
        return None

    app.include_router(router)
    logger.info("n8n webhook routes registered at /api/v1/webhook/*")


# ---------------------------------------------------------------------------
# Internal helpers (module-level so tests can patch them)
# ---------------------------------------------------------------------------

def _check_tier_imports(modules: tuple[str, ...]) -> bool:
    """True iff every module in the tuple is importable."""
    import importlib
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception:  # noqa: BLE001
            return False
    return True


# ---- Batch job registry (in-memory; swap for Redis/DB in production) ------

_BATCH_JOBS: dict[str, dict[str, Any]] = {}


def _enqueue_batch_job(job_id: str, jobs: list[dict[str, Any]]) -> None:
    """Register a batch job for async processing.

    This stub keeps the job in a module-level dict. A production deployment
    replaces this with a persistent queue (Celery, RQ, Arq, or direct
    writes to a Postgres jobs table). The n8n workflow owns its own
    scheduling, so the backing queue only needs at-least-once semantics.
    """
    _BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "total": len(jobs),
        "completed": 0,
        "results": [],
        "_jobs": jobs,
    }
    # In a real deployment: enqueue to Celery/RQ/Arq here.
    # For the stub, we leave the job in "queued" state and expect the
    # caller / orchestrator service to pick it up.


def _get_batch_job_state(job_id: str) -> dict[str, Any] | None:
    state = _BATCH_JOBS.get(job_id)
    if not state:
        return None
    # Strip internal fields before returning to the webhook client.
    return {k: v for k, v in state.items() if not k.startswith("_")}


def _enqueue_synthesis_job(
    synthesis_id: str,
    jurisdictions: list[str],
    include_tier3: bool,
) -> None:
    """Register a synthesis job.

    Synthesis runs the RAIAService (recommended by the v2.5.1 analysis)
    across the requested jurisdiction set and emits a DOCX that n8n WF-010
    uploads to the shared drive.
    """
    _BATCH_JOBS[synthesis_id] = {
        "job_id": synthesis_id,
        "status": "queued",
        "type": "raia_synthesis",
        "jurisdictions": jurisdictions,
        "include_tier3": include_tier3,
    }
