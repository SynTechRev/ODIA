"""Pydantic schemas for Global Constraint Network (GCN).

Request/response models for GCN API endpoints and internal operations.
"""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore

    def Field(*args, **kwargs):  # type: ignore  # noqa: N802
        """Stub Field function for when Pydantic is not installed."""
        return None


class GCNRuleSchema(BaseModel):  # type: ignore
    """Schema for a GCN rule definition."""

    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    rule_type: str = Field(
        ...,
        description="Rule type: structural, policy, document, pipeline, safety",
    )
    rule_version: str = Field(..., description="Rule version (semver)")
    enabled: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(
        default=0, description="Rule priority (higher = evaluated first)"
    )
    scope: str = Field(..., description="Rule scope: global, agent, document, job")
    constraint_expression: str = Field(
        ..., description="Constraint definition/expression"
    )
    violation_action: str = Field(
        ...,
        description="Action on violation: block, warn, log, quarantine",
    )
    rule_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional rule configuration",
    )


class ConstraintValidationRequest(BaseModel):  # type: ignore
    """Request to validate constraints against GCN."""

    entity_type: str = Field(
        ...,
        description="Type of entity to validate: document, job, agent, task",
    )
    entity_id: str = Field(..., description="Entity identifier")
    entity_data: dict[str, Any] = Field(
        ...,
        description="Entity data to validate",
    )
    scope: str = Field(
        default="global",
        description="Validation scope: global, agent, document, job",
    )
    strict: bool = Field(
        default=True,
        description="Whether to fail on warnings",
    )


class ConstraintViolation(BaseModel):  # type: ignore
    """A single constraint violation."""

    rule_id: str = Field(..., description="Violated rule ID")
    rule_name: str = Field(..., description="Violated rule name")
    severity: str = Field(
        ..., description="Violation severity: error, warning, critical"
    )
    action: str = Field(
        ..., description="Violation action: block, warn, log, quarantine"
    )
    message: str = Field(..., description="Human-readable violation message")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional violation details",
    )


class ConstraintValidationResponse(BaseModel):  # type: ignore
    """Response from constraint validation."""

    valid: bool = Field(..., description="Whether validation passed")
    entity_id: str = Field(..., description="Validated entity ID")
    timestamp: str = Field(..., description="Validation timestamp (ISO 8601)")
    rules_evaluated: int = Field(..., description="Number of rules evaluated")
    violations: list[ConstraintViolation] = Field(
        default_factory=list,
        description="List of constraint violations",
    )
    blocked: bool = Field(
        default=False,
        description="Whether entity is blocked due to violations",
    )
    warnings: int = Field(default=0, description="Number of warnings")
    errors: int = Field(default=0, description="Number of errors")


class GCNStateResponse(BaseModel):  # type: ignore
    """GCN system state response."""

    timestamp: str = Field(..., description="State timestamp (ISO 8601)")
    gcn_version: str = Field(..., description="GCN version")
    rules_loaded: int = Field(..., description="Number of rules loaded")
    rules_active: int = Field(..., description="Number of active rules")
    rules_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Rule count by type",
    )
    enforcement_mode: str = Field(
        ...,
        description="Enforcement mode: strict, permissive, audit",
    )
    last_validation: str | None = Field(
        None,
        description="Last validation timestamp",
    )
    health_status: str = Field(
        ..., description="Health status: healthy, degraded, error"
    )


class GCNValidateRequest(BaseModel):  # type: ignore
    """Request to validate GCN system state."""

    deep: bool = Field(
        default=False,
        description="Whether to perform deep validation",
    )
    check_rules: bool = Field(
        default=True,
        description="Whether to check rule integrity",
    )
    check_policies: bool = Field(
        default=True,
        description="Whether to check policy consistency",
    )


class GCNValidateResponse(BaseModel):  # type: ignore
    """Response from GCN system validation."""

    timestamp: str = Field(..., description="Validation timestamp (ISO 8601)")
    overall_status: str = Field(
        ..., description="Overall status: success, warning, error"
    )
    checks: dict[str, Any] = Field(
        default_factory=dict,
        description="Validation check results",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Validation errors",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings",
    )


__all__ = [
    "GCNRuleSchema",
    "ConstraintValidationRequest",
    "ConstraintViolation",
    "ConstraintValidationResponse",
    "GCNStateResponse",
    "GCNValidateRequest",
    "GCNValidateResponse",
]
