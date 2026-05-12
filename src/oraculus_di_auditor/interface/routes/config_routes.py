"""Runtime configuration routes (v2.10.x).

Exposes a small surface for setting runtime-mutable config from the
Settings UI.  The first user is the webhook token: prior to v2.10.x
the token could only be supplied via the ``ODIA_WEBHOOK_TOKEN``
environment variable, which made it effectively un-settable on a
desktop install where the Electron host has no shell to set env vars
in.  Routes here persist the token to ``<user_data_root>/webhook_token``
so the Settings UI can manage it without a backend restart.

Endpoints
---------
    GET  /api/v1/config/webhook-token
        Returns ``{configured: bool, source: "env"|"file"|null}``.
        Never returns the token value itself.

    POST /api/v1/config/webhook-token
        Body: ``{"token": "..."}``.  Empty string clears the token.
        Returns ``{status: "ok", source: "file"|"env"|null}``.
        If the env var is set, the file fallback is shadowed and
        the response notes that the env value still wins.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    APIRouter = None  # type: ignore[assignment]
    HTTPException = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment,misc]


class _WebhookTokenPayload(BaseModel):  # type: ignore[misc,valid-type]
    """Body schema for POST /api/v1/config/webhook-token."""

    token: str


def register_config_routes(app: Any) -> None:
    """Attach runtime-config routes to a FastAPI app."""
    if not _FASTAPI_AVAILABLE:
        logger.warning("FastAPI not installed — config routes will not be registered.")
        return

    router = APIRouter(tags=["config"])

    @router.get("/api/v1/config/webhook-token")
    async def get_webhook_token_status() -> dict[str, Any]:
        """Report whether a webhook token is configured and from where.

        Never returns the value itself — the token is a shared secret
        and the UI has no need to display it.
        """
        from oraculus_di_auditor.interface.routes.webhook import (
            _resolve_webhook_token,
            _user_token_path,
        )

        _, source = _resolve_webhook_token()
        return {
            "configured": source is not None,
            "source": source,
            "file_path": str(_user_token_path()),
            "env_var": "ODIA_WEBHOOK_TOKEN",
        }

    @router.post("/api/v1/config/webhook-token")
    async def set_webhook_token(payload: _WebhookTokenPayload) -> dict[str, Any]:
        """Persist (or clear) the webhook token to disk.

        An empty / whitespace-only token clears the file. The env var
        still wins if it's set; the response surfaces that fact via the
        ``source`` field so the UI can tell the user "your env var is
        shadowing this".
        """
        from oraculus_di_auditor.interface.routes.webhook import (
            WEBHOOK_TOKEN_ENV,
            _resolve_webhook_token,
            _user_token_path,
        )

        path = _user_token_path()
        token = (payload.token or "").strip()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not token:
                # Clear the file. Missing path is fine — already cleared.
                if path.exists():
                    path.unlink()
            else:
                path.write_text(token, encoding="utf-8")
                # Best-effort: tighten POSIX perms to owner-only. No-op on
                # Windows (the call exists but the bits are mostly
                # ignored) — that's acceptable since the user data dir
                # is already user-scoped.
                try:
                    os.chmod(path, 0o600)
                except OSError:
                    pass
        except OSError as exc:
            logger.exception("Failed to write webhook token to %s", path)
            raise HTTPException(
                status_code=500,
                detail=f"Could not persist webhook token: {exc}",
            ) from exc

        _, source = _resolve_webhook_token()
        env_shadows = (
            source == "env"
            and bool(token)
            and os.environ.get(WEBHOOK_TOKEN_ENV, "").strip() != token
        )
        return {
            "status": "ok",
            "source": source,
            "env_shadows_file": env_shadows,
        }

    app.include_router(router)
    logger.info("Runtime-config routes registered at /api/v1/config/*")


__all__ = ["register_config_routes"]
