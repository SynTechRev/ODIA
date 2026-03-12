"""Self-Healing Service for Phase 11.

Central orchestrator for autonomic detection, correction, and prevention.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .correction_engine import CorrectionEngine
from .detection_engine import DetectionEngine
from .prevention_engine import PreventionEngine

logger = logging.getLogger(__name__)


class SelfHealingService:
    """Central service for autonomic self-healing.

    Orchestrates detection, correction, and prevention engines to maintain
    system health and prevent degradation before it causes failures.

    Philosophy: "Heal before breaking, not after"
    """

    def __init__(self, root_path: str | None = None):
        """Initialize self-healing service.

        Args:
            root_path: Root path of the project
        """
        self.detection_engine = DetectionEngine(root_path)
        self.correction_engine = CorrectionEngine(root_path)
        self.prevention_engine = PreventionEngine()

        self.version = "1.0.0"
        self.healing_cycles: list[dict[str, Any]] = []

        logger.info("SelfHealingService initialized")

    def get_system_health(self) -> dict[str, Any]:
        """Get current system health status.

        Returns:
            System health summary
        """
        logger.info("Getting system health status")

        # Run quick detection
        detection_report = self.detection_engine.run_full_detection()

        # Check guards
        guard_results = self.prevention_engine.check_all_guards({})

        health_score = detection_report["summary"]["health_score"]
        guard_health = (
            guard_results["guards_passed"] / guard_results["total_guards"]
            if guard_results["total_guards"] > 0
            else 1.0
        )

        overall_health = (health_score + guard_health) / 2.0

        # Determine health status
        if overall_health >= 0.9:
            status = "healthy"
        elif overall_health >= 0.7:
            status = "warning"
        elif overall_health >= 0.5:
            status = "degraded"
        else:
            status = "critical"

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "version": self.version,
            "overall_health_score": overall_health,
            "status": status,
            "detection_health_score": health_score,
            "guard_health_score": guard_health,
            "total_issues": detection_report["summary"]["total_issues"],
            "critical_issues": detection_report["summary"]["critical_issues"],
            "guards_passed": guard_results["guards_passed"],
            "guards_failed": guard_results["guards_failed"],
            "healing_cycles_completed": len(self.healing_cycles),
        }

    def run_healing_cycle(self, auto_apply: bool = False) -> dict[str, Any]:
        """Run a complete healing cycle.

        Args:
            auto_apply: If True, automatically apply safe fixes
                (low risk, high confidence)

        Returns:
            Healing cycle report
        """
        logger.info(f"Starting healing cycle (auto_apply={auto_apply})")

        cycle_start = datetime.now(UTC)

        # Step 1: Detection
        logger.info("Step 1: Detection")
        detection_report = self.detection_engine.run_full_detection()

        # Step 2: Correction (propose fixes)
        logger.info("Step 2: Correction (proposing fixes)")
        patch_report = self.correction_engine.generate_patch_report(detection_report)

        # Step 3: Prevention (generate plan)
        logger.info("Step 3: Prevention (generating plan)")
        prevention_plan = self.prevention_engine.generate_prevention_plan(
            detection_report
        )

        # Step 4: Auto-apply safe fixes if enabled
        applied_fixes = []
        if auto_apply:
            logger.info("Step 4: Auto-applying safe fixes")
            for fix in patch_report["prioritized_fixes"]:
                # Only apply low-risk, high-confidence fixes
                if fix.get("risk") == "low" and fix.get("confidence", 0) >= 0.8:
                    result = self.correction_engine.apply_fix(fix)
                    applied_fixes.append(result)
                    logger.info(f"Applied fix: {fix['fix_type']}")

        cycle_end = datetime.now(UTC)

        # Compile cycle report
        cycle_report = {
            "cycle_id": len(self.healing_cycles) + 1,
            "timestamp_start": cycle_start.isoformat(),
            "timestamp_end": cycle_end.isoformat(),
            "duration_seconds": (cycle_end - cycle_start).total_seconds(),
            "auto_apply_enabled": auto_apply,
            "detection_summary": detection_report["summary"],
            "total_fixes_proposed": patch_report["total_fixes_proposed"],
            "fixes_applied": len(applied_fixes),
            "prevention_plan": {
                "recommended_guards": len(prevention_plan["recommended_guards"]),
                "recommended_fallbacks": len(prevention_plan["recommended_fallbacks"]),
                "recommended_thresholds": len(
                    prevention_plan["recommended_thresholds"]
                ),
            },
            "cycle_outcome": self._determine_cycle_outcome(
                detection_report, patch_report, auto_apply
            ),
        }

        # Record cycle
        self.healing_cycles.append(cycle_report)

        logger.info(
            f"Healing cycle {cycle_report['cycle_id']} complete: "
            f"{cycle_report['total_fixes_proposed']} fixes proposed, "
            f"{cycle_report['fixes_applied']} applied"
        )

        return cycle_report

    def get_healing_report(self) -> dict[str, Any]:
        """Get comprehensive healing report.

        Returns:
            Detailed report of all healing activities
        """
        logger.info("Generating comprehensive healing report")

        # Get current health
        health = self.get_system_health()

        # Run detection
        detection_report = self.detection_engine.run_full_detection()

        # Generate patch report
        patch_report = self.correction_engine.generate_patch_report(detection_report)

        # Generate prevention plan
        prevention_plan = self.prevention_engine.generate_prevention_plan(
            detection_report
        )

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "service_version": self.version,
            "system_health": health,
            "detection": {
                "total_issues": detection_report["summary"]["total_issues"],
                "critical_issues": detection_report["summary"]["critical_issues"],
                "high_issues": detection_report["summary"]["high_issues"],
                "health_score": detection_report["summary"]["health_score"],
                "issues_by_category": {
                    category: len(issues)
                    for category, issues in detection_report["checks"].items()
                },
            },
            "correction": {
                "total_fixes_proposed": patch_report["total_fixes_proposed"],
                "fixes_by_category": {
                    category: len(fixes)
                    for category, fixes in patch_report["fixes"].items()
                },
                "high_priority_fixes": len(
                    [
                        f
                        for f in patch_report["prioritized_fixes"]
                        if f.get("risk") == "low" and f.get("confidence", 0) >= 0.8
                    ]
                ),
            },
            "prevention": {
                "active_guards": len(self.prevention_engine.guards),
                "recommended_guards": len(prevention_plan["recommended_guards"]),
                "recommended_thresholds": len(
                    prevention_plan["recommended_thresholds"]
                ),
            },
            "history": {
                "total_cycles": len(self.healing_cycles),
                "recent_cycles": (
                    self.healing_cycles[-5:] if len(self.healing_cycles) > 0 else []
                ),
            },
        }

        logger.info("Healing report generated")
        return report

    def validate_system_integrity(self) -> dict[str, Any]:
        """Validate overall system integrity.

        Returns:
            Integrity validation report
        """
        logger.info("Validating system integrity")

        # Run detection
        detection_report = self.detection_engine.run_full_detection()

        # Check guards
        guard_results = self.prevention_engine.check_all_guards({})

        # Calculate integrity score
        detection_score = detection_report["summary"]["health_score"]
        guard_score = (
            guard_results["guards_passed"] / guard_results["total_guards"]
            if guard_results["total_guards"] > 0
            else 1.0
        )
        integrity_score = (detection_score + guard_score) / 2.0

        # Determine integrity status
        if integrity_score >= 0.95:
            status = "excellent"
        elif integrity_score >= 0.85:
            status = "good"
        elif integrity_score >= 0.7:
            status = "acceptable"
        elif integrity_score >= 0.5:
            status = "poor"
        else:
            status = "failing"

        validation = {
            "timestamp": datetime.now(UTC).isoformat(),
            "integrity_score": integrity_score,
            "status": status,
            "components": {
                "code_quality": {
                    "score": detection_score,
                    "issues": detection_report["summary"]["total_issues"],
                },
                "guard_status": {
                    "score": guard_score,
                    "passed": guard_results["guards_passed"],
                    "failed": guard_results["guards_failed"],
                },
            },
            "recommendations": self._generate_recommendations(
                detection_report, guard_results
            ),
        }

        logger.info(f"System integrity: {status} (score: {integrity_score:.2f})")
        return validation

    def _determine_cycle_outcome(
        self,
        detection_report: dict[str, Any],
        patch_report: dict[str, Any],
        auto_apply: bool,
    ) -> str:
        """Determine the outcome of a healing cycle.

        Args:
            detection_report: Detection results
            patch_report: Patch proposals
            auto_apply: Whether auto-apply was enabled

        Returns:
            Outcome description
        """
        total_issues = detection_report["summary"]["total_issues"]
        critical_issues = detection_report["summary"]["critical_issues"]
        total_fixes = patch_report["total_fixes_proposed"]

        if critical_issues > 0:
            return "critical_issues_detected"
        elif total_issues == 0:
            return "no_issues_detected"
        elif total_fixes > 0 and auto_apply:
            return "fixes_proposed_and_applied"
        elif total_fixes > 0:
            return "fixes_proposed"
        else:
            return "issues_detected_no_fixes"

    def _generate_recommendations(
        self, detection_report: dict[str, Any], guard_results: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations based on validation results.

        Args:
            detection_report: Detection results
            guard_results: Guard check results

        Returns:
            List of recommendations
        """
        recommendations = []

        if detection_report["summary"]["critical_issues"] > 0:
            recommendations.append(
                "Address critical issues immediately before deployment"
            )

        if detection_report["summary"]["high_issues"] > 5:
            recommendations.append("Run healing cycle with auto_apply=True")

        if guard_results["guards_failed"] > 0:
            recommendations.append("Review failed guards and update configurations")

        if len(recommendations) == 0:
            recommendations.append("System is healthy - continue monitoring")

        return recommendations
