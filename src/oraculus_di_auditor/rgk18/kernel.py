# src/oraculus_di_auditor/rgk18/kernel.py
"""Core governance kernel: evaluation, decision making, enforcement."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .consensus_engine import ConsensusEngine
from .constants import (
    APPROVE_THRESHOLD,
    CONDITIONAL_THRESHOLD,
    REVIEW_THRESHOLD,
    SERVICE_VERSION,
)
from .policy_interpreter import PolicyInterpreter, PolicySet
from .schemas import DecisionOutcome, DecisionScore, PolicyCheckResult
from .utils import canonicalize_input, seed_from_input, sha256_hex


class GovernanceKernel:
    """Core recursive governance kernel for decision evaluation."""

    def __init__(
        self,
        policy_interpreter: PolicyInterpreter | None = None,
        consensus_engine: ConsensusEngine | None = None,
    ):
        """Initialize governance kernel.

        Args:
            policy_interpreter: Policy interpreter instance
            consensus_engine: Consensus engine instance
        """
        self.policy_interpreter = policy_interpreter or PolicyInterpreter()
        self.consensus_engine = consensus_engine or ConsensusEngine()

    def evaluate(
        self,
        candidate_action: dict[str, Any],
        phase_inputs: dict[str, Any],
        policy_set: PolicySet | None = None,
    ) -> tuple[DecisionOutcome, DecisionScore, list[PolicyCheckResult], dict[str, Any]]:
        """Evaluate a candidate action through the governance kernel.

        Args:
            candidate_action: Action to evaluate
            phase_inputs: Inputs from previous phases (10-17)
            policy_set: Optional policy set to check against

        Returns:
            Tuple of (DecisionOutcome, DecisionScore, policy_violations, provenance)
        """
        # Step 1: Canonicalize input
        combined_input = {
            "candidate_action": candidate_action,
            "phase_inputs": phase_inputs,
        }
        canonical_input = canonicalize_input(combined_input)

        # Step 2: Derive deterministic seed
        seed = seed_from_input(canonical_input)
        input_hash = sha256_hex(canonical_input)

        # Step 3: Check policies
        policy_results: list[PolicyCheckResult] = []
        if policy_set:
            policy_results = self.policy_interpreter.check_policies(
                candidate_action, policy_set
            )

        # Step 4: Check for high severity violations (immediate reject)
        high_severity_violations = [
            r for r in policy_results if r.severity == "high" and r.violated
        ]
        if high_severity_violations:
            outcome = DecisionOutcome(
                outcome="REJECT",
                rationale="High severity policy violations detected",
                mitigations=[],
            )
            # No scoring needed, immediate reject
            score = DecisionScore(score=0.0, components={})
            provenance = self._build_provenance(seed, input_hash)
            return outcome, score, policy_results, provenance

        # Step 5: Collect evidence and aggregate score
        evidence = self._extract_evidence(phase_inputs)
        score = self.consensus_engine.aggregate(evidence)

        # Step 6: Map score to outcome
        outcome = self._score_to_outcome(score, policy_results)

        # Step 7: Build provenance
        provenance = self._build_provenance(seed, input_hash)

        return outcome, score, policy_results, provenance

    def _extract_evidence(self, phase_inputs: dict[str, Any]) -> dict[str, float]:
        """Extract evidence scores from phase inputs.

        Args:
            phase_inputs: Inputs from previous phases

        Returns:
            Evidence dictionary with normalized scores
        """
        evidence = {}

        # Extract from Phase 12 (scalar harmonics)
        phase12 = phase_inputs.get("phase12", {})
        if "coherence_score" in phase12:
            evidence["scalar_harmonics"] = phase12["coherence_score"]
        else:
            evidence["scalar_harmonics"] = None

        # Extract from Phase 13 (QDCL probability)
        phase13 = phase_inputs.get("phase13", {})
        if "probability" in phase13:
            evidence["qdcl_probability"] = phase13["probability"]
        else:
            evidence["qdcl_probability"] = None

        # Extract from Phase 15 (temporal stability)
        phase15 = phase_inputs.get("phase15", {})
        if "stability_score" in phase15:
            evidence["temporal_stability"] = phase15["stability_score"]
        else:
            evidence["temporal_stability"] = None

        # Extract from Phase 17 (ethical score)
        phase17 = phase_inputs.get("phase17", {})
        if "global_ethics_score" in phase17:
            evidence["ethical_score"] = phase17["global_ethics_score"]
        else:
            evidence["ethical_score"] = None

        # Extract from Phase 11 (self-healing risk)
        phase11 = phase_inputs.get("phase11", {})
        if "risk_score" in phase11:
            # Invert risk score (lower risk = higher score)
            evidence["self_healing_risk"] = 1.0 - phase11["risk_score"]
        else:
            evidence["self_healing_risk"] = None

        return evidence

    def _score_to_outcome(
        self, score: DecisionScore, policy_results: list[PolicyCheckResult]
    ) -> DecisionOutcome:
        """Map decision score to outcome.

        Args:
            score: Decision score
            policy_results: Policy check results

        Returns:
            DecisionOutcome
        """
        score_value = score.score

        # Check for medium severity violations
        medium_violations = [
            r for r in policy_results if r.severity == "medium" and r.violated
        ]

        if score_value >= APPROVE_THRESHOLD:
            if medium_violations:
                # Conditional approval despite high score
                return DecisionOutcome(
                    outcome="CONDITIONAL_APPROVE",
                    rationale=(
                        f"High score ({score_value:.3f}) but medium severity "
                        "violations present"
                    ),
                    mitigations=self._generate_mitigations(medium_violations),
                )
            else:
                return DecisionOutcome(
                    outcome="APPROVE",
                    rationale=f"Score ({score_value:.3f}) meets approval threshold",
                    mitigations=[],
                )
        elif score_value >= CONDITIONAL_THRESHOLD:
            return DecisionOutcome(
                outcome="CONDITIONAL_APPROVE",
                rationale=f"Score ({score_value:.3f}) meets conditional threshold",
                mitigations=self._generate_mitigations(policy_results),
            )
        elif score_value >= REVIEW_THRESHOLD:
            return DecisionOutcome(
                outcome="REVIEW",
                rationale=f"Score ({score_value:.3f}) requires manual review",
                mitigations=[],
            )
        else:
            return DecisionOutcome(
                outcome="REJECT",
                rationale=f"Score ({score_value:.3f}) below minimum threshold",
                mitigations=[],
            )

    def _generate_mitigations(
        self, policy_results: list[PolicyCheckResult]
    ) -> list[str]:
        """Generate mitigation recommendations from policy violations.

        Args:
            policy_results: Policy check results

        Returns:
            List of mitigation recommendations
        """
        mitigations = []
        for result in policy_results:
            if result.violated and result.reason:
                mitigations.append(f"Address: {result.reason}")
        return mitigations

    def _build_provenance(self, seed: int, input_hash: str) -> dict[str, Any]:
        """Build provenance metadata.

        Args:
            seed: Deterministic seed
            input_hash: Input hash

        Returns:
            Provenance dictionary
        """
        return {
            "seed": seed,
            "input_hash": input_hash,
            "timestamp": datetime.now(UTC).isoformat(),
            "service_version": SERVICE_VERSION,
        }
