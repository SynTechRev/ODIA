# src/oraculus_di_auditor/rgk18/schemas.py
"""Pydantic v2 schemas for Phase 18: Recursive Governance Kernel."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PolicyCheckResult(BaseModel):
    """Result of a policy check against a candidate action."""

    policy_id: str = Field(..., description="Identifier of the checked policy")
    violated: bool = Field(..., description="Whether the policy was violated")
    reason: str | None = Field(None, description="Reason for the result")
    severity: Literal["low", "medium", "high"] = Field(
        ..., description="Severity level of the violation"
    )


class DecisionScore(BaseModel):
    """Composite score from multi-source evidence aggregation."""

    score: float = Field(..., ge=0.0, le=1.0, description="Final score (0.0 - 1.0)")
    components: dict[str, float] = Field(
        default_factory=dict,
        description="Component scores (e.g., harm, ethics, temporal)",
    )


class DecisionOutcome(BaseModel):
    """Decision outcome from the governance kernel."""

    outcome: Literal["APPROVE", "CONDITIONAL_APPROVE", "REJECT", "REVIEW"] = Field(
        ..., description="Decision outcome"
    )
    rationale: str = Field(..., description="Reasoning for the decision")
    mitigations: list[str] = Field(
        default_factory=list, description="Recommended mitigations if conditional"
    )


class LedgerEntry(BaseModel):
    """Immutable ledger entry for a governance decision."""

    entry_id: str = Field(..., description="Unique entry identifier")
    input_hash: str = Field(..., description="SHA256 hash of canonical input")
    decision: DecisionOutcome = Field(..., description="Decision outcome")
    score: DecisionScore = Field(..., description="Composite score")
    policies_checked: list[PolicyCheckResult] = Field(
        default_factory=list, description="List of policy check results"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Provenance metadata (seed, timestamp, service_version, etc.)",
    )
    signature: str = Field(
        ..., description="SHA256 chain signature for integrity verification"
    )


class Phase18Result(BaseModel):
    """Complete result from Phase 18 governance evaluation."""

    outcome: DecisionOutcome = Field(..., description="Decision outcome")
    score: DecisionScore = Field(..., description="Composite score")
    policy_violations: list[PolicyCheckResult] = Field(
        default_factory=list, description="List of policy violations"
    )
    ledger_entry_id: str | None = Field(
        None, description="Ledger entry ID if persisted"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Provenance metadata"
    )
