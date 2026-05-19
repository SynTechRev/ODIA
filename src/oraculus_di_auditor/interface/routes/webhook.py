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
import threading
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


def _user_token_path() -> Path:
    """Per-user writable file backing the webhook token.

    Lives next to the seeded jurisdictions under ``<user_data_root>/``
    so the desktop installer's user-data directory holds all runtime
    state in one place.  See
    ``config.jurisdiction_loader._user_data_root`` for the platform-
    specific path resolution.
    """
    from oraculus_di_auditor.config.jurisdiction_loader import _user_data_root

    return _user_data_root() / "webhook_token"


def _resolve_webhook_token() -> tuple[str | None, str | None]:
    """Resolve the active webhook token + its source.

    Order of precedence:
        1. ``ODIA_WEBHOOK_TOKEN`` environment variable
        2. ``<user_data_root>/webhook_token`` file (managed via the
           Settings UI's "Automation Webhook" card)

    Returns ``(token, source)`` where ``source`` is ``"env"``,
    ``"file"``, or ``None`` if no token is configured anywhere.
    """
    env_value = os.environ.get(WEBHOOK_TOKEN_ENV, "").strip()
    if env_value:
        return env_value, "env"
    try:
        path = _user_token_path()
        if path.exists():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value, "file"
    except OSError:
        # Disk read failure — fall through to "not configured" rather
        # than crash route registration. The user can re-set the token
        # via the Settings UI.
        logger.warning("Failed to read webhook token file at %s", _user_token_path())
    return None, None


def _verify_token(presented: str | None) -> bool:
    """Constant-time comparison of the webhook token.

    Returns False if no token is configured anywhere (env or file)
    or if the presented value is missing.
    """
    expected, _ = _resolve_webhook_token()
    if not expected or not presented:
        return False
    return hmac.compare_digest(expected.encode(), presented.encode())


def _token_configured() -> bool:
    token, _ = _resolve_webhook_token()
    return bool(token)


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
                engine_version=os.environ.get("ODIA_VERSION", "3.2.3"),
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

    # v2.10.x — register unconditionally. The per-endpoint `_require_token`
    # check below is the real security wall. Registering the routes only
    # when the env var was set at startup made the Settings-page token UI
    # impossible (the routes wouldn't exist for `_require_token` to gate),
    # and made every fresh install fail loud at /webhook/health with 404
    # instead of the documented 401-on-bad-token contract.
    if not _token_configured():
        logger.warning(
            "%s is not set (env or %s). Webhook routes will register but "
            "every authenticated endpoint will return 401 until a token "
            "is configured via the Settings UI or environment.",
            WEBHOOK_TOKEN_ENV,
            _user_token_path(),
        )

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
            "webhook_token_configured": _token_configured(),
            "odia_version": os.environ.get("ODIA_VERSION", "3.2.3"),
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

    # ---- Scrape + ingest (URL → audit, server-side download) ---------------
    @router.post("/api/v1/webhook/scrape-and-ingest")
    async def webhook_scrape_and_ingest(request: Request) -> dict[str, Any]:
        """Download a URL server-side and run the Tier 1 audit on it.

        Why this exists (v3.0.2 — "Backend-Side Scraping"):
            Real-world scraping pipelines hit two recurring problems when
            n8n's HTTP Request node tries to download directly:

              1. Cloudflare-fronted public-records sites (very common for
                 CivicPlus / Granicus / Legistar) inspect the TLS fingerprint
                 of the client. Node.js's TLS stack has a well-known JA3
                 hash that bot-protection rules block. Same request from
                 Python's urllib / requests is accepted because the OpenSSL
                 fingerprint is different.

              2. n8n's recent shift to hardened distroless-style images
                 strips out shell-execution node types (Execute Command)
                 AND the curl binary, which were the natural workarounds.

            Routing the download through this endpoint sidesteps both —
            Python downloads the file, runs the audit, persists the rows,
            and returns the finding payload n8n would have built itself.
            n8n's job becomes trivial: POST a list of URLs.

        Body (JSON):
            {
              "url": "https://www.visalia.gov/AgendaCenter/ViewFile/...",
              "jurisdiction_id": "visalia",
              "filename_hint": "visalia_agenda_05062026-821.pdf"   # optional
            }

        Returns the same payload shape as /webhook/ingest-and-analyze so
        n8n / external orchestrators can treat them interchangeably:
            {
              "status": "ok",
              "already_seen": bool,
              "url": "...",
              "sha256": "...",
              "document": {...},
              "findings": {"count": N, "anomalies": [...]},
              "recursive_scalar_score": float,
              "tier": 1
            }
        """
        _require_token(request)

        payload = await request.json()
        url = (payload.get("url") or "").strip()
        jurisdiction_id = (payload.get("jurisdiction_id") or "").strip()
        filename_hint = (payload.get("filename_hint") or "").strip()

        if not url or not url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail="`url` must be an absolute http(s) URL",
            )
        if not jurisdiction_id:
            raise HTTPException(
                status_code=400,
                detail="`jurisdiction_id` is required",
            )

        # Download server-side. urllib uses Python's TLS stack, whose JA3
        # fingerprint differs from Node's — Cloudflare typically accepts it
        # where it would block n8n's HTTP node. Browser-like headers help
        # for extra Cloudflare rules that gate on Accept-* values.
        import urllib.error
        import urllib.request

        browser_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            req = urllib.request.Request(url, headers=browser_headers)
            with urllib.request.urlopen(
                req, timeout=120
            ) as response:  # noqa: S310 — validated http(s) prefix above
                file_bytes = response.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            _record_webhook_call(
                endpoint="scrape-and-ingest",
                workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
                execution_id=request.headers.get(N8N_EXECUTION_HEADER),
                status=502,
                source_ip=_client_ip(request),
            )
            raise HTTPException(
                status_code=502,
                detail=f"Upstream download failed: {exc}",
            ) from exc

        if not file_bytes:
            raise HTTPException(
                status_code=502,
                detail="Upstream returned an empty body",
            )

        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Early-exit on dedup — same logic as /webhook/ingest-and-analyze.
        if _dedup_check(sha256):
            _record_webhook_call(
                endpoint="scrape-and-ingest",
                workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
                execution_id=request.headers.get(N8N_EXECUTION_HEADER),
                status=200,
                source_ip=_client_ip(request),
            )
            return {
                "status": "ok",
                "already_seen": True,
                "url": url,
                "sha256": sha256,
                "jurisdiction_id": jurisdiction_id,
            }

        # Derive a filename for the persisted Document row. Prefer the
        # caller's hint; otherwise pull the URL tail; otherwise fall back
        # to the SHA prefix so we always have a useful title.
        filename = filename_hint or url.rsplit("/", 1)[-1] or f"scraped_{sha256[:12]}"
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"

        try:
            result = _run_tier1_pipeline(
                file_bytes=file_bytes,
                filename=filename,
                jurisdiction_id=jurisdiction_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("webhook scrape-and-ingest failed")
            _record_webhook_call(
                endpoint="scrape-and-ingest",
                workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
                execution_id=request.headers.get(N8N_EXECUTION_HEADER),
                status=500,
                source_ip=_client_ip(request),
            )
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        _record_webhook_call(
            endpoint="scrape-and-ingest",
            workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
            execution_id=request.headers.get(N8N_EXECUTION_HEADER),
            status=200,
            source_ip=_client_ip(request),
        )
        _record_seen_hash(
            sha256=sha256,
            document_id=(result.get("document") or {}).get("document_id"),
            jurisdiction_id=jurisdiction_id,
        )
        _persist_tier1_result(
            sha256=sha256,
            filename=filename,
            jurisdiction_id=jurisdiction_id,
            result=result,
        )
        return {
            "status": "ok",
            "already_seen": False,
            "url": url,
            **result,
        }

    # ---- Scrape + ingest, async (v3.0.3) ----------------------------------
    @router.post("/api/v1/webhook/scrape-and-ingest-async")
    async def webhook_scrape_and_ingest_async(request: Request) -> dict[str, Any]:
        """Fire-and-forget variant of /scrape-and-ingest. Returns 202 + job_id.

        Why this exists (v3.0.3):
            Synchronous /scrape-and-ingest blocks the HTTP connection for
            the full download + audit duration. Large agenda packets push
            past n8n's 180s HTTP node timeout and the request dies even
            though the backend was still working. This variant queues the
            work onto a daemon thread and hands the caller a poll URL —
            n8n's Wait node + Loop pattern is the natural consumer.

        Body (JSON): identical to /scrape-and-ingest.

        Returns:
            {
              "status":   "accepted",
              "job_id":   "...",
              "url":      "...",
              "poll_url": "/api/v1/webhook/status/{job_id}"
            }
        """
        _require_token(request)

        payload = await request.json()
        url = (payload.get("url") or "").strip()
        jurisdiction_id = (payload.get("jurisdiction_id") or "").strip()
        filename_hint = (payload.get("filename_hint") or "").strip()

        if not url or not url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=400,
                detail="`url` must be an absolute http(s) URL",
            )
        if not jurisdiction_id:
            raise HTTPException(
                status_code=400,
                detail="`jurisdiction_id` is required",
            )

        job_id = secrets.token_hex(8)
        _enqueue_scrape_job(job_id, url, jurisdiction_id, filename_hint)

        _record_webhook_call(
            endpoint="scrape-and-ingest-async",
            workflow_id=request.headers.get(N8N_WORKFLOW_HEADER),
            execution_id=request.headers.get(N8N_EXECUTION_HEADER),
            status=202,
            source_ip=_client_ip(request),
        )

        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "job_id": job_id,
                "url": url,
                "poll_url": f"/api/v1/webhook/status/{job_id}",
            },
        )

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
            # v3.0.5: pass the route-assigned synthesis_id INTO
            # _run_raia_synthesis so it's applied to the RAIAResult
            # BEFORE markdown rendering. The pre-v3.0.5 code overrode
            # result_dict["synthesis_id"] AFTER markdown was already
            # rendered with RAIAService's internally-generated ID,
            # causing the rendered .md to disagree with the JSON's
            # synthesis_id (cosmetic but confusing for operators).
            result_dict, markdown = _run_raia_synthesis(
                jurisdictions=jurisdictions,
                include_tier3=include_tier3,
                render_markdown_flag=want_markdown,
                synthesis_id_override=synthesis_id,
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


# ---- Async scrape job runner (v3.0.3, hardened in v3.0.4) -----------------
#
# Why this exists: real-world public-records PDFs routinely take 60-180s to
# audit end-to-end (large agenda packets, OCR-heavy scans). n8n's HTTP node
# defaults to ~180s and refuses to wait longer without per-node tuning. The
# synchronous /scrape-and-ingest endpoint (v3.0.2) hit this ceiling on
# Visalia item 12 — an 18MB agenda packet. The async variant flips the
# control inversion: the endpoint accepts the URL, registers a job, kicks
# off a daemon thread to do the work, and returns 202 immediately. n8n
# polls /status/{job_id} until the job reports completed/failed.
#
# v3.0.4 hardening: real-world Visalia first-light fired all 84 jobs in
# near-parallel, which surfaced two issues. (1) Cloudflare in front of
# visalia.gov TCP-reset some connections under that concurrency, raising
# http.client.RemoteDisconnected. That's a ConnectionResetError → OSError,
# NOT a urllib.error.URLError — so it escaped the original except clause
# and crashed the worker thread, leaving the job stuck at "downloading"
# in the registry. The catch is now widened to include OSError. (2) The
# upstream rate-limit signal said we were being impolite. _DOWNLOAD_SEMAPHORE
# caps concurrent outbound downloads at _DOWNLOAD_CONCURRENCY regardless of
# how fast n8n enqueues. The semaphore only wraps the network read; audit
# work continues in parallel.
#
# Threading note: db.session opens SQLite with check_same_thread=False, so
# the worker can use the same get_db() context manager from a non-request
# thread. The job registry (_BATCH_JOBS) is process-local; a real
# multi-worker deployment would back this with Redis or a jobs table.

_DOWNLOAD_CONCURRENCY = 4
_DOWNLOAD_SEMAPHORE = threading.Semaphore(_DOWNLOAD_CONCURRENCY)

# v3.1.0 — common browser headers used by both fetcher tiers. Defined at
# module scope so tests can monkeypatch them without reaching into the
# worker function.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# HTTP status codes that v3.1.0 reads as "Tier-1 was blocked, try Tier-2".
# 403 covers Akamai/Cloudflare Bot Manager rejects of Python urllib's
# TLS fingerprint (observed live against tulare.ca.gov). 429 covers
# rate-limit responses that the throttled Tier-2 may have better luck on.
# Other 4xx (404, 401) propagate normally — they are real upstream errors,
# not bot-mitigation.
_TIER1_FALLBACK_HTTP_CODES = frozenset({403, 429})


def _fetch_url(url: str, *, timeout: int = 120) -> bytes:
    """Two-tier URL fetcher for fingerprint-resistant scraping (v3.1.0).

    Tier 1 — ``urllib.request.urlopen`` with browser-like headers.
        Fast, dep-free, succeeds against ~80% of public-records sites
        (Revize, most CivicPlus, basic Cloudflare). Python's OpenSSL JA3
        fingerprint passes most filters that block Node.js. This is the
        v3.0.x default path; keeping it as Tier 1 means common-case
        scraping pays no overhead.

    Tier 2 — ``curl_cffi`` with Chrome impersonation.
        Activated when Tier 1 returns 403/429 (Akamai/Cloudflare Bot
        Manager pattern) or fails with a connection-class ``OSError``
        (TLS handshake reset, server hangup mid-response). curl_cffi
        ships libcurl-impersonate which replicates Chrome's exact
        TLS+HTTP2 fingerprint, defeating JA3/JA4 + HTTP/2 frame-order
        inspection. Observed live against tulare.ca.gov / AkamaiGHost
        which 403s every Python urllib variant we tried.

    Returns the response body as bytes on success from either tier.
    Raises ``OSError`` on both-tier failure — caller can catch it
    alongside other connection-class exceptions (matches the v3.0.4
    OSError catch pattern in the scrape worker).

    ``curl_cffi`` is imported lazily so a non-scraping deployment (or a
    minimal wheel) that omits it can still import this module. If the
    import fails AND Tier 1 also failed, the original Tier-1 exception
    is re-raised (so the operator sees the real underlying problem,
    not a misleading "tier-2 not installed" trail).
    """
    import urllib.error
    import urllib.request

    # --- Tier 1: urllib (current v3.0.x behaviour) ----------------------
    tier1_error: Exception | None = None
    try:
        req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
        with urllib.request.urlopen(
            req, timeout=timeout
        ) as response:  # noqa: S310 — caller validated http(s) prefix
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code not in _TIER1_FALLBACK_HTTP_CODES:
            raise
        tier1_error = exc
        logger.info(
            "tier-1 fetcher got HTTP %s for %s; trying tier-2 (curl_cffi)",
            exc.code,
            url,
        )
    except OSError as exc:
        # Connection-class failure (TLS reset, RemoteDisconnected, DNS,
        # timeout). Tier 2 with a real-browser fingerprint may succeed.
        tier1_error = exc
        logger.info(
            "tier-1 fetcher OSError for %s (%s); trying tier-2 (curl_cffi)",
            url,
            exc.__class__.__name__,
        )

    # --- Tier 2: curl_cffi Chrome impersonation -------------------------
    try:
        from curl_cffi import requests as curl_requests
    except ImportError:
        logger.warning(
            "curl_cffi unavailable — cannot fall through to tier-2; "
            "re-raising tier-1 error"
        )
        # Re-raise the original tier-1 failure (keeps its traceback);
        # `from None` because the ImportError is incidental, not the
        # operational cause the operator needs to see.
        raise tier1_error from None

    try:
        resp = curl_requests.get(
            url,
            headers=_BROWSER_HEADERS,
            impersonate="chrome131",
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 — curl_cffi raises its own classes
        # Wrap as OSError so the worker's existing OSError catch handles
        # it uniformly with tier-1 failures.
        raise OSError(
            f"tier-2 (curl_cffi) failed: {exc} " f"(tier-1 had: {tier1_error})"
        ) from exc

    if not resp.ok:
        raise OSError(
            f"tier-2 (curl_cffi) got HTTP {resp.status_code} "
            f"(tier-1 had: {tier1_error})"
        )

    return resp.content


def _run_scrape_job_background(
    job_id: str,
    url: str,
    jurisdiction_id: str,
    filename_hint: str,
) -> None:
    """Worker for /scrape-and-ingest-async. Mutates ``_BATCH_JOBS[job_id]``.

    Phases (mirrored into ``state['status']`` so pollers can observe progress):
        queued → downloading → auditing → completed | failed
    """
    state = _BATCH_JOBS.get(job_id)
    if state is None:
        logger.warning("scrape job %s missing from registry — aborting", job_id)
        return

    state["status"] = "downloading"
    try:
        # v3.1.0: delegated to _fetch_url which transparently falls back
        # from urllib (tier 1) to curl_cffi Chrome impersonation (tier 2)
        # on 403/429 or OSError — defeats Akamai/Cloudflare bot blocks
        # that pre-v3.1.0 caused permanent download failure. Semaphore
        # wraps the WHOLE fetch attempt so concurrency is throttled
        # regardless of which tier ends up serving the request.
        with _DOWNLOAD_SEMAPHORE:
            file_bytes = _fetch_url(url)
    except OSError as exc:
        # Covers all tier-1/tier-2 failures: urllib.error.URLError,
        # HTTPError, TimeoutError, http.client.RemoteDisconnected,
        # curl_cffi exception classes (wrapped to OSError in _fetch_url),
        # and DNS/connection-reset failures.
        state["status"] = "failed"
        state["error"] = f"Upstream download failed: {exc}"
        return

    if not file_bytes:
        state["status"] = "failed"
        state["error"] = "Upstream returned an empty body"
        return

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    state["sha256"] = sha256

    if _dedup_check(sha256):
        state["status"] = "completed"
        state["already_seen"] = True
        state["result"] = {
            "status": "ok",
            "already_seen": True,
            "url": url,
            "sha256": sha256,
            "jurisdiction_id": jurisdiction_id,
        }
        return

    filename = filename_hint or url.rsplit("/", 1)[-1] or f"scraped_{sha256[:12]}"
    # v3.1.1: honour any extension already on the filename that the
    # ingestion pipeline knows how to parse (PDF, JSON, XML, TXT, HTML).
    # Pre-v3.1.1 force-appended `.pdf` to everything, which routed HTML
    # press releases through the PDF parser → silent failure. If no
    # recognised extension, sniff the first 16 bytes: PDF magic header
    # (%PDF-), HTML opener (<!DOCTYPE / <html), JSON ({ or [) all have
    # distinguishable signatures. Default to .pdf for binary blobs since
    # that matches the v3.0.x scraping-PDFs use case.
    known_exts = {".pdf", ".json", ".xml", ".txt", ".html", ".htm"}
    if Path(filename).suffix.lower() not in known_exts:
        head = file_bytes[:16].lstrip()
        head_lower = head.lower()
        if head.startswith(b"%PDF-"):
            ext = ".pdf"
        elif head_lower.startswith(b"<!doctype") or head_lower.startswith(b"<html"):
            ext = ".html"
        elif head.startswith(b"<?xml"):
            ext = ".xml"
        elif head and head[:1] in (b"{", b"["):
            ext = ".json"
        else:
            ext = ".pdf"  # conservative fallback — preserves v3.0.x behaviour
        filename = f"{filename}{ext}"
    state["filename"] = filename

    state["status"] = "auditing"
    try:
        result = _run_tier1_pipeline(
            file_bytes=file_bytes,
            filename=filename,
            jurisdiction_id=jurisdiction_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("scrape job %s pipeline failed", job_id)
        state["status"] = "failed"
        state["error"] = str(exc)
        return

    _record_seen_hash(
        sha256=sha256,
        document_id=(result.get("document") or {}).get("document_id"),
        jurisdiction_id=jurisdiction_id,
    )
    _persist_tier1_result(
        sha256=sha256,
        filename=filename,
        jurisdiction_id=jurisdiction_id,
        result=result,
    )

    state["status"] = "completed"
    state["already_seen"] = False
    state["result"] = {
        "status": "ok",
        "already_seen": False,
        "url": url,
        **result,
    }


def _enqueue_scrape_job(
    job_id: str,
    url: str,
    jurisdiction_id: str,
    filename_hint: str,
) -> None:
    """Register a scrape job and start its daemon worker thread."""
    _BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "type": "scrape",
        "status": "queued",
        "url": url,
        "jurisdiction_id": jurisdiction_id,
    }
    threading.Thread(
        target=_run_scrape_job_background,
        args=(job_id, url, jurisdiction_id, filename_hint),
        daemon=True,
        name=f"scrape-job-{job_id}",
    ).start()


def _run_raia_synthesis(
    *,
    jurisdictions: list[str],
    include_tier3: bool,
    render_markdown_flag: bool,
    synthesis_id_override: str | None = None,
) -> tuple[dict[str, Any], str | None]:
    """Invoke ``RAIAService.synthesize()`` and optionally render markdown.

    Returns ``(result_dict, markdown_or_none)``. Kept as a module-level
    function so tests can patch it without touching the route closure.

    v3.0.5: ``synthesis_id_override`` lets the route stamp its own
    synthesis_id on the RAIAResult BEFORE markdown rendering. Without
    this override the rendered markdown embeds RAIAService's
    internally-generated ID, which then disagreed with the JSON
    response's synthesis_id (route applied its override later, on the
    already-rendered dict). Optional + None default keeps the signature
    backward-compatible with existing callers and tests.
    """
    from oraculus_di_auditor.raia import RAIAService, render_markdown_template

    svc = RAIAService()
    result = svc.synthesize(jurisdictions, include_tier3=include_tier3)
    if synthesis_id_override:
        result.synthesis_id = synthesis_id_override
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
