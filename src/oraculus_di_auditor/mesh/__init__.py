"""Agent Mesh module for Phase 10.

Multi-agent distributed execution system with intent-based routing,
autonomous coordination, and result synthesis.
"""

from .agent_registry import AgentRegistry
from .agent_types import (
    BaseAgent,
    ConstraintAgent,
    RoutingAgent,
    SentinelAgent,
    SynthesisAgent,
)
from .mesh_coordinator import MeshCoordinator
from .routing_engine import RoutingEngine
from .schemas import (
    AgentNodeSchema,
    AgentRegistrationRequest,
    AgentRegistrationResponse,
    AgentTaskResult,
    MeshExecutionRequest,
    MeshExecutionResponse,
    MeshGraphLink,
    MeshGraphNode,
    MeshGraphResponse,
)
from .synthesis_engine import SynthesisEngine

__all__ = [
    "MeshCoordinator",
    "AgentRegistry",
    "RoutingEngine",
    "SynthesisEngine",
    "BaseAgent",
    "SentinelAgent",
    "ConstraintAgent",
    "RoutingAgent",
    "SynthesisAgent",
    "AgentNodeSchema",
    "AgentRegistrationRequest",
    "AgentRegistrationResponse",
    "MeshExecutionRequest",
    "AgentTaskResult",
    "MeshExecutionResponse",
    "MeshGraphNode",
    "MeshGraphLink",
    "MeshGraphResponse",
]
