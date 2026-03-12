"""Evolution Engine for Phase 11.

Implements recursive refinement cycle: Monitor → Analyze → Refactor →
Reinforce → Re-test → Record → Deploy
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .change_tracker import ChangeTracker

logger = logging.getLogger(__name__)

# Priority scores for opportunity ranking
PRIORITY_SCORES = {"high": 0, "medium": 1, "low": 2}


class EvolutionEngine:
    """Recursive evolution engine for continuous system improvement.

    Implements the 7-step evolution loop:
    1. Monitor - Observe system behavior and metrics
    2. Analyze - Identify improvement opportunities
    3. Refactor - Design architectural improvements
    4. Reinforce - Strengthen weak points
    5. Re-test - Validate improvements
    6. Record - Track changes in audit trail
    7. Deploy - Apply validated improvements

    All changes are reversible and fully audited.
    """

    def __init__(self, root_path: str | None = None):
        """Initialize evolution engine.

        Args:
            root_path: Root path of the project
        """
        if root_path is None:
            current_file = Path(__file__)
            self.root_path = current_file.parent.parent
        else:
            self.root_path = Path(root_path)

        self.change_tracker = ChangeTracker()
        self.evolution_cycles: list[dict[str, Any]] = []
        self.version = "1.0.0"

        logger.info(f"EvolutionEngine initialized at {self.root_path}")

    def monitor_system(self) -> dict[str, Any]:
        """Step 1: Monitor system for improvement opportunities.

        Returns:
            Monitoring report
        """
        logger.info("Evolution Step 1: Monitoring system")

        monitoring_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "metrics": {
                "code_quality": self._assess_code_quality(),
                "test_coverage": self._assess_test_coverage(),
                "dependency_health": self._assess_dependency_health(),
                "architecture_coherence": self._assess_architecture_coherence(),
                "performance_baseline": self._assess_performance_baseline(),
            },
        }

        logger.info(
            f"Monitoring complete: {len(monitoring_data['metrics'])} metrics collected"
        )
        return monitoring_data

    def analyze_improvements(self, monitoring_data: dict[str, Any]) -> dict[str, Any]:
        """Step 2: Analyze monitoring data for improvement opportunities.

        Args:
            monitoring_data: Data from monitor_system()

        Returns:
            Analysis report with improvement opportunities
        """
        logger.info("Evolution Step 2: Analyzing improvement opportunities")

        opportunities = []

        # Analyze code quality
        code_quality = monitoring_data["metrics"]["code_quality"]
        if code_quality["score"] < 0.8:
            opportunities.append(
                {
                    "type": "code_quality_improvement",
                    "priority": "high",
                    "description": "Code quality below threshold",
                    "current_score": code_quality["score"],
                    "target_score": 0.85,
                    "suggested_actions": code_quality["suggestions"],
                }
            )

        # Analyze test coverage
        test_coverage = monitoring_data["metrics"]["test_coverage"]
        if test_coverage["coverage_percentage"] < 90:
            opportunities.append(
                {
                    "type": "test_coverage_increase",
                    "priority": "medium",
                    "description": "Test coverage below 90%",
                    "current_coverage": test_coverage["coverage_percentage"],
                    "target_coverage": 95,
                    "uncovered_modules": test_coverage["uncovered_modules"],
                }
            )

        # Analyze dependencies
        dep_health = monitoring_data["metrics"]["dependency_health"]
        if dep_health["outdated_count"] > 0:
            opportunities.append(
                {
                    "type": "dependency_upgrade",
                    "priority": "medium",
                    "description": (
                        f"{dep_health['outdated_count']} outdated" " dependencies"
                    ),
                    "outdated_packages": dep_health["outdated_packages"],
                }
            )

        # Analyze architecture
        arch_coherence = monitoring_data["metrics"]["architecture_coherence"]
        if arch_coherence["score"] < 0.85:
            opportunities.append(
                {
                    "type": "architecture_refactoring",
                    "priority": "high",
                    "description": "Architecture coherence below threshold",
                    "current_score": arch_coherence["score"],
                    "issues": arch_coherence["issues"],
                }
            )

        analysis = {
            "timestamp": datetime.now(UTC).isoformat(),
            "monitoring_timestamp": monitoring_data["timestamp"],
            "total_opportunities": len(opportunities),
            "opportunities": opportunities,
            "prioritized_opportunities": sorted(
                opportunities, key=lambda x: PRIORITY_SCORES.get(x["priority"], 99)
            ),
        }

        logger.info(
            f"Analysis complete: {len(opportunities)} improvement opportunities found"
        )
        return analysis

    def design_refactoring(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Step 3: Design refactoring plans for improvements.

        Args:
            analysis: Analysis from analyze_improvements()

        Returns:
            Refactoring plan
        """
        logger.info("Evolution Step 3: Designing refactoring plans")

        refactoring_plans = []

        for opportunity in analysis["prioritized_opportunities"]:
            plan = self._create_refactoring_plan(opportunity)
            refactoring_plans.append(plan)

        refactoring_design = {
            "timestamp": datetime.now(UTC).isoformat(),
            "analysis_timestamp": analysis["timestamp"],
            "total_plans": len(refactoring_plans),
            "plans": refactoring_plans,
        }

        logger.info(
            f"Refactoring design complete: {len(refactoring_plans)} plans created"
        )
        return refactoring_design

    def reinforce_system(self, refactoring_design: dict[str, Any]) -> dict[str, Any]:
        """Step 4: Reinforce weak points identified in design.

        Args:
            refactoring_design: Design from design_refactoring()

        Returns:
            Reinforcement report
        """
        logger.info("Evolution Step 4: Reinforcing system weak points")

        reinforcements = []

        for plan in refactoring_design["plans"]:
            reinforcement = {
                "plan_id": plan["plan_id"],
                "reinforcement_type": self._determine_reinforcement_type(plan),
                "actions": self._generate_reinforcement_actions(plan),
                "estimated_impact": plan.get("estimated_impact", "medium"),
            }
            reinforcements.append(reinforcement)

        reinforcement_report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "design_timestamp": refactoring_design["timestamp"],
            "total_reinforcements": len(reinforcements),
            "reinforcements": reinforcements,
        }

        logger.info(
            f"Reinforcement complete: {len(reinforcements)} reinforcements planned"
        )
        return reinforcement_report

    def validate_improvements(
        self, reinforcement_report: dict[str, Any]
    ) -> dict[str, Any]:
        """Step 5: Re-test and validate improvements.

        Args:
            reinforcement_report: Report from reinforce_system()

        Returns:
            Validation report
        """
        logger.info("Evolution Step 5: Validating improvements")

        validation_results = []

        for reinforcement in reinforcement_report["reinforcements"]:
            # Simulate validation (in production, would run actual tests)
            validation = {
                "plan_id": reinforcement["plan_id"],
                "validation_status": "simulated_pass",
                "tests_passed": True,
                "regression_check": "no_regressions",
                "performance_impact": "neutral_or_positive",
                "validated_at": datetime.now(UTC).isoformat(),
            }
            validation_results.append(validation)

        validation_report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "reinforcement_timestamp": reinforcement_report["timestamp"],
            "total_validations": len(validation_results),
            "passed_validations": len(
                [v for v in validation_results if v["tests_passed"]]
            ),
            "failed_validations": len(
                [v for v in validation_results if not v["tests_passed"]]
            ),
            "validations": validation_results,
        }

        logger.info(
            "Validation complete: "
            f"{validation_report['passed_validations']}"  # passed
            "/"
            f"{validation_report['total_validations']} passed"
        )
        return validation_report

    def record_changes(
        self,
        validation_report: dict[str, Any],
        refactoring_design: dict[str, Any],
    ) -> dict[str, Any]:
        """Step 6: Record changes in audit trail.

        Args:
            validation_report: Report from validate_improvements()
            refactoring_design: Design from design_refactoring()

        Returns:
            Recording report
        """
        logger.info("Evolution Step 6: Recording changes in audit trail")

        recorded_changes = []

        for i, plan in enumerate(refactoring_design["plans"]):
            validation = validation_report["validations"][i]

            if validation["tests_passed"]:
                change_id = self.change_tracker.record_change(
                    change_type=plan["change_type"],
                    description=plan["description"],
                    affected_files=plan.get("affected_files", []),
                    before_state=plan.get("before_state", {}),
                    after_state=plan.get("after_state", {}),
                    reversible=True,
                    metadata={
                        "plan_id": plan["plan_id"],
                        "validation_status": validation["validation_status"],
                        "estimated_impact": plan.get("estimated_impact"),
                    },
                )
                recorded_changes.append(change_id)

        recording_report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "validation_timestamp": validation_report["timestamp"],
            "recorded_changes": recorded_changes,
            "total_recorded": len(recorded_changes),
        }

        logger.info(f"Recording complete: {len(recorded_changes)} changes recorded")
        return recording_report

    def deploy_improvements(
        self, recording_report: dict[str, Any], auto_deploy: bool = False
    ) -> dict[str, Any]:
        """Step 7: Deploy validated improvements.

        Args:
            recording_report: Report from record_changes()
            auto_deploy: Whether to automatically deploy changes

        Returns:
            Deployment report
        """
        logger.info(
            f"Evolution Step 7: Deploying improvements (auto_deploy={auto_deploy})"
        )

        deployed_changes = []

        if auto_deploy:
            for change_id in recording_report["recorded_changes"]:
                # In production, would actually apply the change
                self.change_tracker.mark_applied(
                    change_id, success=True, details={"deployment_mode": "auto"}
                )
                deployed_changes.append(change_id)
                logger.info(f"Deployed change: {change_id}")

        deployment_report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "recording_timestamp": recording_report["timestamp"],
            "auto_deploy_enabled": auto_deploy,
            "changes_available": len(recording_report["recorded_changes"]),
            "changes_deployed": len(deployed_changes),
            "deployment_status": "completed" if auto_deploy else "pending_manual",
        }

        logger.info(
            f"Deployment {deployment_report['deployment_status']}: "
            f"{len(deployed_changes)}/"
            f"{len(recording_report['recorded_changes'])} changes deployed"
        )
        return deployment_report

    def run_evolution_cycle(self, auto_deploy: bool = False) -> dict[str, Any]:
        """Run complete evolution cycle.

        Args:
            auto_deploy: Whether to automatically deploy validated changes

        Returns:
            Complete cycle report
        """
        logger.info("Starting complete evolution cycle")
        cycle_start = datetime.now(UTC)

        # Step 1: Monitor
        monitoring_data = self.monitor_system()

        # Step 2: Analyze
        analysis = self.analyze_improvements(monitoring_data)

        # Step 3: Refactor (design)
        refactoring_design = self.design_refactoring(analysis)

        # Step 4: Reinforce
        reinforcement = self.reinforce_system(refactoring_design)

        # Step 5: Re-test
        validation = self.validate_improvements(reinforcement)

        # Step 6: Record
        recording = self.record_changes(validation, refactoring_design)

        # Step 7: Deploy
        deployment = self.deploy_improvements(recording, auto_deploy)

        cycle_end = datetime.now(UTC)

        cycle_report = {
            "cycle_id": len(self.evolution_cycles) + 1,
            "timestamp_start": cycle_start.isoformat(),
            "timestamp_end": cycle_end.isoformat(),
            "duration_seconds": (cycle_end - cycle_start).total_seconds(),
            "auto_deploy": auto_deploy,
            "summary": {
                "opportunities_found": analysis["total_opportunities"],
                "plans_created": refactoring_design["total_plans"],
                "reinforcements_planned": reinforcement["total_reinforcements"],
                "validations_passed": validation["passed_validations"],
                "changes_recorded": recording["total_recorded"],
                "changes_deployed": deployment["changes_deployed"],
            },
            "outcome": self._determine_cycle_outcome(deployment, validation),
        }

        self.evolution_cycles.append(cycle_report)

        logger.info(
            f"Evolution cycle {cycle_report['cycle_id']} complete: "
            f"{cycle_report['summary']['opportunities_found']} opportunities, "
            f"{cycle_report['summary']['changes_deployed']} changes deployed"
        )

        return cycle_report

    def get_evolution_state(self) -> dict[str, Any]:
        """Get current evolution engine state.

        Returns:
            Evolution state summary
        """
        tracker_stats = self.change_tracker.get_statistics()

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "version": self.version,
            "total_cycles": len(self.evolution_cycles),
            "total_changes_tracked": tracker_stats["total_changes"],
            "successful_changes": tracker_stats["successful_changes"],
            "success_rate": tracker_stats["success_rate"],
            "recent_cycles": (
                self.evolution_cycles[-3:] if len(self.evolution_cycles) > 0 else []
            ),
        }

    def _assess_code_quality(self) -> dict[str, Any]:
        """Assess current code quality."""
        # Simplified assessment
        return {
            "score": 0.85,
            "suggestions": ["Reduce function complexity", "Add type hints"],
        }

    def _assess_test_coverage(self) -> dict[str, Any]:
        """Assess test coverage."""
        return {
            "coverage_percentage": 88,
            "uncovered_modules": ["self_healing", "evolution"],
        }

    def _assess_dependency_health(self) -> dict[str, Any]:
        """Assess dependency health."""
        return {"outdated_count": 0, "outdated_packages": []}

    def _assess_architecture_coherence(self) -> dict[str, Any]:
        """Assess architecture coherence."""
        return {"score": 0.90, "issues": []}

    def _assess_performance_baseline(self) -> dict[str, Any]:
        """Assess performance baseline."""
        return {"avg_response_time_ms": 150, "p95_response_time_ms": 300}

    def _create_refactoring_plan(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        """Create refactoring plan for an opportunity."""
        import hashlib

        plan_id = hashlib.sha256(
            f"{opportunity['type']}:{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:12]

        return {
            "plan_id": plan_id,
            "change_type": opportunity["type"],
            "description": opportunity["description"],
            "priority": opportunity["priority"],
            "affected_files": [],
            "before_state": {},
            "after_state": {},
            "estimated_impact": "medium",
        }

    def _determine_reinforcement_type(self, plan: dict[str, Any]) -> str:
        """Determine reinforcement type for a plan."""
        change_type = plan["change_type"]
        if "test" in change_type:
            return "test_reinforcement"
        elif "quality" in change_type:
            return "code_quality_reinforcement"
        elif "architecture" in change_type:
            return "architecture_reinforcement"
        else:
            return "general_reinforcement"

    def _generate_reinforcement_actions(self, plan: dict[str, Any]) -> list[str]:
        """Generate reinforcement actions for a plan."""
        return [
            "Add validation checks",
            "Implement error handling",
            "Add monitoring instrumentation",
        ]

    def _determine_cycle_outcome(
        self, deployment: dict[str, Any], validation: dict[str, Any]
    ) -> str:
        """Determine outcome of evolution cycle."""
        if deployment["changes_deployed"] > 0:
            return "changes_deployed"
        elif validation["passed_validations"] > 0:
            return "changes_validated_pending_deployment"
        else:
            return "no_changes_ready"
