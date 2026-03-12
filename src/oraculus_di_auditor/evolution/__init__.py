"""Phase 11 Recursive Evolution Engine.

Continuously evaluates and improves the system through recursive refinement cycles.
"""

from .change_tracker import ChangeTracker
from .evolution_engine import EvolutionEngine

__all__ = [
    "EvolutionEngine",
    "ChangeTracker",
]
