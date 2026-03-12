# src/oraculus_di_auditor/rec17/schemas.py
"""Pydantic v2 schemas for Phase 17: Recursive Ethical Cognition."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EthicalLattice(BaseModel):
    """Multi-axis ethical lattice representation."""

    ethical_vector: dict[str, float] = Field(
        ..., description="Axis name to score (0-1) mapping"
    )
    primary_ethic: str = Field(
        ...,
        description=(
            "Dominant ethical principle "
            "(beneficence, non-maleficence, justice, autonomy, stability)"
        ),
    )
    lattice_id: str = Field(..., description="SHA256 hash of sorted ethical vector")


class EthicalProjection(BaseModel):
    """Projected ethical consequences over future states."""

    projected_scores: list[float] = Field(
        ..., description="3-step ethical projection scores"
    )
    delta_ethics: float = Field(
        ..., description="Difference between projected and current ethics"
    )
    risk: Literal["none", "low", "moderate", "high"] = Field(
        ..., description="Risk grade based on projection"
    )
    reversible: bool = Field(..., description="Whether changes are reversible")


class LegalMap(BaseModel):
    """Legal and constitutional mapping of actions."""

    constitutional_flags: list[str] = Field(
        default_factory=list, description="US Constitutional concerns"
    )
    human_rights_flags: list[str] = Field(
        default_factory=list, description="International human rights concerns"
    )
    compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall compliance score"
    )


class GovernanceInvariants(BaseModel):
    """Governance invariant violations and alignment."""

    invariant_violations: list[str] = Field(
        default_factory=list, description="List of violated invariants"
    )
    alignment_score: float = Field(
        ..., ge=0.0, le=1.0, description="Alignment with governance invariants"
    )


class Phase17Result(BaseModel):
    """Complete Phase 17 ethical reasoning result."""

    ethical_lattice: EthicalLattice
    ethical_projection: EthicalProjection
    legal_map: LegalMap
    governance_invariants: GovernanceInvariants
    global_ethics_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall ethical score"
    )
    action_suggestions: list[str] = Field(
        default_factory=list, description="Recommended actions"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Provenance metadata"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
