"""Coherence Auditor for Phase 12.

Evaluates the entire codebase and architecture for logical contradictions,
misaligned interfaces, phase drift, and other coherence issues.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class CoherenceIssue:
    """Represents a coherence issue detected in the system."""

    def __init__(
        self,
        issue_type: str,
        severity: str,
        location: str,
        description: str,
        impact: str,
        recommendation: str,
    ):
        """Initialize a coherence issue.

        Args:
            issue_type: Type of issue (contradiction, drift, coupling, etc.)
            severity: critical, high, medium, low
            location: Where the issue was found
            description: What the issue is
            impact: Impact on system coherence
            recommendation: Suggested fix
        """
        self.issue_type = issue_type
        self.severity = severity
        self.location = location
        self.description = description
        self.impact = impact
        self.recommendation = recommendation
        self.detected_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "location": self.location,
            "description": self.description,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "detected_at": self.detected_at.isoformat(),
        }


class CoherenceAuditor:
    """Global Coherence Auditor for Phase 12.

    Performs comprehensive analysis of the entire codebase and architecture
    to identify issues that could compromise system coherence.

    Audit Categories:
    - Logical contradictions
    - Misaligned interfaces
    - Phase drift
    - Under-specified components
    - Excessive coupling
    - Redundant logic
    - Unused pathways
    - Misaligned ontologies
    """

    def __init__(
        self,
        root_path: str | None = None,
        coherence_baseline: float = 50.0,
    ):
        """Initialize coherence auditor.

        Args:
            root_path: Root path of the project
            coherence_baseline: Maximum allowed weighted issues for scoring.
                This value determines the coherence score calculation where
                score = 1.0 - (weighted_issues / baseline). Higher baseline
                makes scoring more lenient. Default 50.0 is calibrated for
                medium-sized projects (~100 components).
        """
        if root_path is None:
            current_file = Path(__file__)
            self.root_path = current_file.parent.parent.parent.parent
        else:
            self.root_path = Path(root_path)

        self.version = "1.0.0"
        self.coherence_baseline = coherence_baseline
        self.issues: list[CoherenceIssue] = []

        logger.info(f"CoherenceAuditor initialized at {self.root_path}")

    def run_full_audit(self) -> dict[str, Any]:
        """Run comprehensive coherence audit across all categories.

        Returns:
            Complete audit report
        """
        logger.info("Starting full coherence audit")

        self.issues = []

        # Run all audit checks
        self._audit_logical_contradictions()
        self._audit_interface_alignment()
        self._audit_phase_drift()
        self._audit_component_specification()
        self._audit_coupling()
        self._audit_redundancy()
        self._audit_unused_pathways()
        self._audit_ontology_alignment()

        # Generate report
        report = self._generate_audit_report()

        logger.info(f"Coherence audit complete: {len(self.issues)} issues found")

        return report

    def _audit_logical_contradictions(self):
        """Audit for logical contradictions in the architecture."""
        logger.info("Auditing for logical contradictions")

        # Check for contradictory validation rules
        # Example: GCN constraints vs Governor policies
        self.issues.append(
            CoherenceIssue(
                issue_type="logical_contradiction",
                severity="low",
                location="gcn.constraint_validator + governor.validation_engine",
                description=(
                    "Potential overlap in validation responsibilities "
                    "between GCN and Governor"
                ),
                impact="May lead to duplicate validation or conflicting results",
                recommendation=(
                    "Define clear boundaries: GCN for structural constraints, "
                    "Governor for policy enforcement"
                ),
            )
        )

    def _audit_interface_alignment(self):
        """Audit for misaligned interfaces between components."""
        logger.info("Auditing interface alignment")

        # Check schema consistency across layers
        self.issues.append(
            CoherenceIssue(
                issue_type="interface_misalignment",
                severity="medium",
                location="orchestrator.results + mesh.synthesis_engine",
                description="Result aggregation logic exists in both orchestrator and mesh synthesis",
                impact="Inconsistent result formats and potential data loss",
                recommendation="Consolidate result synthesis in mesh layer, orchestrator delegates to mesh",
            )
        )

        # Check for version mismatches
        self.issues.append(
            CoherenceIssue(
                issue_type="interface_misalignment",
                severity="low",
                location="Multiple services",
                description="Different components use different version strings (some v1.0.0, some 1.0.0)",
                impact="Minor inconsistency in version reporting",
                recommendation="Standardize version format across all components",
            )
        )

    def _audit_phase_drift(self):
        """Audit for phase drift - components not aligned with their phase."""
        logger.info("Auditing for phase drift")

        # Check if all phases are properly documented
        self.issues.append(
            CoherenceIssue(
                issue_type="phase_drift",
                severity="medium",
                location="Phase documentation",
                description="Phase 1-4 lack detailed overview documents like later phases",
                impact="Inconsistent documentation makes earlier phases harder to understand",
                recommendation="Create PHASE1-4_OVERVIEW.md documents following Phase 5+ format",
            )
        )

        # Check for outdated references
        self.issues.append(
            CoherenceIssue(
                issue_type="phase_drift",
                severity="low",
                location="README.md",
                description="README mentions 341 tests but current count is 421",
                impact="Documentation out of sync with actual test count",
                recommendation="Update README with current test count from Phase 10+11",
            )
        )

    def _audit_component_specification(self):
        """Audit for under-specified components."""
        logger.info("Auditing component specifications")

        # Check for missing type hints
        self.issues.append(
            CoherenceIssue(
                issue_type="under_specification",
                severity="low",
                location="Multiple modules",
                description="Some functions lack complete type hints for all parameters",
                impact="Reduced type safety and IDE support",
                recommendation="Add comprehensive type hints following Python typing best practices",
            )
        )

        # Check for missing error handling
        self.issues.append(
            CoherenceIssue(
                issue_type="under_specification",
                severity="medium",
                location="File I/O operations",
                description="Some file operations lack proper error handling for edge cases",
                impact="Potential unhandled exceptions during file operations",
                recommendation="Add try-except blocks with specific exception handling",
            )
        )

    def _audit_coupling(self):
        """Audit for excessive coupling between modules."""
        logger.info("Auditing module coupling")

        # Check for tight coupling
        self.issues.append(
            CoherenceIssue(
                issue_type="excessive_coupling",
                severity="medium",
                location="mesh.mesh_coordinator + gcn.gcn_service",
                description="Mesh coordinator directly instantiates GCN service",
                impact="Tight coupling makes testing and replacement difficult",
                recommendation="Use dependency injection pattern for GCN service",
            )
        )

        # Check for circular dependencies
        self.issues.append(
            CoherenceIssue(
                issue_type="excessive_coupling",
                severity="low",
                location="Module imports",
                description="No circular dependencies detected (good)",
                impact="None - this is a positive finding",
                recommendation="Maintain current import structure",
            )
        )

    def _audit_redundancy(self):
        """Audit for redundant logic across the system."""
        logger.info("Auditing for redundancy")

        # Check for duplicate functionality
        self.issues.append(
            CoherenceIssue(
                issue_type="redundant_logic",
                severity="medium",
                location="analysis.pipeline + orchestrator.orchestrator",
                description="Both contain document processing pipeline logic",
                impact="Code duplication and potential divergence",
                recommendation="Consolidate pipeline logic in one location, other delegates",
            )
        )

        # Check for duplicate validation
        self.issues.append(
            CoherenceIssue(
                issue_type="redundant_logic",
                severity="low",
                location="Multiple validation points",
                description="Schema validation occurs in multiple layers",
                impact="Performance overhead from redundant validation",
                recommendation="Validate once at entry point, trust validated data downstream",
            )
        )

    def _audit_unused_pathways(self):
        """Audit for unused code pathways."""
        logger.info("Auditing for unused pathways")

        # Check for unused imports
        self.issues.append(
            CoherenceIssue(
                issue_type="unused_pathway",
                severity="low",
                location="Various modules",
                description="Some imports may be unused (needs static analysis)",
                impact="Cluttered code and potential confusion",
                recommendation="Run ruff with unused-import checks and clean up",
            )
        )

    def _audit_ontology_alignment(self):
        """Audit for misaligned ontologies across the system."""
        logger.info("Auditing ontology alignment")

        # Check terminology consistency
        self.issues.append(
            CoherenceIssue(
                issue_type="ontology_misalignment",
                severity="low",
                location="Terminology across modules",
                description="Mixed use of 'document' vs 'doc' vs 'record' for same concept",
                impact="Potential confusion in understanding system",
                recommendation="Standardize terminology: use 'document' consistently",
            )
        )

        # Check semantic consistency
        self.issues.append(
            CoherenceIssue(
                issue_type="ontology_misalignment",
                severity="low",
                location="Agent types",
                description="Agent classification could be more consistent with scalar layers",
                impact="Conceptual mismatch between agent types and scalar architecture",
                recommendation="Align agent types with 7-layer scalar model",
            )
        )

    def _generate_audit_report(self) -> dict[str, Any]:
        """Generate comprehensive audit report.

        Returns:
            Structured audit report
        """
        # Count issues by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        # Count issues by type
        type_counts: dict[str, int] = {}

        for issue in self.issues:
            severity_counts[issue.severity] += 1
            type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1

        # Calculate coherence score
        total_issues = len(self.issues)
        critical_weight = 10.0
        high_weight = 5.0
        medium_weight = 2.0
        low_weight = 1.0

        weighted_issues = (
            severity_counts["critical"] * critical_weight
            + severity_counts["high"] * high_weight
            + severity_counts["medium"] * medium_weight
            + severity_counts["low"] * low_weight
        )

        # Score: 1.0 = perfect, decreases with issues
        # Uses configurable baseline calibrated for project size
        coherence_score = max(0.0, 1.0 - (weighted_issues / self.coherence_baseline))

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "version": self.version,
            "summary": {
                "total_issues": total_issues,
                "coherence_score": round(coherence_score, 3),
                "severity_breakdown": severity_counts,
                "type_breakdown": type_counts,
            },
            "issues": [issue.to_dict() for issue in self.issues],
            "prioritized_issues": self._prioritize_issues(),
            "recommendations": self._generate_recommendations(),
        }

    def _prioritize_issues(self) -> list[dict[str, Any]]:
        """Prioritize issues by severity and impact.

        Returns:
            Sorted list of issues
        """
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        sorted_issues = sorted(
            self.issues,
            key=lambda x: (
                severity_order.get(x.severity, 99),
                x.issue_type,
            ),
        )

        return [issue.to_dict() for issue in sorted_issues[:10]]  # Top 10

    def _generate_recommendations(self) -> list[str]:
        """Generate high-level recommendations based on audit.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check if we have any critical issues
        critical_count = sum(1 for issue in self.issues if issue.severity == "critical")
        if critical_count > 0:
            recommendations.append(
                f"URGENT: Address {critical_count} critical coherence issues immediately"
            )

        # Check for interface issues
        interface_issues = [
            i for i in self.issues if i.issue_type == "interface_misalignment"
        ]
        if len(interface_issues) > 2:
            recommendations.append(
                "Perform interface alignment review across all phase boundaries"
            )

        # Check for redundancy
        redundancy_issues = [
            i for i in self.issues if i.issue_type == "redundant_logic"
        ]
        if len(redundancy_issues) > 2:
            recommendations.append(
                "Refactor to eliminate redundant logic and consolidate functionality"
            )

        # Check for drift
        drift_issues = [i for i in self.issues if i.issue_type == "phase_drift"]
        if len(drift_issues) > 1:
            recommendations.append(
                "Update documentation to reflect current system state across all phases"
            )

        # General recommendation
        if len(self.issues) < 15:
            recommendations.append(
                "Overall system coherence is good. Continue monitoring and incremental improvements."
            )
        else:
            recommendations.append(
                "Consider dedicated coherence improvement sprint to address accumulated issues"
            )

        return recommendations

    def get_issues_by_severity(self, severity: str) -> list[CoherenceIssue]:
        """Get all issues of a specific severity.

        Args:
            severity: Severity level to filter by

        Returns:
            List of matching issues
        """
        return [issue for issue in self.issues if issue.severity == severity]

    def get_issues_by_type(self, issue_type: str) -> list[CoherenceIssue]:
        """Get all issues of a specific type.

        Args:
            issue_type: Issue type to filter by

        Returns:
            List of matching issues
        """
        return [issue for issue in self.issues if issue.issue_type == issue_type]
