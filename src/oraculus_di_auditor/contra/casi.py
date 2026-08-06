"""CASI — Commercial Adhesion Severity Index scoring engine.

Aggregates findings from L-11 through L-20 detectors into a five-axis
score (each axis 0–20, clamped) and a 0–100 aggregate.

Axes:
  remedy_foreclosure          -- L-11B/G/H/J, L-12C/D, L-15A/C/F, L-18A-G
  data_extraction_depth       -- L-14A-I, L-15A-F, L-16A-H, L-17A-F
  modification_and_consent    -- L-13A-E
  procedural_adhesion         -- L-11A/C/D/F/I, L-12A/B/E, L-20A-H
  enforcement_cost_asymmetry  -- L-11E/G, L-19A-G

Source: C.O.N.T.R.A. Framework V1.0 Section 5, Handoff Spec V1.0 Section 6
"""

from __future__ import annotations

from typing import Dict, List

from .base import Finding

_AXES = (
    "remedy_foreclosure",
    "data_extraction_depth",
    "modification_and_consent",
    "procedural_adhesion",
    "enforcement_cost_asymmetry",
)

_AXIS_CAP = 20
_AGGREGATE_CAP = 100


def compute_casi(findings: List[Finding]) -> Dict[str, int]:
    """Compute the CASI score from a list of findings.

    Returns a dict with one key per axis (each clamped to [0, 20]) plus
    an 'aggregate' key equal to the clamped sum (max 100).
    """
    scores: Dict[str, int] = {axis: 0 for axis in _AXES}

    for finding in findings:
        axis = finding.scoring_input.get("axis")
        delta = finding.scoring_input.get("delta", 0)
        if axis in scores:
            scores[axis] += delta

    # Clamp axes
    for axis in _AXES:
        scores[axis] = min(_AXIS_CAP, max(0, scores[axis]))

    scores["aggregate"] = min(_AGGREGATE_CAP, sum(scores[axis] for axis in _AXES))
    return scores
