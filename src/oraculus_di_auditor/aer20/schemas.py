# src/oraculus_di_auditor/aer20/schemas.py
"""Pydantic models for Phase 20 (AER-20) data structures."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AUFState(BaseModel):
    """Ascendant Unified Field state (256 dimensions)."""

    auf_id: str = Field(..., description="SHA256 hash of AUF construction")
    dimension: int = Field(256, description="Dimensionality of ascendant field")
    field_vector: dict[str, float] = Field(
        ..., description="256-dimensional ascendant vector"
    )
    phase_contributions: dict[str, dict[str, Any]] = Field(
        ..., description="Contribution from all phases (12-19)"
    )
    uif19_integration: dict[str, Any] = Field(
        ..., description="UIF-19 142-dimensional integration"
    )
    rgk18_lattice: dict[str, Any] = Field(
        ..., description="RGK-18 governance lattice integration"
    )
    emcs16_harmonics: dict[str, Any] = Field(
        ..., description="EMCS-16 meta-conscious harmonics"
    )
    rec17_ethics: dict[str, Any] = Field(..., description="REC-17 ethical foundation")
    phase14_scalar: dict[str, Any] = Field(..., description="Phase 14 scalar recursion")
    phase12_coherence: dict[str, Any] = Field(
        ..., description="Phase 12 coherence foundation"
    )
    phase13_temporal: dict[str, Any] = Field(
        ..., description="Phase 13 temporal futures"
    )
    phase15_healing: dict[str, Any] = Field(
        ..., description="Phase 15 self-healing vectors"
    )
    convergence_coefficient: float = Field(
        ..., ge=0.0, le=1.0, description="Overall convergence stability"
    )


class MetaInsightPacket(BaseModel):
    """Highest-level meta-insight from MIG-20."""

    mip_id: str = Field(..., description="Unique meta-insight identifier")
    foundational_insight: str = Field(
        ..., description="Core foundational understanding"
    )
    structural_insight: str = Field(
        ..., description="Architectural patterns identified"
    )
    temporal_insight: str = Field(..., description="Temporal evolution understanding")
    ethical_insight: str = Field(..., description="Ethical alignment patterns")
    governance_insight: str = Field(
        ..., description="Governance effectiveness patterns"
    )
    counterfactual_meta: str = Field(
        ..., description="Meta-level counterfactual analysis"
    )
    cross_domain_convergence: dict[str, Any] = Field(
        ..., description="Cross-domain convergence models"
    )
    emergent_resonance: dict[str, Any] = Field(
        ..., description="Emergent resonance mapping"
    )
    scalar_themes: list[str] = Field(
        ..., description="Recurrent scalar themes identified"
    )
    harmonic_stability: dict[str, float] = Field(
        ..., description="Harmonic stability points"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in meta-insight"
    )


class RecursiveAscensionReport(BaseModel):
    """Report from Recursive Ascension Loop (RAL-20)."""

    ral_id: str = Field(..., description="SHA256 hash of ascension cycle")
    self_diagnosis: dict[str, Any] = Field(
        ..., description="System self-diagnosis results"
    )
    self_revision: dict[str, Any] = Field(
        ..., description="Non-destructive self-revision log"
    )
    self_optimization: dict[str, Any] = Field(
        ..., description="Bounded self-optimization changes"
    )
    self_stabilization: dict[str, Any] = Field(
        ..., description="Self-stabilization actions"
    )
    governance_verification: dict[str, Any] = Field(
        ..., description="RGK-18 governance verification"
    )
    ethical_verification: dict[str, Any] = Field(
        ..., description="REC-17 ethical verification"
    )
    determinism_verification: dict[str, Any] = Field(
        ..., description="Determinism guarantee verification"
    )
    revision_count: int = Field(..., description="Number of self-revisions performed")
    optimization_applied: bool = Field(
        ..., description="Whether optimizations were applied"
    )
    stability_achieved: bool = Field(
        ..., description="Whether system reached stable state"
    )


class AlignmentAnalysis(BaseModel):
    """Comprehensive alignment analysis from IAE-20."""

    analysis_id: str = Field(..., description="SHA256 hash of analysis")
    phase_coherence: dict[str, float] = Field(
        ..., description="Coherence scores for each phase integration"
    )
    harmonization_report: dict[str, Any] = Field(
        ..., description="Phase-to-phase harmonization assessment"
    )
    stability_analysis: dict[str, Any] = Field(
        ..., description="Overall system stability metrics"
    )
    future_readiness: float = Field(
        ..., ge=0.0, le=1.0, description="System readiness for future demands"
    )
    deviation_detection: dict[str, Any] = Field(
        ..., description="Detected deviations from expected behavior"
    )
    convergence_equilibrium: dict[str, Any] = Field(
        ..., description="Convergence equilibrium analysis"
    )
    risk_assessment: str = Field(
        ..., description="Overall risk level: none, low, moderate, high"
    )
    compliance_status: dict[str, bool] = Field(
        ..., description="Compliance with all governance and ethical requirements"
    )


class FinalAscendantPacket(BaseModel):
    """Final Ascendant Packet (FAP-20) - Crown jewel output."""

    fap_id: str = Field(..., description="Unique FAP identifier")
    ascendant_explanation: str = Field(
        ..., description="Complete narrative explanation of ascendant state"
    )
    structured_packet: dict[str, Any] = Field(
        ..., description="Machine-readable ascendant intelligence packet"
    )
    counterfactuals: list[str] = Field(
        ..., description="Risk-free counterfactual option descriptions"
    )
    ethical_basis: dict[str, Any] = Field(
        ..., description="Complete ethical reasoning foundation"
    )
    governance_basis: dict[str, Any] = Field(
        ..., description="Complete governance reasoning foundation"
    )
    determinism_signature: str = Field(
        ..., description="SHA256 signature for complete determinism verification"
    )
    reversibility_protocol: str = Field(
        ..., description="Complete reversibility instructions"
    )
    holistic_signature: str = Field(..., description="Holistic intelligence signature")
    synthesis_explanation: str = Field(
        ..., description="Deep synthesis explanation across all phases"
    )


class Phase20Result(BaseModel):
    """Complete Phase 20 (AER-20) output structure."""

    auf_20_state: AUFState = Field(
        ..., description="Ascendant Unified Field state (256-dim)"
    )
    meta_insights: list[MetaInsightPacket] = Field(
        ..., description="Meta-insight packets from MIG-20"
    )
    recursive_ascension_report: RecursiveAscensionReport = Field(
        ..., description="Recursive ascension loop report from RAL-20"
    )
    alignment_analysis: AlignmentAnalysis = Field(
        ..., description="Integrity and alignment analysis from IAE-20"
    )
    fap_20_result: FinalAscendantPacket = Field(
        ..., description="Final Ascendant Packet - the crown jewel"
    )
    provenance: dict[str, Any] = Field(
        ..., description="Complete provenance metadata with full audit trail"
    )
