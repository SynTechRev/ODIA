"""n8n Automation proxy routes (v2.7.3 D7).

Thin HTTP proxy between the frontend Automation page and the local n8n
container. Exists because the Automation UI polls two endpoints every
3-8 seconds — letting the browser call n8n directly requires a CORS
opening, a shared API key, and exposes n8n's data model verbatim.
Routing through the ODIA backend lets us:

  * keep n8n on a trusted LAN-only interface;
  * transform n8n's response shape to the exact shapes the frontend
    already expects (WorkflowSummary, ExecutionEvent);
  * return a helpful 503 when the n8n container is down rather than
    a generic browser network error.

Endpoints
---------
    GET  /api/v1/automation/health
        Liveness probe. Forwards to n8n's ``/healthz`` with a 2-second
        timeout. Returns ``{n8n_online, n8n_version, n8n_base_url}``.
        Used by the "Open n8n Editor" button (D8) to gate the link.

    GET  /api/v1/automation/workflows
        Lists n8n workflows. Proxies ``GET /api/v1/workflows`` with the
        ``X-N8N-API-KEY`` header. Response is transformed into the
        frontend's ``WorkflowSummary[]`` shape.

    GET  /api/v1/automation/executions?since=TS&limit=20
        Recent executions, newest first. Proxies
        ``GET /api/v1/executions`` with optional ``startedAfter`` and
        clamped ``limit``. Transformed into ``ExecutionEvent[]``.

    POST /api/v1/automation/workflows/{id}/run
        Toggles workflow activation in n8n. The handoff notes a workflow
        may be triggered either by activation or by direct execution;
        this endpoint delegates to activate which is the stable public-API
        surface across n8n versions.

Environment
-----------
    N8N_BASE_URL  default: ``http://localhost:5678``
    N8N_API_KEY   the API key from n8n's "Settings → API" page.

When ``N8N_API_KEY`` is unset the workflow / execution / run endpoints
return 503 immediately rather than hitting n8n; /health still works
(healthz is unauthenticated) so the frontend can tell operators the
container itself is reachable.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException, Query

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore
    HTTPException = None  # type: ignore
    Query = None  # type: ignore

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False
    httpx = None  # type: ignore


N8N_BASE_URL_ENV = "N8N_BASE_URL"
N8N_API_KEY_ENV = "N8N_API_KEY"
_DEFAULT_N8N_BASE_URL = "http://localhost:5678"
_HEALTH_TIMEOUT_S = 2.0
_LIST_TIMEOUT_S = 5.0


def _n8n_base_url() -> str:
    return os.environ.get(N8N_BASE_URL_ENV, _DEFAULT_N8N_BASE_URL).rstrip("/")


def _n8n_api_key() -> str | None:
    key = os.environ.get(N8N_API_KEY_ENV, "").strip()
    return key or None


def _n8n_headers() -> dict[str, str]:
    key = _n8n_api_key()
    return {"X-N8N-API-KEY": key} if key else {}


# ---------------------------------------------------------------------------
# Response transformers — map n8n shapes to the frontend's expected shapes
# ---------------------------------------------------------------------------


def _transform_workflow(n8n_wf: dict[str, Any]) -> dict[str, Any]:
    """Transform a single n8n workflow object to WorkflowSummary shape.

    n8n returns: {id, name, active, createdAt, updatedAt, tags, ...}
    Frontend expects: {id, name, description, active, status, lastRun,
    nextRun, lastExecutionId}
    """
    tags = n8n_wf.get("tags") or []
    tag_names = [t.get("name") for t in tags if isinstance(t, dict)]
    description = (
        " · ".join(t for t in tag_names if t)
        or n8n_wf.get("description")
        or "n8n workflow"
    )
    active = bool(n8n_wf.get("active"))
    return {
        "id": str(n8n_wf.get("id", "")),
        "name": n8n_wf.get("name", "(unnamed)"),
        "description": description,
        "active": active,
        "status": "idle" if active else "unavailable",
        "lastRun": n8n_wf.get("updatedAt"),
        "nextRun": None,
        "lastExecutionId": None,
    }


def _transform_execution(n8n_ex: dict[str, Any]) -> dict[str, Any]:
    """Transform a single n8n execution object to ExecutionEvent shape.

    n8n returns: {id, workflowId, finished, stoppedAt, startedAt, status,
    mode, ...}
    Frontend expects: {ts, workflow_id, execution_id, level, message}
    """
    status = str(n8n_ex.get("status") or "").lower()
    level = "info"
    if status in {"error", "failed"}:
        level = "error"
    elif status in {"success"} or bool(n8n_ex.get("finished")):
        level = "success"
    elif status in {"waiting", "running"}:
        level = "info"
    mode = n8n_ex.get("mode") or "manual"
    return {
        "ts": n8n_ex.get("stoppedAt") or n8n_ex.get("startedAt") or "",
        "workflow_id": str(n8n_ex.get("workflowId", "")),
        "execution_id": str(n8n_ex.get("id", "")),
        "level": level,
        "message": f"{mode} · status={status or 'unknown'}",
    }


# ---------------------------------------------------------------------------
# Route registrar
# ---------------------------------------------------------------------------


def register_automation_routes(app: Any) -> None:
    """Attach the n8n automation proxy router to a FastAPI app."""
    if not _FASTAPI_AVAILABLE:
        logger.warning(
            "FastAPI not installed — automation routes will not be registered."
        )
        return
    if not _HTTPX_AVAILABLE:
        logger.warning(
            "httpx not installed — automation routes will not be registered."
        )
        return

    router = APIRouter(tags=["automation", "n8n"])

    # ---- Health probe -----------------------------------------------------
    @router.get("/api/v1/automation/health")
    async def automation_health() -> dict[str, Any]:
        """Reports whether the n8n container is reachable."""
        base = _n8n_base_url()
        out: dict[str, Any] = {
            "n8n_online": False,
            "n8n_version": None,
            "n8n_base_url": base,
            "api_key_configured": _n8n_api_key() is not None,
        }
        try:
            async with httpx.AsyncClient(timeout=_HEALTH_TIMEOUT_S) as cli:
                resp = await cli.get(f"{base}/healthz")
                if resp.status_code == 200:
                    out["n8n_online"] = True
                    try:
                        body = resp.json()
                        if isinstance(body, dict):
                            # n8n's /healthz typically returns {status: 'ok'};
                            # some versions include {version: 'x.y.z'}.
                            out["n8n_version"] = body.get("version")
                    except ValueError:
                        pass
        except Exception as exc:  # noqa: BLE001 — best-effort health probe
            logger.debug("n8n health probe failed: %s", exc)
        return out

    # ---- Workflows list ---------------------------------------------------
    @router.get("/api/v1/automation/workflows")
    async def automation_workflows() -> list[dict[str, Any]]:
        """Returns the n8n workflow roster in frontend WorkflowSummary shape."""
        if _n8n_api_key() is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "N8N_API_KEY not configured — set the env var from "
                    "n8n Settings → API before loading this page."
                ),
            )
        base = _n8n_base_url()
        try:
            async with httpx.AsyncClient(timeout=_LIST_TIMEOUT_S) as cli:
                resp = await cli.get(
                    f"{base}/api/v1/workflows",
                    headers=_n8n_headers(),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("n8n workflows proxy failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail=(
                    f"n8n unreachable — is the container running at {base}?"
                ),
            ) from exc

        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"n8n returned HTTP {resp.status_code} for /api/v1/workflows"
                ),
            )
        body = resp.json()
        items = body.get("data") if isinstance(body, dict) else body
        if not isinstance(items, list):
            return []
        return [_transform_workflow(w) for w in items if isinstance(w, dict)]

    # ---- Executions list --------------------------------------------------
    @router.get("/api/v1/automation/executions")
    async def automation_executions(
        since: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> list[dict[str, Any]]:
        """Returns recent n8n executions as ExecutionEvent[]."""
        if _n8n_api_key() is None:
            raise HTTPException(
                status_code=503,
                detail="N8N_API_KEY not configured — cannot query executions.",
            )
        base = _n8n_base_url()
        params: dict[str, Any] = {"limit": limit}
        if since:
            # Normalise to ISO if the caller fed a plain datetime string.
            try:
                parsed = datetime.fromisoformat(since.replace("Z", "+00:00"))
                params["startedAfter"] = parsed.isoformat()
            except (TypeError, ValueError):
                params["startedAfter"] = since  # pass through

        try:
            async with httpx.AsyncClient(timeout=_LIST_TIMEOUT_S) as cli:
                resp = await cli.get(
                    f"{base}/api/v1/executions",
                    headers=_n8n_headers(),
                    params=params,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("n8n executions proxy failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail=(
                    f"n8n unreachable — is the container running at {base}?"
                ),
            ) from exc

        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"n8n returned HTTP {resp.status_code} for /executions",
            )
        body = resp.json()
        items = body.get("data") if isinstance(body, dict) else body
        if not isinstance(items, list):
            return []
        return [_transform_execution(e) for e in items if isinstance(e, dict)]

    # ---- Manual trigger ---------------------------------------------------
    @router.post("/api/v1/automation/workflows/{workflow_id}/run")
    async def automation_run_workflow(workflow_id: str) -> dict[str, Any]:
        """Activates (or keeps active) a workflow so its trigger can fire.

        n8n's public API exposes activation rather than one-shot execution;
        for workflow-internal manual triggers the frontend typically pairs
        the activate call with an immediate webhook POST. We return the
        activate response verbatim and let the caller decide.
        """
        if _n8n_api_key() is None:
            raise HTTPException(
                status_code=503,
                detail="N8N_API_KEY not configured — cannot trigger workflow.",
            )
        base = _n8n_base_url()
        try:
            async with httpx.AsyncClient(timeout=_LIST_TIMEOUT_S) as cli:
                resp = await cli.post(
                    f"{base}/api/v1/workflows/{workflow_id}/activate",
                    headers=_n8n_headers(),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("n8n activate proxy failed: %s", exc)
            raise HTTPException(
                status_code=503,
                detail=(
                    f"n8n unreachable — is the container running at {base}?"
                ),
            ) from exc

        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=502,
                detail=(
                    f"n8n returned HTTP {resp.status_code} for activate "
                    f"(workflow {workflow_id})"
                ),
            )
        try:
            body = resp.json()
        except ValueError:
            body = {}
        return {
            "status": "triggered",
            "workflow_id": workflow_id,
            "n8n_response": body,
        }

    app.include_router(router)
    logger.info("n8n automation routes registered at /api/v1/automation/*")


__all__ = [
    "register_automation_routes",
    "_transform_workflow",
    "_transform_execution",
]
