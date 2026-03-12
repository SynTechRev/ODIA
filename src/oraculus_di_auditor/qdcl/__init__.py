"""QDCL - Quantum-Distributed Cognition Layer (Phase 13).

This module implements the quantum-distributed cognition layer that overlays
Phases 1-12 as a trans-scalar cognitive membrane enabling:

- Nonlinear reasoning across scales
- Cross-agent distributed inference
- Quantum-like superposition of hypothesis states
- Multi-perspective analysis fusion
- Predictive trajectory mapping using scalar harmonics
- Coherence-resonant decisioning
- Meta-agent awareness & topological state memory

The QDCL layer does not replace existing structures. It overlays them,
acting as a trans-scalar cognitive membrane that:
1. Consumes signals from Phases 1–12
2. Performs distributed inference
3. Generates convergence vectors
4. Feeds vectors back downstream into all agents
"""

from .adaptive_cognition import AdaptiveCompressionExpansion, CognitionMode
from .cognitive_mesh_fusion import CognitiveMeshFusion, SemanticFractalMap
from .convergence_vectors import (
    ConvergenceVector,
    ConvergenceVectorGenerator,
    ConvergenceVectorSet,
    VectorType,
)
from .fractal_trajectory import (
    FractalPredictiveTrajectoryEngine,
    TrajectoryProbabilityCube,
)
from .holographic_memory import HolographicMemoryOrganizer, MemoryType
from .multi_perspective import (
    DeltaDifferenceMap,
    MultiPerspectiveEvaluator,
    Perspective,
)
from .qdcl_service import QDCLService
from .quantum_kernel import DecisionKernel, QuantumKernelDecisionLayer
from .superpositional_hypothesis import (
    Hypothesis,
    HypothesisState,
    SuperpositionalHypothesisEngine,
)

__all__ = [
    # Main service
    "QDCLService",
    # Superpositional hypothesis engine
    "SuperpositionalHypothesisEngine",
    "Hypothesis",
    "HypothesisState",
    # Cognitive mesh fusion
    "CognitiveMeshFusion",
    "SemanticFractalMap",
    # Fractal trajectory engine
    "FractalPredictiveTrajectoryEngine",
    "TrajectoryProbabilityCube",
    # Convergence vectors
    "ConvergenceVectorGenerator",
    "ConvergenceVectorSet",
    "ConvergenceVector",
    "VectorType",
    # Holographic memory
    "HolographicMemoryOrganizer",
    "MemoryType",
    # Multi-perspective evaluation
    "MultiPerspectiveEvaluator",
    "DeltaDifferenceMap",
    "Perspective",
    # Adaptive cognition
    "AdaptiveCompressionExpansion",
    "CognitionMode",
    # Quantum kernel
    "QuantumKernelDecisionLayer",
    "DecisionKernel",
]

__version__ = "1.0.0"
__phase__ = 13
