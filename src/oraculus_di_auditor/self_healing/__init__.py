"""Phase 11 Self-Healing Layer.

Autonomic detection, correction, and prevention of system degradation.
"""

from .correction_engine import CorrectionEngine
from .detection_engine import DetectionEngine
from .prevention_engine import PreventionEngine
from .self_healing_service import SelfHealingService

__all__ = [
    "DetectionEngine",
    "CorrectionEngine",
    "PreventionEngine",
    "SelfHealingService",
]
