"""Multi-Perspective State Evaluation - QDCL Phase 13.

Evaluates system state from six perspectives and generates Δ-difference maps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Perspective(Enum):
    """Six evaluation perspectives."""

    SYSTEMIC = "systemic"  # Overall system health and coherence
    COMPONENT = "component"  # Individual component behavior
    TEMPORAL = "temporal"  # Time-based evolution and trends
    ADVERSARIAL = "adversarial"  # Attack vectors and vulnerabilities
    GOVERNANCE = "governance"  # Policy compliance and controls
    USER_CENTRIC = "user_centric"  # User experience and value delivery


@dataclass
class PerspectiveEvaluation:
    """Evaluation from a single perspective."""

    perspective: Perspective
    score: float  # 0.0 to 1.0
    findings: list[str]
    metrics: dict[str, float]
    recommendations: list[str]
    timestamp: datetime


class DeltaDifferenceMap:
    """Δ-difference map across all six perspectives."""

    def __init__(self):
        """Initialize delta difference map."""
        self.evaluations: dict[Perspective, PerspectiveEvaluation] = {}
        self.delta_matrix: dict[tuple[Perspective, Perspective], float] = {}
        self.created_at = datetime.now(UTC)

    def add_evaluation(self, evaluation: PerspectiveEvaluation):
        """Add a perspective evaluation.

        Args:
            evaluation: Perspective evaluation to add
        """
        self.evaluations[evaluation.perspective] = evaluation
        logger.debug(
            f"Added {evaluation.perspective.value} evaluation "
            f"(score={evaluation.score:.2f})"
        )

    def calculate_deltas(self):
        """Calculate Δ differences between all perspective pairs."""
        perspectives = list(self.evaluations.keys())

        for i, persp1 in enumerate(perspectives):
            for persp2 in perspectives[i + 1 :]:
                eval1 = self.evaluations[persp1]
                eval2 = self.evaluations[persp2]

                # Calculate delta as score difference
                delta = abs(eval1.score - eval2.score)
                self.delta_matrix[(persp1, persp2)] = delta
                self.delta_matrix[(persp2, persp1)] = delta

        logger.info(f"Calculated {len(self.delta_matrix)} delta differences")

    def get_largest_deltas(
        self, top_k: int = 3
    ) -> list[tuple[Perspective, Perspective, float]]:
        """Get perspective pairs with largest deltas.

        Args:
            top_k: Number of top deltas to return

        Returns:
            List of (perspective1, perspective2, delta) tuples
        """
        sorted_deltas = sorted(
            self.delta_matrix.items(), key=lambda x: x[1], reverse=True
        )
        return [(pair[0], pair[1], delta) for pair, delta in sorted_deltas[:top_k]]

    def to_dict(self) -> dict[str, Any]:
        """Convert map to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "evaluations": {
                persp.value: {
                    "score": eval.score,
                    "findings": eval.findings,
                    "metrics": eval.metrics,
                    "recommendations": eval.recommendations,
                    "timestamp": eval.timestamp.isoformat(),
                }
                for persp, eval in self.evaluations.items()
            },
            "delta_matrix": {
                f"{p1.value}-{p2.value}": delta
                for (p1, p2), delta in self.delta_matrix.items()
            },
            "created_at": self.created_at.isoformat(),
        }


class MultiPerspectiveEvaluator:
    """Multi-perspective state evaluator for QDCL.

    Evaluates every system state from six perspectives:
    - Systemic (overall system health)
    - Component (individual component behavior)
    - Temporal (time-based evolution)
    - Adversarial (security vulnerabilities)
    - Governance (policy compliance)
    - User-centric (user experience)

    Generates Δ-difference map showing perspective divergence.
    """

    def __init__(self):
        """Initialize multi-perspective evaluator."""
        self.version = "1.0.0"
        self.delta_map: DeltaDifferenceMap | None = None
        self.created_at = datetime.now(UTC)
        logger.info("MultiPerspectiveEvaluator initialized")

    def evaluate_systemic_perspective(
        self, system_state: dict[str, Any]
    ) -> PerspectiveEvaluation:
        """Evaluate from systemic perspective.

        Args:
            system_state: Current system state

        Returns:
            Perspective evaluation
        """
        # Analyze overall system coherence and health
        coherence_score = system_state.get("coherence_score", 0.5)
        component_count = system_state.get("component_count", 0)
        integration_level = system_state.get("integration_level", 0.5)

        score = (coherence_score + integration_level) / 2.0

        findings = []
        if coherence_score < 0.7:
            findings.append("Low system coherence detected")
        if component_count > 100:
            findings.append("High component count may indicate complexity")

        recommendations = []
        if score < 0.7:
            recommendations.append("Improve system integration")

        return PerspectiveEvaluation(
            perspective=Perspective.SYSTEMIC,
            score=score,
            findings=findings,
            metrics={
                "coherence_score": coherence_score,
                "component_count": component_count,
                "integration_level": integration_level,
            },
            recommendations=recommendations,
            timestamp=datetime.now(UTC),
        )

    def evaluate_component_perspective(
        self, system_state: dict[str, Any]
    ) -> PerspectiveEvaluation:
        """Evaluate from component perspective.

        Args:
            system_state: Current system state

        Returns:
            Perspective evaluation
        """
        # Analyze individual component behavior
        component_health = system_state.get("component_health", {})
        avg_health = (
            sum(component_health.values()) / len(component_health)
            if component_health
            else 0.5
        )

        findings = []
        for comp, health in component_health.items():
            if health < 0.5:
                findings.append(f"Component {comp} has low health: {health:.2f}")

        recommendations = []
        if avg_health < 0.7:
            recommendations.append("Review and optimize underperforming components")

        return PerspectiveEvaluation(
            perspective=Perspective.COMPONENT,
            score=avg_health,
            findings=findings,
            metrics={"average_component_health": avg_health},
            recommendations=recommendations,
            timestamp=datetime.now(UTC),
        )

    def evaluate_temporal_perspective(
        self, system_state: dict[str, Any]
    ) -> PerspectiveEvaluation:
        """Evaluate from temporal perspective.

        Args:
            system_state: Current system state

        Returns:
            Perspective evaluation
        """
        # Analyze time-based evolution and trends
        drift_rate = system_state.get("drift_rate", 0.0)
        evolution_health = system_state.get("evolution_health", 0.5)
        change_velocity = system_state.get("change_velocity", 0.0)

        # Lower drift and moderate velocity are better
        score = (
            evolution_health
            * (1.0 - min(drift_rate, 1.0))
            * (1.0 - min(change_velocity * 0.5, 1.0))
        )

        findings = []
        if drift_rate > 0.5:
            findings.append(f"High drift rate detected: {drift_rate:.2f}")
        if change_velocity > 0.8:
            findings.append(f"Rapid change velocity: {change_velocity:.2f}")

        recommendations = []
        if score < 0.7:
            recommendations.append("Monitor temporal drift and stabilize change rate")

        return PerspectiveEvaluation(
            perspective=Perspective.TEMPORAL,
            score=score,
            findings=findings,
            metrics={
                "drift_rate": drift_rate,
                "evolution_health": evolution_health,
                "change_velocity": change_velocity,
            },
            recommendations=recommendations,
            timestamp=datetime.now(UTC),
        )

    def evaluate_adversarial_perspective(
        self, system_state: dict[str, Any]
    ) -> PerspectiveEvaluation:
        """Evaluate from adversarial perspective.

        Args:
            system_state: Current system state

        Returns:
            Perspective evaluation
        """
        # Analyze attack vectors and vulnerabilities
        vulnerability_count = system_state.get("vulnerability_count", 0)
        security_score = system_state.get("security_score", 0.8)
        attack_surface = system_state.get("attack_surface", 0.3)

        # Higher security score and lower vulnerabilities are better
        score = security_score * (1.0 - min(vulnerability_count * 0.1, 1.0))

        findings = []
        if vulnerability_count > 0:
            findings.append(f"{vulnerability_count} vulnerabilities detected")
        if attack_surface > 0.5:
            findings.append(f"Large attack surface: {attack_surface:.2f}")

        recommendations = []
        if score < 0.8:
            recommendations.append("Address vulnerabilities and reduce attack surface")

        return PerspectiveEvaluation(
            perspective=Perspective.ADVERSARIAL,
            score=score,
            findings=findings,
            metrics={
                "vulnerability_count": vulnerability_count,
                "security_score": security_score,
                "attack_surface": attack_surface,
            },
            recommendations=recommendations,
            timestamp=datetime.now(UTC),
        )

    def evaluate_governance_perspective(
        self, system_state: dict[str, Any]
    ) -> PerspectiveEvaluation:
        """Evaluate from governance perspective.

        Args:
            system_state: Current system state

        Returns:
            Perspective evaluation
        """
        # Analyze policy compliance and controls
        compliance_score = system_state.get("compliance_score", 0.8)
        policy_violations = system_state.get("policy_violations", 0)
        governance_health = system_state.get("governance_health", 0.8)

        score = governance_health * (1.0 - min(policy_violations * 0.1, 1.0))

        findings = []
        if policy_violations > 0:
            findings.append(f"{policy_violations} policy violations detected")
        if compliance_score < 0.9:
            findings.append(f"Compliance score below target: {compliance_score:.2f}")

        recommendations = []
        if score < 0.8:
            recommendations.append("Improve policy compliance and governance controls")

        return PerspectiveEvaluation(
            perspective=Perspective.GOVERNANCE,
            score=score,
            findings=findings,
            metrics={
                "compliance_score": compliance_score,
                "policy_violations": policy_violations,
                "governance_health": governance_health,
            },
            recommendations=recommendations,
            timestamp=datetime.now(UTC),
        )

    def evaluate_user_centric_perspective(
        self, system_state: dict[str, Any]
    ) -> PerspectiveEvaluation:
        """Evaluate from user-centric perspective.

        Args:
            system_state: Current system state

        Returns:
            Perspective evaluation
        """
        # Analyze user experience and value delivery
        user_satisfaction = system_state.get("user_satisfaction", 0.7)
        value_delivery = system_state.get("value_delivery", 0.7)
        usability_score = system_state.get("usability_score", 0.7)

        score = (user_satisfaction + value_delivery + usability_score) / 3.0

        findings = []
        if user_satisfaction < 0.7:
            findings.append(f"Low user satisfaction: {user_satisfaction:.2f}")
        if usability_score < 0.7:
            findings.append(f"Usability concerns: {usability_score:.2f}")

        recommendations = []
        if score < 0.7:
            recommendations.append("Enhance user experience and value delivery")

        return PerspectiveEvaluation(
            perspective=Perspective.USER_CENTRIC,
            score=score,
            findings=findings,
            metrics={
                "user_satisfaction": user_satisfaction,
                "value_delivery": value_delivery,
                "usability_score": usability_score,
            },
            recommendations=recommendations,
            timestamp=datetime.now(UTC),
        )

    def evaluate_all_perspectives(
        self, system_state: dict[str, Any]
    ) -> DeltaDifferenceMap:
        """Evaluate system state from all six perspectives.

        Args:
            system_state: Current system state

        Returns:
            Delta difference map
        """
        self.delta_map = DeltaDifferenceMap()

        # Evaluate each perspective
        evaluations = [
            self.evaluate_systemic_perspective(system_state),
            self.evaluate_component_perspective(system_state),
            self.evaluate_temporal_perspective(system_state),
            self.evaluate_adversarial_perspective(system_state),
            self.evaluate_governance_perspective(system_state),
            self.evaluate_user_centric_perspective(system_state),
        ]

        for evaluation in evaluations:
            self.delta_map.add_evaluation(evaluation)

        # Calculate deltas between perspectives
        self.delta_map.calculate_deltas()

        logger.info(
            f"Evaluated system from {len(evaluations)} perspectives, "
            f"calculated delta differences"
        )
        return self.delta_map

    def get_perspective_alignment(self) -> dict[str, Any]:
        """Get alignment analysis across perspectives.

        Returns:
            Alignment analysis
        """
        if not self.delta_map:
            return {"error": "No delta map generated yet"}

        # Calculate average delta
        avg_delta = (
            sum(self.delta_map.delta_matrix.values()) / len(self.delta_map.delta_matrix)
            if self.delta_map.delta_matrix
            else 0.0
        )

        # Get largest divergences
        largest_deltas = self.delta_map.get_largest_deltas(top_k=3)

        # Overall alignment score (lower delta = better alignment)
        alignment_score = 1.0 - min(avg_delta, 1.0)

        return {
            "alignment_score": alignment_score,
            "average_delta": avg_delta,
            "largest_divergences": [
                {
                    "perspective1": p1.value,
                    "perspective2": p2.value,
                    "delta": delta,
                }
                for p1, p2, delta in largest_deltas
            ],
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert evaluator to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "delta_map": self.delta_map.to_dict() if self.delta_map else None,
            "alignment_analysis": self.get_perspective_alignment(),
        }
