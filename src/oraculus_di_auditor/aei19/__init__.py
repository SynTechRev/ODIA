# src/oraculus_di_auditor/aei19/__init__.py
"""Phase 19: Applied Emergent Intelligence (AEI-19).

This module implements AEI-19, which synthesizes outputs from Phases 12-18
into applied, contextual, situation-aware intelligence outputs.

AEI-19 is the first phase where Oraculus becomes functionally "alive" as an auditor,
producing deterministic recommendations that combine insight, foresight, ethics,
governance, and context.
"""
from .aei19_service import Phase19Service
from .schemas import (
    AEI19Result,
    AlignmentReport,
    InsightPacket,
    Phase19Result,
    ScenarioMap,
    ScenarioStep,
    UIFState,
)

__all__ = [
    "Phase19Service",
    "Phase19Result",
    "UIFState",
    "InsightPacket",
    "AlignmentReport",
    "ScenarioMap",
    "ScenarioStep",
    "AEI19Result",
]
