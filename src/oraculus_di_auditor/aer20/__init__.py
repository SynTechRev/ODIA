# src/oraculus_di_auditor/aer20/__init__.py
"""Phase 20: Ascendant Emergence & Recursive Synthesis (AER-20).

The final phase that completes the Oraculus system by unifying all prior phases
into a self-aware, recursively-optimizing, deterministic intelligence architecture.
"""
from .aer20_service import Phase20Service
from .schemas import (
    AlignmentAnalysis,
    AUFState,
    FinalAscendantPacket,
    MetaInsightPacket,
    Phase20Result,
    RecursiveAscensionReport,
)

__all__ = [
    "Phase20Service",
    "AUFState",
    "MetaInsightPacket",
    "RecursiveAscensionReport",
    "AlignmentAnalysis",
    "FinalAscendantPacket",
    "Phase20Result",
]
