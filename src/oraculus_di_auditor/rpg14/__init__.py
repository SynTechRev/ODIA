"""Phase 14: Meta-Causal Inference & Recursive Predictive Governance Engine (RPG-14).

The governing intelligence layer that sits above Phases 1-13, providing:
- Retrocausal inference and root cause analysis
- Causal Responsibility Index (CRI) computation
- Causal anomaly detection with 7 required outputs
- Governance trajectory prognosis (best/worst/median)
- Governance stability assessment
- Predictive governance advisories
"""

from .causal_anomaly_detector import AnomalyType, CausalAnomalyDetector
from .causal_graph import CausalGraph, CausalNode, NodeType, StateVector
from .causal_responsibility_index import CausalResponsibilityIndex
from .governance_prognosis import GovernancePrognosisGenerator, TrajectoryType
from .phase14_service import Phase14Service
from .retrocausal_inference import RetrocausalInferenceEngine

__all__ = [
    # Main service
    "Phase14Service",
    # Causal graph
    "CausalGraph",
    "CausalNode",
    "NodeType",
    "StateVector",
    # Retrocausal inference
    "RetrocausalInferenceEngine",
    # CRI
    "CausalResponsibilityIndex",
    # Anomaly detection
    "CausalAnomalyDetector",
    "AnomalyType",
    # Prognosis
    "GovernancePrognosisGenerator",
    "TrajectoryType",
]

__version__ = "1.0.0"
__phase__ = 14
