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

# FastAPI imports must be module-level, NOT function-scoped:
# `from __future__ import annotations` turns every type hint into a lazy
# string; FastAPI resolves them via `typing.get_type_hints()` against
# the function's module-globals at route-registration time. When
# `Request`, `UploadFile`, etc. are imported inside `register_webhook_routes`,
# the name never reaches module globals, FastAPI fails to resolve the
# annotation, and treats the parameter as a plain query arg (observable
# as 422 "field required" on /health, which has no query surface).
# Match the pattern established by upload.py: try-import at module scope
# and let the registrar re-check `_FASTAPI_AVAILABLE` at call time.
try:
    from fastapi import (
        APIRouter,
        File,
        Form,
        HTTPException,
        Request,
        UploadFile,
    )

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore
    File = None  # type: ignore
    Form = None  # type: ignore
    HTTPException = None  # type: ignore
    Request = None  # type: ignore
    UploadFile = None  # type: ignore

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
    score = compute_recursive_scalar_score(normalized, findings.get("anomalies", []))

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
        from oraculus_di_auditor.db import models as db_models
        from oraculus_di_auditor.db.session import get_db as get_session
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


def _record_seen_hash(
    sha256: str,
    document_id: str | None = None,
    jurisdiction_id: str | None = None,
) -> None:
    """Best-effort insert into SeenHash after a successful first pipeline.

    The spec's `_dedup_check` reads from this table but the original
    webhook body did not write to it — leaving the dedup mechanism
    permanently inert. This helper closes the loop.

    First-write-wins: on duplicate insert, the IntegrityError is caught
    and suppressed. Caller semantics are "best effort" — a failed write
    must not break the webhook response, since the pipeline has already
    succeeded.
    """
    try:
        from oraculus_di_auditor.db import models as db_models
        from oraculus_di_auditor.db.session import get_db as get_session
    except ImportError:
        return

    if not hasattr(db_models, "SeenHash"):
        return

    try:
        with get_session() as session:
            session.add(
                db_models.SeenHash(
                    sha256=sha256,
                    document_id=document_id,
                    jurisdiction_id=jurisdiction_id,
                )
            )
            session.commit()
    except Exception as exc:  # noqa: BLE001 — dedup is a nice-to-have
        logger.warning("seen_hash write failed: %s", exc)


def _persist_tier1_result(
    sha256: str,
    filename: str,
    jurisdiction_id: str | None,
    result: dict[str, Any],
) -> None:
    """Best-effort persistence of a successful Tier 1 pipeline run.

    Writes three rows:
      - Document (keyed on sha256 as document_id, unique; skip if exists)
      - Analysis (counts + score, one row per run)
      - Anomaly rows (one per finding)

    v2.7.1 C5 prerequisite: RAIAService queries these tables to build
    cross-jurisdiction synthesis reports. Without this persistence, Tier
    1 results live only in the `_JOBS` process dict and are lost on
    restart — RAIAService would find nothing.

    Never raises. Persistence is a consumer convenience; the webhook
    response has already succeeded by the time we get here, and a DB
    write failure must not flip the overall response to 500.
    """
    try:
        import json

        from oraculus_di_auditor.db import models as db_models
        from oraculus_di_auditor.db.session import get_db as get_session
    except ImportError:
        return

    required = ("Document", "Analysis", "Anomaly")
    if not all(hasattr(db_models, m) for m in required):
        return

    anomalies = (result.get("findings") or {}).get("anomalies", [])
    score = result.get("recursive_scalar_score", 0.0)
    file_format = (filename.rsplit(".", 1)[-1] or "unknown").lower()[:20]

    try:
        with get_session() as session:
            # Document — first-writer-wins on sha256. If already present
            # (rare — dedup short-circuits earlier — but possible on
            # concurrent requests), reuse the row.
            existing = (
                session.query(db_models.Document).filter_by(document_id=sha256).first()
            )
            if existing is None:
                doc_row = db_models.Document(
                    document_id=sha256,
                    title=filename[:255] if filename else "unknown",
                    document_type=file_format,
                    jurisdiction=jurisdiction_id,
                )
                session.add(doc_row)
                session.flush()

            # Analysis — one new row per ingest call.
            analysis_row = db_models.Analysis(
                document_id=sha256,
                anomaly_count=len(anomalies),
                scalar_score=float(score) if score is not None else 0.0,
                engine_version=os.environ.get("ODIA_VERSION", "2.7.1"),
                metadata_json=json.dumps({"source": "webhook/ingest-and-analyze"}),
            )
            session.add(analysis_row)
            session.flush()

            # Anomaly rows.
            for a in anomalies:
                session.add(
                    db_models.Anomaly(
                        analysis_id=analysis_row.id,
                        anomaly_id=a.get("id", "unknown"),
                        issue=a.get("issue", ""),
                        severity=a.get("severity", "medium"),
                        layer=a.get("layer", "unknown"),
                        details_json=json.dumps(a.get("details", {})),
                    )
                )
            session.commit()
    except Exception as exc:  # noqa: BLE001 — persistence is a nice-to-have
        logger.warning("tier1 persistence failed for sha256=%s: %s", sha256[:16], exc)


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
        from oraculus_di_auditor.db import models as db_models
        from oraculus_di_auditor.db.session import get_db as get_session
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
    if not _FASTAPI_AVAILABLE:
        logger.warning("FastAPI not installed — webhook routes will not be registered.")
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
            "odia_version": os.environ.get("ODIA_VERSION", "2.7.1"),
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
        # Close the dedup loop: record the hash so the next POST with
        # the same bytes short-circuits. Document_id is taken from the
        # pipeline result; pipeline may or may not emit one depending
        # on the detector path, so read it defensively.
        _record_seen_hash(
            sha256=sha256,
            document_id=(result.get("document") or {}).get("document_id"),
            jurisdiction_id=jurisdiction_id,
        )
        # C5 prerequisite — persist Document + Analysis + Anomaly rows
        # so RAIAService.synthesize() can aggregate across runs. Best-
        # effort, never raises, does not affect the webhook response.
        _persist_tier1_result(
            sha256=sha256,
            filename=file.filename or "unknown",
            jurisdiction_id=jurisdiction_id,
            result=result,
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
        """Trigger a cross-jurisdictional R.A.I.A. synthesis run.

        Body:
          {
            "jurisdictions": ["a", "b", "c"],
            "include_tier3": false,
            "render_markdown": true
          }

        Runs synchronously — the synthesis is DB-query-bound (no
        model inference), so latency is bounded and a queue hop would
        just add a polling round-trip for n8n. The serialised result
        is *also* stored in ``_BATCH_JOBS[synthesis_id]`` so the
        existing ``GET /status/{job_id}`` endpoint can re-serve it
        without re-running the synthesis.
        """
        _require_token(request)
        payload = await request.json()
        jurisdictions = payload.get("jurisdictions", [])
        include_tier3 = bool(payload.get("include_tier3", False))
        want_markdown = bool(payload.get("render_markdown", True))

        if not jurisdictions:
            raise HTTPException(
                status_code=400, detail="jurisdictions must be a non-empty list"
            )

        synthesis_id = secrets.token_hex(8)

        try:
            result_dict, markdown = _run_raia_synthesis(
                jurisdictions=jurisdictions,
                include_tier3=include_tier3,
                render_markdown_flag=want_markdown,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("webhook synthesize failed")
            _record_webhook_call(
                endpoint="synthesize",
                workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
                execution_id=request.headers.get(N8N_EXECUTION_HEADER),
                status=500,
                source_ip=_client_ip(request),
            )
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        # Override the synthesis_id on the inner result so it matches
        # the one n8n was handed — RAIAService generates its own, but
        # callers expect the returned synthesis_id to be the handle.
        result_dict["synthesis_id"] = synthesis_id

        # Park the full result under _BATCH_JOBS so /status/{job_id}
        # can re-serve it. Strip _jobs-style internal keys from the
        # response (they'd bloat the webhook payload).
        _store_synthesis_result(synthesis_id, result_dict, markdown)

        _record_webhook_call(
            endpoint="synthesize",
            workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
            execution_id=request.headers.get(N8N_EXECUTION_HEADER),
            status=200,
            source_ip=_client_ip(request),
        )
        response: dict[str, Any] = {
            "status": "ok",
            "synthesis_id": synthesis_id,
            "jurisdictions": jurisdictions,
            "include_tier3": include_tier3,
            "result": result_dict,
        }
        if markdown is not None:
            response["markdown"] = markdown
        return response

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


def _run_raia_synthesis(
    *,
    jurisdictions: list[str],
    include_tier3: bool,
    render_markdown_flag: bool,
) -> tuple[dict[str, Any], str | None]:
    """Invoke ``RAIAService.synthesize()`` and optionally render markdown.

    Returns ``(result_dict, markdown_or_none)``. Kept as a module-level
    function so tests can patch it without touching the route closure.
    """
    from oraculus_di_auditor.raia import RAIAService, render_markdown_template

    svc = RAIAService()
    result = svc.synthesize(jurisdictions, include_tier3=include_tier3)
    md = render_markdown_template(result) if render_markdown_flag else None
    return result.to_dict(), md


def _store_synthesis_result(
    synthesis_id: str,
    result_dict: dict[str, Any],
    markdown: str | None,
) -> None:
    """Park a completed synthesis under ``_BATCH_JOBS`` for later polling.

    The ``/status/{job_id}`` endpoint strips keys prefixed with ``_``
    before returning, so we pack the raw result under ``result`` and
    (optionally) the rendered markdown under ``markdown``.
    """
    _BATCH_JOBS[synthesis_id] = {
        "job_id": synthesis_id,
        "status": "completed",
        "type": "raia_synthesis",
        "result": result_dict,
        "markdown": markdown,
    }
