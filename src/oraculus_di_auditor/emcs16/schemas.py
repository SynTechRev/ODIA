# src/oraculus_di_auditor/emcs16/schemas.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Phase16RunOptions(BaseModel):
    auto_apply: bool = Field(
        False, description="Allow auto-application of low-risk fixes"
    )
    dry_run: bool = Field(True, description="If True, suggest but do not apply changes")
    time_depth: int = Field(12, ge=1)
    debug: bool = Field(False)


class Phase16Request(BaseModel):
    system_state: dict[str, Any]
    phase12_harmonics: dict[str, float]
    phase13_probabilities: dict[str, float]
    phase14_outputs: dict[str, Any]
    run_options: Phase16RunOptions = Field(default_factory=Phase16RunOptions)


class ActionSuggestion(BaseModel):
    id: str
    description: str
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    estimated_effort_hours: float = Field(0.0, ge=0.0)
    risk_level: Literal["low", "medium", "high"] = "low"
    reversible: bool = True


class Phase16Result(BaseModel):
    meta_state_vector: dict[str, Any]
    recursive_integrity_score: float = Field(0.0, ge=0.0, le=1.0)
    emergent_pattern_index: dict[str, float]
    prediction_drift_corrections: list[ActionSuggestion]
    self_reflection_report: dict[str, Any]
    meta_harmonic_field: dict[str, float]
    provenance: dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
