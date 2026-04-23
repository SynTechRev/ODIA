"""FastAPI routes for the ODIA AI subsystem.

These routes extend the existing oraculus_di_auditor backend (see
src/oraculus_di_auditor/interface/api.py) with AI-specific endpoints
for extraction, feedback submission, registry inspection, and trigger
status.

Integration:
    from odia_ai.server_routes import include_ai_routes
    include_ai_routes(app, config_path=None)

The routes are deliberately dependency-injected: a caller passes in a
config path (or None) and the router loads the configuration and
instantiates services lazily. This avoids boot-time ML imports when
the user has not requested extraction.

Author: ODIA AI Team
License: MIT
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _build_router(config_path: str | None = None):  # -> APIRouter
    """Build the APIRouter lazily. FastAPI is imported inside this function.

    Lazy import means odia_ai can still be imported on systems without
    FastAPI installed (e.g. for running dataset construction only).
    """
    try:
        from fastapi import APIRouter, HTTPException  # type: ignore
        from pydantic import BaseModel, Field  # type: ignore
    except ImportError as e:
        raise ImportError(
            "odia_ai.server_routes requires FastAPI. Install with: "
            "pip install fastapi uvicorn pydantic"
        ) from e

    from odia_ai.configs import ODIAAIConfig, load_config
    from odia_ai.continual import (
        CorrectionStore,
        TriggerConfig,
        new_correction,
        should_trigger_retraining,
    )
    from odia_ai.extraction import ExtractionService
    from odia_ai.registry import ModelRegistry

    router = APIRouter(prefix="/ai", tags=["odia_ai"])
    cfg: ODIAAIConfig = load_config(config_path)

    # Lazily instantiated singletons
    _extraction_service: dict[str, Any] = {"svc": None}
    _correction_store: dict[str, Any] = {"store": None}
    _registry: dict[str, Any] = {"registry": None}

    def get_extraction_service() -> ExtractionService:
        if _extraction_service["svc"] is None:
            _extraction_service["svc"] = ExtractionService(
                finetuned_model_path=cfg.deployment.finetuned_model_path,
                llm_provider=cfg.deployment.default_llm_provider,
                llm_model=cfg.deployment.default_llm_model,
                force_backend=cfg.deployment.force_backend,
            )
        return _extraction_service["svc"]  # type: ignore

    def get_correction_store() -> CorrectionStore:
        if _correction_store["store"] is None:
            _correction_store["store"] = CorrectionStore(
                Path(cfg.continual.correction_store_path)
            )
        return _correction_store["store"]  # type: ignore

    def get_registry() -> ModelRegistry:
        if _registry["registry"] is None:
            _registry["registry"] = ModelRegistry(Path(cfg.deployment.registry_root))
        return _registry["registry"]  # type: ignore

    # ----------------------- request/response models --------------------

    class ExtractRequest(BaseModel):
        text: str = Field(..., description="Document passage to analyze")
        backend: str | None = Field(
            None, description="Optional backend override: pattern | rag_llm | finetuned"
        )

    class ExtractResponse(BaseModel):
        extraction: dict
        backend_used: str

    class CorrectionRequest(BaseModel):
        input_text: str
        field_name: str = Field(..., description="e.g. 'vendors', 'anomaly_candidates'")
        correction_type: str = Field(
            ..., description="addition | deletion | modification"
        )
        original_value: str
        corrected_value: str
        model_version_id: str = "unknown"
        jurisdiction: str = ""
        reviewer_id: str = ""
        reviewer_note: str = ""

    class CorrectionResponse(BaseModel):
        correction_id: str
        stored: bool

    class StatusResponse(BaseModel):
        backends_available: list[str]
        corrections_total: int
        corrections_pending: int
        should_retrain: bool
        retrain_reason: str
        production_model_version: str | None
        config: dict

    # --------------------------------- routes ---------------------------

    @router.post("/extract", response_model=ExtractResponse)
    async def extract(req: ExtractRequest) -> ExtractResponse:
        if not req.text or not req.text.strip():
            raise HTTPException(status_code=400, detail="text field is required")

        if req.backend:
            svc = ExtractionService(
                finetuned_model_path=cfg.deployment.finetuned_model_path,
                llm_provider=cfg.deployment.default_llm_provider,
                llm_model=cfg.deployment.default_llm_model,
                force_backend=req.backend,
            )
        else:
            svc = get_extraction_service()
        result = svc.extract(req.text)
        return ExtractResponse(
            extraction=result.to_dict(),
            backend_used=result.backend_used,
        )

    @router.post("/corrections", response_model=CorrectionResponse)
    async def submit_correction(req: CorrectionRequest) -> CorrectionResponse:
        if req.correction_type not in ("addition", "deletion", "modification"):
            raise HTTPException(
                status_code=400,
                detail="correction_type must be addition|deletion|modification",
            )
        try:
            corr = new_correction(
                input_text=req.input_text,
                field_name=req.field_name,
                correction_type=req.correction_type,  # type: ignore
                original_value=req.original_value,
                corrected_value=req.corrected_value,
                model_version_id=req.model_version_id,
                jurisdiction=req.jurisdiction,
                reviewer_id=req.reviewer_id,
                reviewer_note=req.reviewer_note,
            )
            store = get_correction_store()
            store.record(corr)
            return CorrectionResponse(correction_id=corr.correction_id, stored=True)
        except Exception as e:
            logger.exception("Correction submission failed")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @router.get("/corrections/stats")
    async def correction_stats() -> dict:
        store = get_correction_store()
        return {
            "total": store.count(),
            "reviewed": store.count(reviewed_only=True),
            "pending": store.count(reviewed_only=True, unapplied_only=True),
            "by_field": store.stats_by_field(),
            "by_jurisdiction": store.stats_by_jurisdiction(),
        }

    @router.get("/registry/versions")
    async def list_versions() -> dict:
        registry = get_registry()
        return {
            "versions": registry.list_versions(),
            "production": (
                registry.production_version().to_dict()
                if registry.production_version()
                else None
            ),
        }

    @router.get("/registry/versions/{version_id}")
    async def get_version(version_id: str) -> dict:
        registry = get_registry()
        v = registry.get(version_id)
        if v is None:
            raise HTTPException(
                status_code=404, detail=f"Unknown version: {version_id}"
            )
        return v.to_dict()

    @router.get("/status", response_model=StatusResponse)
    async def status() -> StatusResponse:
        svc = get_extraction_service()
        store = get_correction_store()
        registry = get_registry()
        prod = registry.production_version()

        trig_cfg = TriggerConfig(
            min_new_corrections=cfg.continual.min_new_corrections,
            min_days_since_last_training=cfg.continual.min_days_since_last_training,
        )
        decision = should_trigger_retraining(store, trig_cfg)

        return StatusResponse(
            backends_available=svc.available_backends(),
            corrections_total=store.count(),
            corrections_pending=store.count(reviewed_only=True, unapplied_only=True),
            should_retrain=decision.should_retrain,
            retrain_reason=decision.reason,
            production_model_version=prod.version_id if prod else None,
            config={
                "llm_provider": cfg.deployment.default_llm_provider,
                "llm_model": cfg.deployment.default_llm_model,
                "finetuned_model_path": cfg.deployment.finetuned_model_path,
                "correction_store": cfg.continual.correction_store_path,
                "registry_root": cfg.deployment.registry_root,
            },
        )

    @router.get("/health")
    async def health() -> dict:
        return {"status": "ok", "subsystem": "odia_ai"}

    return router


def include_ai_routes(app, config_path: str | None = None) -> None:
    """Register AI routes onto an existing FastAPI app.

    Usage:
        from fastapi import FastAPI
        from odia_ai.server_routes import include_ai_routes

        app = FastAPI()
        include_ai_routes(app)
    """
    router = _build_router(config_path)
    app.include_router(router)
