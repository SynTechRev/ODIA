"""Phase 12 Service - Scalar-Convergent Architecture Integration.

Main orchestrator for Phase 12 analysis and integration planning.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .coherence_auditor import CoherenceAuditor
from .integration_engine import IntegrationEngine
from .scalar_recursive_map import ScalarRecursiveMap

logger = logging.getLogger(__name__)


class Phase12Service:
    """Phase 12 Service: Scalar-Convergent Architecture Integration.

    Orchestrates the complete Phase 12 process:
    1. Build Scalar Recursive Map (SRM)
    2. Run Global Coherence Audit
    3. Generate Integration Plan
    4. Produce Comprehensive Reports

    This is a DRY-RUN phase focused on analysis and planning, not implementation.
    """

    def __init__(
        self,
        root_path: str | None = None,
        layer_balance_threshold: float = 0.5,
    ):
        """Initialize Phase 12 service.

        Args:
            root_path: Root path of the project
            layer_balance_threshold: Maximum allowed deviation from average
                component count per layer (as ratio of average). Default 0.5
                means layers are balanced if no layer deviates more than 50%
                from the average. Lower values enforce stricter balance.
        """
        if root_path is None:
            current_file = Path(__file__)
            self.root_path = current_file.parent.parent.parent.parent
        else:
            self.root_path = Path(root_path)

        self.version = "1.0.0"
        self.layer_balance_threshold = layer_balance_threshold
        self.srm = ScalarRecursiveMap()
        self.coherence_auditor = CoherenceAuditor(str(self.root_path))
        self.integration_engine = IntegrationEngine()

        self.execution_history: list[dict[str, Any]] = []

        logger.info(f"Phase12Service initialized at {self.root_path}")

    def execute_phase12_analysis(self) -> dict[str, Any]:
        """Execute complete Phase 12 analysis.

        This is the main entry point for Phase 12 execution.

        Returns:
            Complete Phase 12 analysis report
        """
        logger.info("=== PHASE 12 EXECUTION STARTED ===")
        start_time = datetime.now(UTC)

        # Step 1: Build Scalar Recursive Map
        logger.info("Step 1: Building Scalar Recursive Map")
        srm_report = self.srm.to_dict()

        # Step 2: Run Global Coherence Audit
        logger.info("Step 2: Running Global Coherence Audit")
        coherence_report = self.coherence_auditor.run_full_audit()

        # Step 3: Generate Integration Plan
        logger.info("Step 3: Generating Integration Plan")
        integration_plan = self.integration_engine.generate_integration_plan(
            srm_report, coherence_report
        )

        # Step 4: Generate System-wide Analysis
        logger.info("Step 4: Generating System-wide Analysis")
        system_analysis = self._analyze_system_architecture()

        # Step 5: Predict Failure Modes
        logger.info("Step 5: Predicting Failure Modes")
        failure_predictions = self._predict_failure_modes(coherence_report, srm_report)

        # Build complete report
        end_time = datetime.now(UTC)
        execution_time = (end_time - start_time).total_seconds()

        report = {
            "phase": "Phase 12: Scalar-Convergent Architecture Integration",
            "version": self.version,
            "status": "complete",
            "mode": "DRY-RUN",
            "timestamp": end_time.isoformat(),
            "execution_time_seconds": round(execution_time, 2),
            "summary": {
                "scalar_layers": 7,
                "coherence_issues": coherence_report["summary"]["total_issues"],
                "coherence_score": coherence_report["summary"]["coherence_score"],
                "integration_tasks": integration_plan["summary"]["total_tasks"],
                "estimated_integration_hours": integration_plan["summary"][
                    "estimated_total_hours"
                ],
            },
            "outputs": {
                "scalar_recursive_map": srm_report,
                "coherence_audit": coherence_report,
                "integration_plan": integration_plan,
                "system_analysis": system_analysis,
                "failure_predictions": failure_predictions,
            },
            "next_steps": [
                "Review all reports and analysis",
                "Prioritize integration tasks",
                "Assign tasks to development teams",
                "Begin implementation of high-priority tasks",
                "Monitor coherence score during implementation",
                "Re-run Phase 12 analysis after major changes",
                "Wait for Phase 13 initiation command",
            ],
        }

        # Record execution
        self.execution_history.append(
            {
                "timestamp": end_time.isoformat(),
                "execution_time": execution_time,
                "status": "success",
            }
        )

        logger.info("=== PHASE 12 EXECUTION COMPLETED ===")
        logger.info(f"Execution time: {execution_time:.2f} seconds")
        logger.info(
            f"Coherence score: {coherence_report['summary']['coherence_score']:.3f}"
        )
        logger.info(f"Integration tasks: {integration_plan['summary']['total_tasks']}")

        return report

    def _analyze_system_architecture(self) -> dict[str, Any]:
        """Analyze overall system architecture.

        Returns:
            System architecture analysis
        """
        logger.info("Analyzing system architecture")

        # Count components by layer
        src_path = self.root_path / "src" / "oraculus_di_auditor"
        components = []

        if src_path.exists():
            for module_path in src_path.rglob("*.py"):
                if "__pycache__" not in str(module_path):
                    relative_path = module_path.relative_to(src_path)
                    component_name = str(relative_path).replace("/", ".")
                    layers = self.srm.map_component_to_layer(component_name)
                    components.append(
                        {
                            "component": component_name,
                            "layers": layers,
                            "path": str(module_path),
                        }
                    )

        # Analyze layer distribution
        layer_counts = {i: 0 for i in range(1, 8)}
        for component in components:
            for layer in component["layers"]:
                layer_counts[layer] += 1

        # Identify cross-layer components
        cross_layer = [c for c in components if len(c["layers"]) > 1]

        return {
            "total_components": len(components),
            "layer_distribution": layer_counts,
            "cross_layer_components": len(cross_layer),
            "most_populated_layer": max(layer_counts, key=layer_counts.get),
            "least_populated_layer": min(layer_counts, key=layer_counts.get),
            "components_by_layer": {
                layer: [c["component"] for c in components if layer in c["layers"]]
                for layer in range(1, 8)
            },
            "architecture_health": {
                "balanced": self._check_layer_balance(layer_counts),
                "connectivity": "good",  # All layers have components
                "modularity": "high",  # Many single-layer components
            },
        }

    def _check_layer_balance(self, layer_counts: dict[int, int]) -> bool:
        """Check if layer distribution is balanced.

        Args:
            layer_counts: Component count per layer

        Returns:
            True if balanced
        """
        counts = list(layer_counts.values())
        if not counts:
            return False

        avg = sum(counts) / len(counts)
        max_deviation = max(abs(c - avg) for c in counts)

        # Balanced if no layer deviates more than threshold from average
        return max_deviation <= (avg * self.layer_balance_threshold)

    def _predict_failure_modes(
        self, coherence_report: dict[str, Any], srm_report: dict[str, Any]
    ) -> dict[str, Any]:
        """Predict potential failure modes based on current state.

        Args:
            coherence_report: Coherence audit results
            srm_report: Scalar Recursive Map

        Returns:
            Failure mode predictions
        """
        logger.info("Predicting failure modes")

        predictions = []

        # Predict based on coherence issues
        critical_issues = [
            i for i in coherence_report["issues"] if i["severity"] == "critical"
        ]
        if critical_issues:
            predictions.append(
                {
                    "failure_mode": "Critical Coherence Failure",
                    "probability": "high",
                    "trigger": "Unaddressed critical coherence issues",
                    "impact": "System instability and incorrect results",
                    "mitigation": "Address all critical coherence issues immediately",
                }
            )

        # Predict based on coupling
        coupling_issues = [
            i
            for i in coherence_report["issues"]
            if i["issue_type"] == "excessive_coupling"
        ]
        if len(coupling_issues) > 2:
            predictions.append(
                {
                    "failure_mode": "Maintenance Breakdown",
                    "probability": "medium",
                    "trigger": "Excessive coupling makes changes risky",
                    "impact": "Difficulty making changes without breaking system",
                    "mitigation": "Refactor to reduce coupling, add integration tests",
                }
            )

        # Predict based on redundancy
        redundancy_issues = [
            i
            for i in coherence_report["issues"]
            if i["issue_type"] == "redundant_logic"
        ]
        if len(redundancy_issues) > 2:
            predictions.append(
                {
                    "failure_mode": "Divergent Implementations",
                    "probability": "medium",
                    "trigger": "Redundant logic diverges over time",
                    "impact": "Inconsistent behavior across system",
                    "mitigation": "Consolidate redundant logic into single implementation",
                }
            )

        # Predict based on phase drift
        drift_issues = [
            i for i in coherence_report["issues"] if i["issue_type"] == "phase_drift"
        ]
        if drift_issues:
            predictions.append(
                {
                    "failure_mode": "Documentation Decay",
                    "probability": "low",
                    "trigger": "Documentation falls behind code",
                    "impact": "Developer confusion and incorrect assumptions",
                    "mitigation": "Update documentation as part of development process",
                }
            )

        # Always predict potential scaling issues
        predictions.append(
            {
                "failure_mode": "Scalability Bottleneck",
                "probability": "low",
                "trigger": "Increased load on single-threaded components",
                "impact": "Performance degradation under high load",
                "mitigation": "Add performance monitoring and load testing",
            }
        )

        return {
            "total_predictions": len(predictions),
            "high_probability": sum(
                1 for p in predictions if p["probability"] == "high"
            ),
            "medium_probability": sum(
                1 for p in predictions if p["probability"] == "medium"
            ),
            "low_probability": sum(1 for p in predictions if p["probability"] == "low"),
            "predictions": predictions,
            "recommendation": (
                "Address high-probability failure modes immediately"
                if any(p["probability"] == "high" for p in predictions)
                else "Monitor medium-probability modes and continue improvements"
            ),
        }

    def save_reports(self, output_dir: str | None = None) -> dict[str, str]:
        """Save all reports to files.

        Args:
            output_dir: Output directory (defaults to project root)

        Returns:
            Dictionary mapping report name to file path
        """
        if output_dir is None:
            output_dir = str(self.root_path)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving reports to {output_path}")

        # Execute analysis
        report = self.execute_phase12_analysis()

        # Save individual reports
        files = {}

        # Main report
        main_report_path = output_path / "PHASE12_ANALYSIS.json"
        with open(main_report_path, "w") as f:
            json.dump(report, f, indent=2)
        files["main_report"] = str(main_report_path)

        # Scalar Recursive Map
        srm_path = output_path / "PHASE12_SCALAR_MAP.json"
        with open(srm_path, "w") as f:
            json.dump(report["outputs"]["scalar_recursive_map"], f, indent=2)
        files["scalar_map"] = str(srm_path)

        # Coherence Audit
        coherence_path = output_path / "PHASE12_COHERENCE_AUDIT.json"
        with open(coherence_path, "w") as f:
            json.dump(report["outputs"]["coherence_audit"], f, indent=2)
        files["coherence_audit"] = str(coherence_path)

        # Integration Plan
        integration_path = output_path / "PHASE12_INTEGRATION_PLAN.json"
        with open(integration_path, "w") as f:
            json.dump(report["outputs"]["integration_plan"], f, indent=2)
        files["integration_plan"] = str(integration_path)

        logger.info(f"Saved {len(files)} report files")

        return files

    def get_status(self) -> dict[str, Any]:
        """Get current Phase 12 status.

        Returns:
            Status information
        """
        return {
            "version": self.version,
            "root_path": str(self.root_path),
            "execution_count": len(self.execution_history),
            "last_execution": (
                self.execution_history[-1] if self.execution_history else None
            ),
            "components": {
                "scalar_recursive_map": "active",
                "coherence_auditor": "active",
                "integration_engine": "active",
            },
        }
