"""Consumer Adhesion Severity Index (CASI) scoring engine.

Aggregates C.O.N.T.R.A. detector findings into a five-axis score.
The engine is deterministic: identical input findings produce identical
output under all conditions. temperature=0 on all LLM calls enforces
this at the upstream extraction layer.

CASI Framework Version: 1.0
Source: C.O.N.T.R.A. Framework V1.0 Section V, Handoff Specification V1.0 Section IV
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..contra.base import Finding, Severity

# Axis names as string constants — used as keys in scoring_input dicts
AXIS_REMEDY_FORECLOSURE = "remedy_foreclosure"
AXIS_DATA_EXTRACTION_DEPTH = "data_extraction_depth"
AXIS_MODIFICATION_AND_CONSENT = "modification_and_consent"
AXIS_PROCEDURAL_ADHESION = "procedural_adhesion"
AXIS_ENFORCEMENT_COST_ASYMMETRY = "enforcement_cost_asymmetry"

_VALID_AXES: frozenset[str] = frozenset(
    {
        AXIS_REMEDY_FORECLOSURE,
        AXIS_DATA_EXTRACTION_DEPTH,
        AXIS_MODIFICATION_AND_CONSENT,
        AXIS_PROCEDURAL_ADHESION,
        AXIS_ENFORCEMENT_COST_ASYMMETRY,
    }
)

_AXIS_MAX = 20

# Default severity-to-delta mapping.
# Individual detectors may override per sub-detector where documented.
# CRITICAL=7 is capable of moving the aggregate across a band boundary alone.
_SEVERITY_DELTA: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 4,
    "critical": 7,
}


@dataclass
class CasiAxes:
    """Five-axis Consumer Adhesion Severity Index result.

    Each axis is 0-20; aggregate is 0-100.
    Axes measure: remedy access, data extraction breadth, consent mechanisms,
    procedural fairness, and enforcement cost distribution.
    """

    remedy_foreclosure: int = 0
    data_extraction_depth: int = 0
    modification_and_consent: int = 0
    procedural_adhesion: int = 0
    enforcement_cost_asymmetry: int = 0

    @property
    def aggregate(self) -> int:
        return (
            self.remedy_foreclosure
            + self.data_extraction_depth
            + self.modification_and_consent
            + self.procedural_adhesion
            + self.enforcement_cost_asymmetry
        )

    @property
    def band(self) -> str:
        agg = self.aggregate
        if agg <= 20:
            return "Baseline Adhesion"
        if agg <= 40:
            return "Elevated Asymmetry"
        if agg <= 60:
            return "Substantial Asymmetry"
        if agg <= 80:
            return "Severe Asymmetry"
        return "Foreclosure Regime"

    def to_dict(self) -> dict:
        return {
            "remedy_foreclosure": self.remedy_foreclosure,
            "data_extraction_depth": self.data_extraction_depth,
            "modification_and_consent": self.modification_and_consent,
            "procedural_adhesion": self.procedural_adhesion,
            "enforcement_cost_asymmetry": self.enforcement_cost_asymmetry,
            "aggregate": self.aggregate,
            "band": self.band,
        }


def severity_to_delta(severity: "Severity", override: int | None = None) -> int:
    """Convert a Severity enum to its axis delta contribution.

    Detectors may pass override when sub-detector-specific evidence
    justifies deviation from the default table. Overrides must be
    documented in the detector's docstring.
    """
    if override is not None:
        return override
    return _SEVERITY_DELTA.get(severity.value, 0)


def compute_casi(
    findings: List["Finding"],
    delta_overrides: dict[str, int] | None = None,
) -> CasiAxes:
    """Deterministic CASI computation from a list of findings.

    Findings contribute to axes via scoring_input["axis"] and
    scoring_input["delta"]. Unknown axes are silently ignored so that
    future detector additions do not break this function. Each axis
    is clamped at 20.

    delta_overrides: {finding_id: delta} for test-time injection.
    """
    axes: dict[str, int] = {
        AXIS_REMEDY_FORECLOSURE: 0,
        AXIS_DATA_EXTRACTION_DEPTH: 0,
        AXIS_MODIFICATION_AND_CONSENT: 0,
        AXIS_PROCEDURAL_ADHESION: 0,
        AXIS_ENFORCEMENT_COST_ASYMMETRY: 0,
    }

    for finding in findings:
        axis = finding.scoring_input.get("axis")
        if axis not in _VALID_AXES:
            continue
        if delta_overrides and finding.finding_id in delta_overrides:
            delta = delta_overrides[finding.finding_id]
        else:
            delta = finding.scoring_input.get("delta", 0)
        axes[axis] = min(_AXIS_MAX, axes[axis] + delta)

    return CasiAxes(**axes)
