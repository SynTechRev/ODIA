"""Pydantic schemas for Agent Mesh module.

Request/response models for mesh API endpoints and internal operations.
"""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore

    def Field(*args, **kwargs):  # type: ignore  # noqa: N802
        """Stub Field function for when Pydantic is not installed."""
        return None


class AgentNodeSchema(BaseModel):  # type: ignore
    """Schema for an agent node in the mesh."""

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_name: str = Field(..., description="Human-readable agent name")
    agent_type: str = Field(
        ...,
        description="Agent type: sentinel, constraint, routing, synthesis, specialist",
    )
    status: str = Field(
        default="active",
        description="Agent status: active, inactive, suspended, error",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of agent capabilities",
    )
    version: str = Field(..., description="Agent version")
    priority: int = Field(default=0, description="Agent priority")
    max_concurrent_tasks: int = Field(
        default=10,
        description="Maximum concurrent tasks",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional agent metadata",
    )


class AgentRegistrationRequest(BaseModel):  # type: ignore
    """Request to register a new agent in the mesh."""

    agent_name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    capabilities: list[str] = Field(
        default_factory=list,
        description="Agent capabilities",
    )
    version: str = Field(..., description="Agent version")
    priority: int = Field(default=0, description="Agent priority")
    max_concurrent_tasks: int = Field(
        default=10,
        description="Maximum concurrent tasks",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent metadata",
    )


class AgentRegistrationResponse(BaseModel):  # type: ignore
    """Response from agent registration."""

    success: bool = Field(..., description="Whether registration succeeded")
    agent_id: str = Field(..., description="Assigned agent ID")
    message: str = Field(..., description="Registration message")
    timestamp: str = Field(..., description="Registration timestamp (ISO 8601)")


class MeshExecutionRequest(BaseModel):  # type: ignore
    """Request for multi-agent mesh execution."""

    job_type: str = Field(
        ...,
        description="Job type: analysis, synthesis, routing, validation",
    )
    documents: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Documents to process",
    )
    agents: list[str] = Field(
        default_factory=list,
        description="Specific agents to use (empty = auto-select)",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution options",
    )
    gcn_validate: bool = Field(
        default=True,
        description="Whether to validate with GCN before execution",
    )
    governor_check: bool = Field(
        default=True,
        description="Whether to check with Governor before execution",
    )


class AgentTaskResult(BaseModel):  # type: ignore
    """Result from a single agent task execution."""

    agent_id: str = Field(..., description="Agent that executed the task")
    task_name: str = Field(..., description="Task name")
    status: str = Field(..., description="Task status: success, failed, interrupted")
    result: dict[str, Any] = Field(
        default_factory=dict,
        description="Task result data",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Task execution metrics",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Task errors",
    )


class MeshExecutionResponse(BaseModel):  # type: ignore
    """Response from mesh execution."""

    success: bool = Field(..., description="Whether execution succeeded")
    job_id: str = Field(..., description="Mesh execution job ID")
    status: str = Field(..., description="Job status")
    timestamp: str = Field(..., description="Execution timestamp (ISO 8601)")
    agent_count: int = Field(..., description="Number of agents used")
    task_count: int = Field(..., description="Number of tasks executed")
    results: list[AgentTaskResult] = Field(
        default_factory=list,
        description="Agent task results",
    )
    synthesized_result: dict[str, Any] = Field(
        default_factory=dict,
        description="Synthesized multi-agent result",
    )
    execution_log: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Execution event log",
    )


class MeshGraphNode(BaseModel):  # type: ignore
    """Node in the mesh connectivity graph."""

    agent_id: str = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    agent_type: str = Field(..., description="Agent type")
    status: str = Field(..., description="Agent status")
    connections: int = Field(..., description="Number of connections")


class MeshGraphLink(BaseModel):  # type: ignore
    """Link in the mesh connectivity graph."""

    source: str = Field(..., description="Source agent ID")
    target: str = Field(..., description="Target agent ID")
    link_type: str = Field(..., description="Link type")
    weight: float = Field(..., description="Link weight")


class MeshGraphResponse(BaseModel):  # type: ignore
    """Response containing mesh connectivity graph."""

    timestamp: str = Field(..., description="Graph snapshot timestamp (ISO 8601)")
    node_count: int = Field(..., description="Number of nodes")
    link_count: int = Field(..., description="Number of links")
    nodes: list[MeshGraphNode] = Field(
        default_factory=list,
        description="Graph nodes",
    )
    links: list[MeshGraphLink] = Field(
        default_factory=list,
        description="Graph links",
    )


__all__ = [
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
