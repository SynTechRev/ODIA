"""Phase 9 Governor API Routes.

Implements REST endpoints for pipeline governance, validation, and policy enforcement.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Import Pydantic models conditionally
try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore

    def Field(*args, **kwargs):  # type: ignore  # noqa: N802
        """Stub Field function for when Pydantic is not installed."""
        return None


# ============================================================================
# Request/Response Schemas (Pydantic v2)
# ============================================================================


class ValidateRequest(BaseModel):  # type: ignore
    """Request model for /governor/validate endpoint."""

    deep: bool = Field(
        default=False,
        description="Whether to run deep validation (slower but thorough)",
    )


class EnforceRequest(BaseModel):  # type: ignore
    """Request model for /governor/enforce endpoint."""

    document_text: str = Field(
        ..., min_length=1, description="Document text to validate"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    options: dict[str, Any] = Field(
        default_factory=dict, description="Enforcement options"
    )


class StateResponse(BaseModel):  # type: ignore
    """Response model for /governor/state endpoint."""

    timestamp: str = Field(..., description="Response timestamp")
    overall_health: str = Field(..., description="Overall system health status")
    governor_version: str = Field(..., description="Governor version")
    validation_summary: dict[str, Any] = Field(..., description="Validation summary")
    policy_version: str = Field(..., description="Policy version")
    security_posture: str = Field(..., description="Security posture status")
    compliance_status: str = Field(..., description="Compliance monitoring status")


class ValidationResponse(BaseModel):  # type: ignore
    """Response model for /governor/validate endpoint."""

    timestamp: str = Field(..., description="Validation timestamp")
    overall_status: str = Field(..., description="Overall validation status")
    checks: dict[str, Any] = Field(..., description="Individual check results")


class EnforcementResponse(BaseModel):  # type: ignore
    """Response model for /governor/enforce endpoint."""

    timestamp: str = Field(..., description="Enforcement timestamp")
    enforcement_status: str = Field(
        ..., description="Enforcement decision (passed/blocked)"
    )
    checks_performed: list[str] = Field(..., description="List of checks performed")
    violations: list[dict[str, Any]] = Field(
        default_factory=list, description="Policy violations"
    )
    warnings: list[dict[str, Any]] = Field(
        default_factory=list, description="Policy warnings"
    )
    security_profile: dict[str, Any] = Field(
        default_factory=dict, description="Security profile"
    )
    document_policies: dict[str, Any] = Field(
        default_factory=dict, description="Document policy results"
    )
    security_policies: dict[str, Any] = Field(
        default_factory=dict, description="Security policy results"
    )


# ============================================================================
# Route Registration
# ============================================================================


def register_governor_routes(app: Any) -> None:
    """Register governor routes to FastAPI app.

    Args:
        app: FastAPI application instance
    """
    from ...governor import GovernorService

    service = GovernorService()

    @app.get("/governor/state")
    async def get_state() -> StateResponse:
        """Get current system state and health.

        Returns system health summary including validation status,
        policy version, security posture, and compliance status.

        Returns:
            StateResponse with system state
        """
        logger.info("Governor state request received")
        state = service.get_system_state()
        logger.info("Governor state returned")
        return StateResponse(**state)

    @app.post("/governor/validate")
    async def validate_pipeline(request: ValidateRequest) -> ValidationResponse:
        """Validate pipeline components and readiness.

        Performs validation of schemas, agents, dependencies, database,
        orchestrator, models, and endpoints.

        Args:
            request: Validation request with options

        Returns:
            ValidationResponse with validation results
        """
        logger.info(f"Pipeline validation request received (deep={request.deep})")
        result = service.validate_pipeline(deep=request.deep)
        logger.info(f"Pipeline validation completed: {result['overall_status']}")
        return ValidationResponse(**result)

    @app.post("/governor/enforce")
    async def enforce_policies(request: EnforceRequest) -> EnforcementResponse:
        """Enforce governance policies on a document.

        Checks document against security policies, input sanitation,
        threat detection, and compliance rules.

        Args:
            request: Enforcement request with document and options

        Returns:
            EnforcementResponse with enforcement decision and details
        """
        logger.info("Policy enforcement request received")
        result = service.enforce_policies(
            request.document_text, request.metadata, request.options
        )
        logger.info(f"Policy enforcement completed: {result['enforcement_status']}")
        return EnforcementResponse(**result)


__all__ = [
    "ValidateRequest",
    "EnforceRequest",
    "StateResponse",
    "ValidationResponse",
    "EnforcementResponse",
    "register_governor_routes",
]
