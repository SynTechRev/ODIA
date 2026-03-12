"""API routes for Global Constraint Network (GCN).

Endpoints for GCN state, validation, and constraint enforcement.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import FastAPI dependencies
try:
    from fastapi import APIRouter

    from ...gcn import (
        ConstraintValidationRequest,
        GCNService,
        GCNValidateRequest,
    )

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object  # type: ignore

# Initialize GCN service
gcn_service = GCNService() if FASTAPI_AVAILABLE else None

# Create router
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/gcn", tags=["gcn"])
else:
    router = None  # type: ignore


def get_gcn_state() -> dict[str, Any]:
    """Get current GCN system state.

    Returns:
        GCN state summary
    """
    if not gcn_service:
        return {"error": "GCN service not available"}

    return gcn_service.get_state()


def validate_gcn_system(request: dict[str, Any]) -> dict[str, Any]:
    """Validate GCN system state and integrity.

    Args:
        request: Validation request parameters

    Returns:
        Validation result
    """
    if not gcn_service:
        return {"error": "GCN service not available"}

    deep = request.get("deep", False)
    check_rules = request.get("check_rules", True)
    check_policies = request.get("check_policies", True)

    return gcn_service.validate_system(
        deep=deep,
        check_rules=check_rules,
        check_policies=check_policies,
    )


def validate_entity_constraints(request: dict[str, Any]) -> dict[str, Any]:
    """Validate an entity against GCN constraints.

    Args:
        request: Constraint validation request

    Returns:
        Validation result with violations
    """
    if not gcn_service:
        return {"error": "GCN service not available"}

    entity_type = request.get("entity_type", "document")
    entity_id = request.get("entity_id", "unknown")
    entity_data = request.get("entity_data", {})
    scope = request.get("scope", "global")
    strict = request.get("strict", True)

    return gcn_service.validate_entity(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_data=entity_data,
        scope=scope,
        strict=strict,
    )


# Register routes if FastAPI is available
if FASTAPI_AVAILABLE and router:

    @router.get("/state")
    async def gcn_state_endpoint():
        """Get GCN state.

        Returns current state of the Global Constraint Network including
        rules loaded, enforcement mode, and health status.
        """
        return get_gcn_state()

    @router.post("/validate")
    async def gcn_validate_endpoint(request: GCNValidateRequest):  # type: ignore
        """Validate GCN system.

        Validates GCN system state, rule integrity, and policy consistency.
        Can perform quick or deep validation.
        """
        request_dict = request.dict() if hasattr(request, "dict") else request
        return validate_gcn_system(request_dict)

    @router.post("/validate/entity")
    async def gcn_validate_entity_endpoint(request: ConstraintValidationRequest):  # type: ignore  # noqa: E501
        """Validate entity against GCN constraints.

        Validates documents, jobs, agents, or tasks against GCN constraint rules.
        Returns list of violations if any constraints are violated.
        """
        request_dict = request.dict() if hasattr(request, "dict") else request
        return validate_entity_constraints(request_dict)


__all__ = [
    "router",
    "get_gcn_state",
    "validate_gcn_system",
    "validate_entity_constraints",
]
