"""C.O.N.T.R.A. CASI — thin re-export of scoring.casi (V2.0-A-6).

The canonical CASI engine lives in scoring/casi.py.  This module exists
only for backward-compatible import paths:

    from oraculus_di_auditor.contra.casi import compute_casi  # legacy
    from oraculus_di_auditor.scoring.casi import compute_casi  # canonical

The local compute_casi() wraps the canonical CasiAxes-returning engine
and converts to a plain dict so existing callers continue to work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from oraculus_di_auditor.scoring.casi import (
    AXIS_DATA_EXTRACTION_DEPTH,
    AXIS_ENFORCEMENT_COST_ASYMMETRY,
    AXIS_MODIFICATION_AND_CONSENT,
    AXIS_PROCEDURAL_ADHESION,
    AXIS_REMEDY_FORECLOSURE,
    CasiAxes,
    compute_casi as _compute_casi,
    severity_to_delta,
)

if TYPE_CHECKING:
    from oraculus_di_auditor.contra.base import Finding


def compute_casi(findings: list[Finding]) -> dict[str, int | str]:
    """Compute CASI — delegates to scoring.casi.compute_casi.

    Returns a flat dict for callers predating the CasiAxes dataclass.
    New code should import from scoring.casi and use CasiAxes directly.
    """
    return _compute_casi(findings).to_dict()


__all__ = [
    "AXIS_DATA_EXTRACTION_DEPTH",
    "AXIS_ENFORCEMENT_COST_ASYMMETRY",
    "AXIS_MODIFICATION_AND_CONSENT",
    "AXIS_PROCEDURAL_ADHESION",
    "AXIS_REMEDY_FORECLOSURE",
    "CasiAxes",
    "compute_casi",
    "severity_to_delta",
]
