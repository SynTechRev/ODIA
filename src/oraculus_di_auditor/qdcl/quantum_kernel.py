"""Quantum-Kernel Decision Layer - QDCL Phase 13.

Final reasoning integrating scalar harmonics, hypothesis resonance,
multidimensional coherence, cross-agent consensus, and predicted trajectory stability.
Outputs decision kernels with full traceability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Confidence calculation weights for multi-factor integration
CONFIDENCE_WEIGHTS = {
    "scalar": 0.15,
    "hypothesis": 0.20,
    "coherence": 0.20,
    "consensus": 0.25,
    "trajectory": 0.20,
}

# Justification score thresholds
STRONG_JUSTIFICATION_THRESHOLD = 0.7


@dataclass
class DecisionKernel:
    """A decision kernel with full traceability."""

    kernel_id: str
    decision: str
    confidence: float  # 0.0 to 1.0
    scalar_harmonic_score: float  # From Phase 12
    hypothesis_resonance: float  # From hypothesis engine
    coherence_score: float  # Multidimensional coherence
    consensus_score: float  # Cross-agent consensus
    trajectory_stability: float  # From trajectory engine
    justification: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """Validate kernel values."""
        for field_name, value in [
            ("confidence", self.confidence),
            ("scalar_harmonic_score", self.scalar_harmonic_score),
            ("hypothesis_resonance", self.hypothesis_resonance),
            ("coherence_score", self.coherence_score),
            ("consensus_score", self.consensus_score),
            ("trajectory_stability", self.trajectory_stability),
        ]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be 0.0-1.0, got {value}")


class QuantumKernelDecisionLayer:
    """Quantum-kernel decision layer for QDCL.

    Final reasoning integrating:
    - Scalar harmonics (from Phase 12)
    - Hypothesis resonance (from superpositional engine)
    - Multidimensional coherence (from multi-perspective evaluator)
    - Cross-agent consensus (from cognitive mesh fusion)
    - Predicted trajectory stability (from trajectory engine)

    Output: Decision kernels with full traceability
    """

    def __init__(self):
        """Initialize quantum-kernel decision layer."""
        self.version = "1.0.0"
        self.decision_kernels: list[DecisionKernel] = []
        self.created_at = datetime.now(UTC)
        logger.info("QuantumKernelDecisionLayer initialized")

    def generate_decision_kernel(
        self,
        decision: str,
        scalar_harmonics: dict[int, float],
        hypothesis_data: dict[str, Any],
        coherence_data: dict[str, Any],
        consensus_data: dict[str, Any],
        trajectory_data: dict[str, Any],
    ) -> DecisionKernel:
        """Generate a decision kernel from integrated reasoning.

        Args:
            decision: Decision statement
            scalar_harmonics: Scalar harmonic weights from Phase 12
            hypothesis_data: Hypothesis engine data
            coherence_data: Multi-perspective coherence data
            consensus_data: Cross-agent consensus data
            trajectory_data: Trajectory prediction data

        Returns:
            Decision kernel with full traceability
        """
        # Calculate scalar harmonic score
        scalar_harmonic_score = self._calculate_scalar_harmonic_score(scalar_harmonics)

        # Calculate hypothesis resonance
        hypothesis_resonance = self._calculate_hypothesis_resonance(hypothesis_data)

        # Calculate coherence score
        coherence_score = self._calculate_coherence_score(coherence_data)

        # Calculate consensus score
        consensus_score = self._calculate_consensus_score(consensus_data)

        # Calculate trajectory stability
        trajectory_stability = self._calculate_trajectory_stability(trajectory_data)

        # Calculate overall confidence
        confidence = self._calculate_overall_confidence(
            scalar_harmonic_score,
            hypothesis_resonance,
            coherence_score,
            consensus_score,
            trajectory_stability,
        )

        # Generate justification
        justification = self._generate_justification(
            scalar_harmonic_score,
            hypothesis_resonance,
            coherence_score,
            consensus_score,
            trajectory_stability,
        )

        # Compile evidence
        evidence = {
            "scalar_harmonics": scalar_harmonics,
            "hypothesis_summary": self._summarize_hypotheses(hypothesis_data),
            "coherence_summary": self._summarize_coherence(coherence_data),
            "consensus_summary": self._summarize_consensus(consensus_data),
            "trajectory_summary": self._summarize_trajectory(trajectory_data),
        }

        # Generate alternatives
        alternatives = self._generate_alternatives(decision, evidence)

        kernel = DecisionKernel(
            kernel_id=f"kernel_{len(self.decision_kernels)}",
            decision=decision,
            confidence=confidence,
            scalar_harmonic_score=scalar_harmonic_score,
            hypothesis_resonance=hypothesis_resonance,
            coherence_score=coherence_score,
            consensus_score=consensus_score,
            trajectory_stability=trajectory_stability,
            justification=justification,
            evidence=evidence,
            alternatives=alternatives,
        )

        self.decision_kernels.append(kernel)
        logger.info(
            f"Generated decision kernel: {decision} (confidence={confidence:.2f})"
        )
        return kernel

    def _calculate_scalar_harmonic_score(
        self, scalar_harmonics: dict[int, float]
    ) -> float:
        """Calculate scalar harmonic score.

        Args:
            scalar_harmonics: Harmonic weights by layer

        Returns:
            Harmonic score (0.0-1.0)
        """
        if not scalar_harmonics:
            return 0.5

        # Average harmonic weights
        return sum(scalar_harmonics.values()) / len(scalar_harmonics)

    def _calculate_hypothesis_resonance(self, hypothesis_data: dict[str, Any]) -> float:
        """Calculate hypothesis resonance.

        Args:
            hypothesis_data: Hypothesis engine data

        Returns:
            Resonance score (0.0-1.0)
        """
        if "hypotheses" not in hypothesis_data:
            return 0.5

        hypotheses = hypothesis_data["hypotheses"]
        if not hypotheses:
            return 0.5

        # Calculate average coherence across hypotheses
        total_coherence = 0.0
        count = 0

        for hyp in hypotheses:
            if "state_vectors" in hyp:
                for vector in hyp["state_vectors"]:
                    total_coherence += vector.get("coherence", 0.0)
                    count += 1

        return total_coherence / count if count > 0 else 0.5

    def _calculate_coherence_score(self, coherence_data: dict[str, Any]) -> float:
        """Calculate multidimensional coherence score.

        Args:
            coherence_data: Multi-perspective coherence data

        Returns:
            Coherence score (0.0-1.0)
        """
        if "alignment_score" in coherence_data:
            return coherence_data["alignment_score"]

        # Calculate from evaluations
        if "evaluations" in coherence_data:
            evaluations = coherence_data["evaluations"]
            if evaluations:
                scores = [
                    eval_data["score"]
                    for eval_data in evaluations.values()
                    if "score" in eval_data
                ]
                return sum(scores) / len(scores) if scores else 0.5

        return 0.5

    def _calculate_consensus_score(self, consensus_data: dict[str, Any]) -> float:
        """Calculate cross-agent consensus score.

        Args:
            consensus_data: Consensus data from cognitive mesh

        Returns:
            Consensus score (0.0-1.0)
        """
        if "high_consensus_concepts" in consensus_data:
            total = consensus_data.get("total_concepts", 0)
            high = len(consensus_data["high_consensus_concepts"])
            return high / total if total > 0 else 0.5

        return 0.5

    def _calculate_trajectory_stability(self, trajectory_data: dict[str, Any]) -> float:
        """Calculate trajectory stability.

        Args:
            trajectory_data: Trajectory prediction data

        Returns:
            Stability score (0.0-1.0)
        """
        if "stability_score" in trajectory_data:
            return trajectory_data["stability_score"]

        return 0.5

    def _calculate_overall_confidence(
        self,
        scalar_harmonic_score: float,
        hypothesis_resonance: float,
        coherence_score: float,
        consensus_score: float,
        trajectory_stability: float,
    ) -> float:
        """Calculate overall confidence from all factors.

        Args:
            scalar_harmonic_score: Scalar harmonic score
            hypothesis_resonance: Hypothesis resonance
            coherence_score: Coherence score
            consensus_score: Consensus score
            trajectory_stability: Trajectory stability

        Returns:
            Overall confidence (0.0-1.0)
        """
        # Weighted average with emphasis on consensus and trajectory
        confidence = (
            CONFIDENCE_WEIGHTS["scalar"] * scalar_harmonic_score
            + CONFIDENCE_WEIGHTS["hypothesis"] * hypothesis_resonance
            + CONFIDENCE_WEIGHTS["coherence"] * coherence_score
            + CONFIDENCE_WEIGHTS["consensus"] * consensus_score
            + CONFIDENCE_WEIGHTS["trajectory"] * trajectory_stability
        )

        return min(1.0, max(0.0, confidence))

    def _generate_justification(
        self,
        scalar_harmonic_score: float,
        hypothesis_resonance: float,
        coherence_score: float,
        consensus_score: float,
        trajectory_stability: float,
    ) -> list[str]:
        """Generate justification statements.

        Args:
            scalar_harmonic_score: Scalar harmonic score
            hypothesis_resonance: Hypothesis resonance
            coherence_score: Coherence score
            consensus_score: Consensus score
            trajectory_stability: Trajectory stability

        Returns:
            List of justification statements
        """
        justification = []

        if scalar_harmonic_score >= STRONG_JUSTIFICATION_THRESHOLD:
            justification.append(
                f"Strong scalar harmonic alignment (score={scalar_harmonic_score:.2f})"
            )
        if hypothesis_resonance >= STRONG_JUSTIFICATION_THRESHOLD:
            justification.append(
                f"High hypothesis resonance (score={hypothesis_resonance:.2f})"
            )
        if coherence_score >= STRONG_JUSTIFICATION_THRESHOLD:
            justification.append(
                f"Strong multidimensional coherence (score={coherence_score:.2f})"
            )
        if consensus_score >= STRONG_JUSTIFICATION_THRESHOLD:
            justification.append(
                f"High cross-agent consensus (score={consensus_score:.2f})"
            )
        if trajectory_stability >= STRONG_JUSTIFICATION_THRESHOLD:
            justification.append(
                f"Stable trajectory prediction (score={trajectory_stability:.2f})"
            )

        if not justification:
            justification.append("Decision based on moderate confidence across factors")

        return justification

    def _summarize_hypotheses(self, hypothesis_data: dict[str, Any]) -> dict[str, Any]:
        """Summarize hypothesis data.

        Args:
            hypothesis_data: Hypothesis engine data

        Returns:
            Summary dictionary
        """
        return {
            "total_hypotheses": hypothesis_data.get("total_hypotheses", 0),
            "state_distribution": hypothesis_data.get("state_distribution", {}),
        }

    def _summarize_coherence(self, coherence_data: dict[str, Any]) -> dict[str, Any]:
        """Summarize coherence data.

        Args:
            coherence_data: Coherence data

        Returns:
            Summary dictionary
        """
        return {
            "alignment_score": coherence_data.get("alignment_score", 0.5),
            "average_delta": coherence_data.get("average_delta", 0.0),
        }

    def _summarize_consensus(self, consensus_data: dict[str, Any]) -> dict[str, Any]:
        """Summarize consensus data.

        Args:
            consensus_data: Consensus data

        Returns:
            Summary dictionary
        """
        return {
            "total_agents": consensus_data.get("total_agents", 0),
            "total_concepts": consensus_data.get("total_concepts", 0),
        }

    def _summarize_trajectory(self, trajectory_data: dict[str, Any]) -> dict[str, Any]:
        """Summarize trajectory data.

        Args:
            trajectory_data: Trajectory data

        Returns:
            Summary dictionary
        """
        return {
            "total_paths": trajectory_data.get("total_paths", 0),
            "stability_score": trajectory_data.get("stability_score", 0.5),
        }

    def _generate_alternatives(
        self, decision: str, evidence: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate alternative decisions.

        Args:
            decision: Main decision
            evidence: Evidence dictionary

        Returns:
            List of alternative decisions
        """
        # Simplified: generate one alternative
        return [
            {
                "alternative_decision": f"Alternative to: {decision}",
                "confidence": 0.3,
                "rationale": "Lower confidence alternative approach",
            }
        ]

    def get_kernel(self, kernel_id: str) -> DecisionKernel | None:
        """Get a decision kernel by ID.

        Args:
            kernel_id: Kernel identifier

        Returns:
            Decision kernel or None
        """
        for kernel in self.decision_kernels:
            if kernel.kernel_id == kernel_id:
                return kernel
        return None

    def get_high_confidence_kernels(
        self, threshold: float = 0.7
    ) -> list[DecisionKernel]:
        """Get decision kernels with high confidence.

        Args:
            threshold: Minimum confidence threshold

        Returns:
            List of high-confidence kernels
        """
        return [k for k in self.decision_kernels if k.confidence >= threshold]

    def to_dict(self) -> dict[str, Any]:
        """Convert decision layer to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "total_kernels": len(self.decision_kernels),
            "kernels": [
                {
                    "kernel_id": k.kernel_id,
                    "decision": k.decision,
                    "confidence": k.confidence,
                    "scalar_harmonic_score": k.scalar_harmonic_score,
                    "hypothesis_resonance": k.hypothesis_resonance,
                    "coherence_score": k.coherence_score,
                    "consensus_score": k.consensus_score,
                    "trajectory_stability": k.trajectory_stability,
                    "justification": k.justification,
                    "timestamp": k.timestamp.isoformat(),
                }
                for k in self.decision_kernels
            ],
        }
