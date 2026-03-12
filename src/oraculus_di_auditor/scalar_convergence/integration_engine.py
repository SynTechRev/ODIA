"""Integration Engine for Phase 12.

Produces comprehensive integration plans for unifying all system layers
into the scalar-convergent architecture.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class IntegrationTask:
    """Represents a single integration task."""

    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        category: str,
        priority: str,
        dependencies: list[str],
        estimated_effort: str,
        impact: str,
    ):
        """Initialize integration task.

        Args:
            task_id: Unique task identifier
            title: Task title
            description: Detailed description
            category: Task category (code, schema, test, docs, etc.)
            priority: critical, high, medium, low
            dependencies: List of task IDs this depends on
            estimated_effort: hours, days, weeks
            impact: Expected impact on system
        """
        self.task_id = task_id
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.dependencies = dependencies
        self.estimated_effort = estimated_effort
        self.impact = impact
        self.status = "pending"
        self.created_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "estimated_effort": self.estimated_effort,
            "impact": self.impact,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class IntegrationEngine:
    """Integration Engine for Phase 12.

    Generates comprehensive integration plans that specify:
    - Required code adjustments
    - Module integration maps
    - Interface schemas
    - New tests
    - CI enhancements
    - Mesh updates
    - Evolutionary cycle adjustments
    - Prevention guard updates
    - Missing documentation
    """

    def __init__(
        self,
        hours_per_day: float = 8.0,
        hours_per_week: float = 40.0,
    ):
        """Initialize integration engine.

        Args:
            hours_per_day: Working hours per day for effort estimation.
                Default 8.0 (standard workday).
            hours_per_week: Working hours per week for effort estimation.
                Default 40.0 (standard workweek).
        """
        self.version = "1.0.0"
        self.tasks: list[IntegrationTask] = []
        self.hours_per_day = hours_per_day
        self.hours_per_week = hours_per_week

        logger.info("IntegrationEngine initialized")

    def generate_integration_plan(
        self, srm_report: dict[str, Any], coherence_report: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate comprehensive integration plan.

        Args:
            srm_report: Scalar Recursive Map report
            coherence_report: Coherence audit report

        Returns:
            Complete integration plan
        """
        logger.info("Generating integration plan")

        self.tasks = []

        # Generate tasks based on analysis
        self._generate_code_adjustment_tasks(coherence_report)
        self._generate_schema_integration_tasks(srm_report)
        self._generate_test_tasks(srm_report)
        self._generate_ci_enhancement_tasks()
        self._generate_mesh_update_tasks()
        self._generate_evolution_adjustment_tasks()
        self._generate_prevention_guard_tasks()
        self._generate_documentation_tasks(coherence_report)

        # Build integration plan
        plan = self._build_integration_plan()

        logger.info(f"Integration plan generated with {len(self.tasks)} tasks")

        return plan

    def _generate_code_adjustment_tasks(self, coherence_report: dict[str, Any]):
        """Generate code adjustment tasks based on coherence issues."""
        # Task for redundancy elimination
        self.tasks.append(
            IntegrationTask(
                task_id="CODE-001",
                title="Eliminate Redundant Pipeline Logic",
                description="Consolidate document processing pipeline logic from analysis.pipeline and orchestrator.orchestrator into single canonical implementation",
                category="code_adjustment",
                priority="medium",
                dependencies=[],
                estimated_effort="4 hours",
                impact="Reduces code duplication and maintenance burden",
            )
        )

        # Task for dependency injection
        self.tasks.append(
            IntegrationTask(
                task_id="CODE-002",
                title="Implement Dependency Injection for GCN Service",
                description="Refactor mesh coordinator to use dependency injection for GCN service instead of direct instantiation",
                category="code_adjustment",
                priority="medium",
                dependencies=[],
                estimated_effort="2 hours",
                impact="Improves testability and reduces coupling",
            )
        )

        # Task for result synthesis consolidation
        self.tasks.append(
            IntegrationTask(
                task_id="CODE-003",
                title="Consolidate Result Synthesis Logic",
                description="Move all result aggregation logic to mesh.synthesis_engine, update orchestrator to delegate",
                category="code_adjustment",
                priority="medium",
                dependencies=[],
                estimated_effort="3 hours",
                impact="Ensures consistent result formats across system",
            )
        )

    def _generate_schema_integration_tasks(self, srm_report: dict[str, Any]):
        """Generate schema integration tasks."""
        self.tasks.append(
            IntegrationTask(
                task_id="SCHEMA-001",
                title="Create Scalar Layer Schema",
                description="Define Pydantic schemas for all 7 scalar layers with validation rules",
                category="schema",
                priority="high",
                dependencies=[],
                estimated_effort="4 hours",
                impact="Enables type-safe layer interactions",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="SCHEMA-002",
                title="Standardize Version Format",
                description="Create centralized version schema and update all components to use consistent format (v1.0.0)",
                category="schema",
                priority="low",
                dependencies=[],
                estimated_effort="2 hours",
                impact="Improves consistency in version reporting",
            )
        )

    def _generate_test_tasks(self, srm_report: dict[str, Any]):
        """Generate testing tasks."""
        self.tasks.append(
            IntegrationTask(
                task_id="TEST-001",
                title="Create Scalar Recursive Map Tests",
                description="Write comprehensive tests for ScalarRecursiveMap class covering all 7 layers and dependencies",
                category="test",
                priority="high",
                dependencies=["SCHEMA-001"],
                estimated_effort="3 hours",
                impact="Ensures SRM correctness and stability",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="TEST-002",
                title="Create Coherence Auditor Tests",
                description="Write tests for CoherenceAuditor covering all audit categories",
                category="test",
                priority="high",
                dependencies=[],
                estimated_effort="3 hours",
                impact="Validates coherence checking logic",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="TEST-003",
                title="Create Integration Engine Tests",
                description="Write tests for IntegrationEngine task generation and planning",
                category="test",
                priority="high",
                dependencies=[],
                estimated_effort="2 hours",
                impact="Ensures integration planning correctness",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="TEST-004",
                title="Create Phase 12 Service Tests",
                description="Write comprehensive tests for Phase12Service orchestration",
                category="test",
                priority="high",
                dependencies=["TEST-001", "TEST-002", "TEST-003"],
                estimated_effort="3 hours",
                impact="Validates Phase 12 end-to-end functionality",
            )
        )

    def _generate_ci_enhancement_tasks(self):
        """Generate CI/CD enhancement tasks."""
        self.tasks.append(
            IntegrationTask(
                task_id="CI-001",
                title="Add Phase 12 to CI Pipeline",
                description="Update GitHub Actions workflow to include Phase 12 tests and validation",
                category="ci",
                priority="high",
                dependencies=["TEST-001", "TEST-002", "TEST-003", "TEST-004"],
                estimated_effort="1 hour",
                impact="Ensures Phase 12 is continuously validated",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="CI-002",
                title="Add Coherence Check to CI",
                description="Add coherence audit as CI check that fails on critical issues",
                category="ci",
                priority="medium",
                dependencies=["TEST-002"],
                estimated_effort="1 hour",
                impact="Prevents coherence degradation",
            )
        )

    def _generate_mesh_update_tasks(self):
        """Generate mesh update tasks."""
        self.tasks.append(
            IntegrationTask(
                task_id="MESH-001",
                title="Align Agent Types with Scalar Layers",
                description="Update agent type classification to align with 7-layer scalar model",
                category="mesh_update",
                priority="medium",
                dependencies=["SCHEMA-001"],
                estimated_effort="3 hours",
                impact="Improves conceptual consistency",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="MESH-002",
                title="Add Scalar Layer Routing",
                description="Enhance routing engine to support layer-aware routing based on SRM",
                category="mesh_update",
                priority="medium",
                dependencies=["MESH-001"],
                estimated_effort="4 hours",
                impact="Enables intelligent layer-based task routing",
            )
        )

    def _generate_evolution_adjustment_tasks(self):
        """Generate evolutionary cycle adjustment tasks."""
        self.tasks.append(
            IntegrationTask(
                task_id="EVOL-001",
                title="Integrate SRM into Evolution Engine",
                description="Update evolution engine to use SRM for understanding system structure",
                category="evolution_adjustment",
                priority="medium",
                dependencies=["SCHEMA-001"],
                estimated_effort="3 hours",
                impact="Enables layer-aware evolution",
            )
        )

    def _generate_prevention_guard_tasks(self):
        """Generate prevention guard update tasks."""
        self.tasks.append(
            IntegrationTask(
                task_id="GUARD-001",
                title="Add Coherence Guards",
                description="Create prevention guards that check for coherence violations",
                category="prevention_guard",
                priority="medium",
                dependencies=["TEST-002"],
                estimated_effort="3 hours",
                impact="Prevents coherence degradation",
            )
        )

    def _generate_documentation_tasks(self, coherence_report: dict[str, Any]):
        """Generate documentation tasks."""
        self.tasks.append(
            IntegrationTask(
                task_id="DOC-001",
                title="Create PHASE12_OVERVIEW.md",
                description="Write comprehensive Phase 12 overview document following format of Phase 10/11",
                category="documentation",
                priority="high",
                dependencies=[],
                estimated_effort="4 hours",
                impact="Documents Phase 12 for users and developers",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="DOC-002",
                title="Create Phase 1-4 Overview Documents",
                description="Write PHASE1-4_OVERVIEW.md documents for consistency",
                category="documentation",
                priority="low",
                dependencies=[],
                estimated_effort="8 hours",
                impact="Improves documentation completeness",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="DOC-003",
                title="Update README with Phase 12",
                description="Update README to reflect Phase 12 completion and current test count",
                category="documentation",
                priority="high",
                dependencies=["DOC-001"],
                estimated_effort="1 hour",
                impact="Keeps README current",
            )
        )

        self.tasks.append(
            IntegrationTask(
                task_id="DOC-004",
                title="Create Scalar Architecture Guide",
                description="Write comprehensive guide explaining scalar-convergent architecture and its benefits",
                category="documentation",
                priority="medium",
                dependencies=["DOC-001"],
                estimated_effort="6 hours",
                impact="Helps developers understand scalar model",
            )
        )

    def _build_integration_plan(self) -> dict[str, Any]:
        """Build complete integration plan from tasks.

        Returns:
            Structured integration plan
        """
        # Group tasks by category
        categories: dict[str, list[IntegrationTask]] = {}
        for task in self.tasks:
            if task.category not in categories:
                categories[task.category] = []
            categories[task.category].append(task)

        # Calculate total effort using configurable hours
        effort_hours = 0
        effort_mapping = {
            "hour": 1,
            "hours": 1,
            "day": self.hours_per_day,
            "days": self.hours_per_day,
            "week": self.hours_per_week,
            "weeks": self.hours_per_week,
        }

        for task in self.tasks:
            parts = task.estimated_effort.split()
            if len(parts) >= 2:
                value = float(parts[0])
                unit = parts[1].lower()
                multiplier = effort_mapping.get(unit, 1)
                effort_hours += value * multiplier

        # Build dependency graph
        dependency_graph = {
            "nodes": [task.task_id for task in self.tasks],
            "edges": [
                {"from": task.task_id, "to": dep}
                for task in self.tasks
                for dep in task.dependencies
            ],
        }

        # Determine execution phases
        execution_phases = self._determine_execution_phases()

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "version": self.version,
            "summary": {
                "total_tasks": len(self.tasks),
                "categories": {cat: len(tasks) for cat, tasks in categories.items()},
                "estimated_total_hours": round(effort_hours, 1),
                "estimated_days": round(effort_hours / 8, 1),
            },
            "tasks_by_category": {
                cat: [task.to_dict() for task in tasks]
                for cat, tasks in categories.items()
            },
            "all_tasks": [task.to_dict() for task in self.tasks],
            "dependency_graph": dependency_graph,
            "execution_phases": execution_phases,
            "critical_path": self._identify_critical_path(),
        }

    def _determine_execution_phases(self) -> list[dict[str, Any]]:
        """Determine execution phases based on dependencies.

        Returns:
            List of execution phases
        """
        phases = []

        # Phase 1: Foundation (no dependencies)
        phase1_tasks = [task for task in self.tasks if not task.dependencies]
        if phase1_tasks:
            phases.append(
                {
                    "phase_id": 1,
                    "name": "Foundation",
                    "description": "Initial setup and independent tasks",
                    "tasks": [task.task_id for task in phase1_tasks],
                }
            )

        # Phase 2: Integration (depends on Phase 1)
        phase1_ids = {task.task_id for task in phase1_tasks}
        phase2_tasks = [
            task
            for task in self.tasks
            if task.dependencies and set(task.dependencies).issubset(phase1_ids)
        ]
        if phase2_tasks:
            phases.append(
                {
                    "phase_id": 2,
                    "name": "Integration",
                    "description": "Core integration tasks",
                    "tasks": [task.task_id for task in phase2_tasks],
                }
            )

        # Phase 3: Completion (all other tasks)
        phase12_ids = phase1_ids | {task.task_id for task in phase2_tasks}
        phase3_tasks = [task for task in self.tasks if task.task_id not in phase12_ids]
        if phase3_tasks:
            phases.append(
                {
                    "phase_id": 3,
                    "name": "Completion",
                    "description": "Final integration and documentation",
                    "tasks": [task.task_id for task in phase3_tasks],
                }
            )

        return phases

    def _identify_critical_path(self) -> list[str]:
        """Identify the critical path through the task graph.

        Note: This is a simplified implementation that returns tasks with
        the most dependencies rather than a true Critical Path Method (CPM)
        algorithm. A full CPM would consider task duration and calculate
        the longest path through the dependency network. This simplified
        approach is sufficient for initial planning and prioritization.

        Returns:
            List of task IDs on critical path (top 5 most dependent tasks)
        """
        # Simplified critical path: tasks with most dependencies
        dependency_counts = {}
        for task in self.tasks:
            dependency_counts[task.task_id] = len(task.dependencies)

        # Sort by dependency count (descending)
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: dependency_counts[t.task_id],
            reverse=True,
        )

        # Return top 5 most dependent tasks
        return [task.task_id for task in sorted_tasks[:5]]
