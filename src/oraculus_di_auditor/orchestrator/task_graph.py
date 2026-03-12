"""Task graph management for Phase 5 orchestration.

This module provides task dependency tracking, scheduling, and execution ordering
for multi-agent workflows.
"""

from __future__ import annotations

from typing import Any


class TaskNode:
    """Represents a single task in the execution graph."""

    def __init__(
        self,
        task_id: str,
        agent_name: str,
        action: str,
        inputs: dict[str, Any],
        dependencies: list[str] | None = None,
    ):
        """Initialize task node.

        Args:
            task_id: Unique task identifier
            agent_name: Name of agent to execute this task
            action: Action to perform
            inputs: Input parameters for the task
            dependencies: List of task IDs this task depends on
        """
        self.task_id = task_id
        self.agent_name = agent_name
        self.action = action
        self.inputs = inputs
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, running, completed, failed
        self.result: dict[str, Any] | None = None
        self.error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert task node to dictionary."""
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "inputs": self.inputs,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class TaskGraph:
    """Manages task dependencies and execution order.

    Provides topological sorting, dependency resolution, and parallel
    execution planning for multi-agent workflows.
    """

    def __init__(self):
        """Initialize empty task graph."""
        self.tasks: dict[str, TaskNode] = {}
        self.execution_order: list[list[str]] = []

    def add_task(
        self,
        task_id: str,
        agent_name: str,
        action: str,
        inputs: dict[str, Any],
        dependencies: list[str] | None = None,
    ) -> None:
        """Add a task to the graph.

        Args:
            task_id: Unique task identifier
            agent_name: Name of agent to execute this task
            action: Action to perform
            inputs: Input parameters for the task
            dependencies: List of task IDs this task depends on
        """
        if task_id in self.tasks:
            raise ValueError(f"Task {task_id} already exists in graph")

        # Validate dependencies exist
        deps = dependencies or []
        for dep_id in deps:
            if dep_id not in self.tasks:
                raise ValueError(f"Dependency {dep_id} not found for task {task_id}")

        self.tasks[task_id] = TaskNode(
            task_id, agent_name, action, inputs, dependencies
        )

    def compute_execution_order(self) -> list[list[str]]:
        """Compute execution order using topological sort.

        Returns tasks grouped by execution level, where all tasks in a level
        can be executed in parallel.

        Returns:
            List of task ID lists, where each inner list is a parallel batch

        Raises:
            ValueError: If circular dependencies are detected
        """
        # Build dependency count and reverse dependency map
        in_degree = {task_id: 0 for task_id in self.tasks}
        for task in self.tasks.values():
            for _dep_id in task.dependencies:
                in_degree[task.task_id] += 1

        # Find tasks with no dependencies (can run immediately)
        execution_levels: list[list[str]] = []
        ready_queue = [task_id for task_id, degree in in_degree.items() if degree == 0]

        completed = set()
        while ready_queue:
            # All tasks in ready_queue can execute in parallel
            execution_levels.append(ready_queue[:])

            # Mark these tasks as completed
            for task_id in ready_queue:
                completed.add(task_id)

            # Find next set of ready tasks
            next_ready = []
            for task_id in self.tasks:
                if task_id in completed:
                    continue

                task = self.tasks[task_id]
                if all(dep_id in completed for dep_id in task.dependencies):
                    next_ready.append(task_id)

            ready_queue = next_ready

        # Check if all tasks were scheduled
        if len(completed) != len(self.tasks):
            unscheduled = set(self.tasks.keys()) - completed
            raise ValueError(
                f"Circular dependency detected. Unscheduled tasks: {unscheduled}"
            )

        self.execution_order = execution_levels
        return execution_levels

    def get_execution_mode(self) -> str:
        """Determine execution mode based on graph structure.

        Returns:
            "sequential" if all tasks must run in order,
            "parallel" if all tasks can run simultaneously,
            "hybrid" if there's a mix
        """
        if not self.execution_order:
            self.compute_execution_order()

        if len(self.execution_order) == 1:
            return "parallel"
        elif all(len(level) == 1 for level in self.execution_order):
            return "sequential"
        else:
            return "hybrid"

    def get_task(self, task_id: str) -> TaskNode:
        """Get task node by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task node

        Raises:
            KeyError: If task not found
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found in graph")
        return self.tasks[task_id]

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Update task status and result.

        Args:
            task_id: Task identifier
            status: New status (pending, running, completed, failed)
            result: Task result (if completed)
            error: Error message (if failed)
        """
        task = self.get_task(task_id)
        task.status = status
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error

    def get_ready_tasks(self) -> list[str]:
        """Get tasks that are ready to execute.

        Returns tasks whose dependencies are all completed and status is pending.

        Returns:
            List of task IDs ready to execute
        """
        ready = []
        for task_id, task in self.tasks.items():
            if task.status != "pending":
                continue

            # Check if all dependencies are completed
            all_deps_complete = all(
                self.tasks[dep_id].status == "completed" for dep_id in task.dependencies
            )

            if all_deps_complete:
                ready.append(task_id)

        return ready

    def to_dict(self) -> dict[str, Any]:
        """Convert task graph to dictionary.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "execution_order": self.execution_order,
            "execution_mode": self.get_execution_mode(),
            "total_tasks": len(self.tasks),
            "completed_tasks": sum(
                1 for task in self.tasks.values() if task.status == "completed"
            ),
        }


__all__ = ["TaskNode", "TaskGraph"]
