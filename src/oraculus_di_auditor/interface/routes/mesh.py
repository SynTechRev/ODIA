"""API routes for Agent Mesh.

Endpoints for agent registration, mesh execution, and connectivity graph.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import FastAPI dependencies
try:
    from fastapi import APIRouter

    from ...mesh import (
        AgentRegistrationRequest,
        MeshCoordinator,
        MeshExecutionRequest,
    )

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object  # type: ignore

# Initialize mesh coordinator
mesh_coordinator = MeshCoordinator() if FASTAPI_AVAILABLE else None

# Create router
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/mesh", tags=["mesh"])
else:
    router = None  # type: ignore


def register_agent_handler(request: dict[str, Any]) -> dict[str, Any]:
    """Register a new agent in the mesh.

    Args:
        request: Agent registration request

    Returns:
        Registration result with agent_id
    """
    if not mesh_coordinator:
        return {"error": "Mesh coordinator not available"}

    return mesh_coordinator.register_agent(
        agent_name=request.get("agent_name", "UnknownAgent"),
        agent_type=request.get("agent_type", "specialist"),
        capabilities=request.get("capabilities", []),
        version=request.get("version", "1.0.0"),
        priority=request.get("priority", 0),
        max_concurrent_tasks=request.get("max_concurrent_tasks", 10),
        metadata=request.get("metadata"),
    )


def execute_mesh_job_handler(request: dict[str, Any]) -> dict[str, Any]:
    """Execute a multi-agent mesh job.

    Args:
        request: Mesh execution request

    Returns:
        Execution result with synthesized output
    """
    if not mesh_coordinator:
        return {"error": "Mesh coordinator not available"}

    return mesh_coordinator.execute_mesh_job(
        job_type=request.get("job_type", "analysis"),
        documents=request.get("documents", []),
        agents=request.get("agents"),
        options=request.get("options"),
        gcn_validate=request.get("gcn_validate", True),
        governor_check=request.get("governor_check", True),
    )


def get_mesh_graph_handler() -> dict[str, Any]:
    """Get mesh connectivity graph.

    Returns:
        Graph with agent nodes and links
    """
    if not mesh_coordinator:
        return {"error": "Mesh coordinator not available"}

    return mesh_coordinator.get_mesh_graph()


def get_mesh_state_handler() -> dict[str, Any]:
    """Get current mesh state.

    Returns:
        Mesh state summary
    """
    if not mesh_coordinator:
        return {"error": "Mesh coordinator not available"}

    return mesh_coordinator.get_mesh_state()


# Register routes if FastAPI is available
if FASTAPI_AVAILABLE and router:

    @router.post("/agent/register")
    async def mesh_agent_register_endpoint(request: AgentRegistrationRequest):  # type: ignore  # noqa: E501
        """Register agent in mesh.

        Registers a new agent node in the autonomous agent mesh.
        Agent will be available for task routing and execution.
        """
        request_dict = request.dict() if hasattr(request, "dict") else request
        return register_agent_handler(request_dict)

    @router.post("/execute")
    async def mesh_execute_endpoint(request: MeshExecutionRequest):  # type: ignore
        """Execute mesh job.

        Orchestrates multi-agent execution across the mesh.
        Routes tasks, coordinates execution, and synthesizes results.
        """
        request_dict = request.dict() if hasattr(request, "dict") else request
        return execute_mesh_job_handler(request_dict)

    @router.get("/graph")
    async def mesh_graph_endpoint():
        """Get mesh graph.

        Returns the current agent connectivity graph showing
        all nodes (agents) and links between them.
        """
        return get_mesh_graph_handler()

    @router.get("/state")
    async def mesh_state_endpoint():
        """Get mesh state.

        Returns current state of the agent mesh including
        agent count, execution statistics, and health status.
        """
        return get_mesh_state_handler()


__all__ = [
    "router",
    "register_agent_handler",
    "execute_mesh_job_handler",
    "get_mesh_graph_handler",
    "get_mesh_state_handler",
]
