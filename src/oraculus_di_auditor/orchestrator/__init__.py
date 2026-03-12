"""Phase 5 Autonomous Agent Orchestration Module.

This module implements the Phase 5 orchestration kernel for Oraculus-DI-Auditor,
providing multi-agent coordination, task scheduling, and async execution capabilities.

The orchestrator coordinates:
- Ingestion Agent: Document materialization and chunking
- Analysis Agent: Unified pipeline execution (fiscal, constitutional, surveillance)
- Anomaly Agent: Inconsistency and risk pattern detection
- Synthesis Agent: Cross-document narrative generation
- Database Agent: Persistence operations
- Interface Agent: External system responses

All operations maintain:
- Deterministic behavior
- Explainability
- Provenance tracking
- Chain-of-custody semantics
- Secure defaults
- Graceful degradation
"""

from .agents import (
    AnalysisAgent,
    AnomalyAgent,
    DatabaseAgent,
    IngestionAgent,
    InterfaceAgent,
    SynthesisAgent,
)
from .orchestrator import Phase5Orchestrator
from .results import (
    AgentResponse,
    CrossDocumentSynthesis,
    PipelineOutput,
    TaskExecutionPlan,
)
from .task_graph import TaskGraph

__all__ = [
    "Phase5Orchestrator",
    "IngestionAgent",
    "AnalysisAgent",
    "AnomalyAgent",
    "SynthesisAgent",
    "DatabaseAgent",
    "InterfaceAgent",
    "TaskGraph",
    "TaskExecutionPlan",
    "AgentResponse",
    "CrossDocumentSynthesis",
    "PipelineOutput",
]
