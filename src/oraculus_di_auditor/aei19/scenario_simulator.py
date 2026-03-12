# src/oraculus_di_auditor/aei19/scenario_simulator.py
"""DSS-19: Deterministic Scenario Simulator.

Simulates 1-3 steps ahead using temporal vectors (P13), scalar recursion (P14),
and harmonics (P12) in a fully deterministic manner.
"""
from __future__ import annotations

from typing import Any

from .schemas import ScenarioMap, ScenarioStep, UIFState
from .utils import DeterministicRNG, seed_from_input, sha256_hex


class DeterministicScenarioSimulator:
    """Simulates future scenarios deterministically."""

    def __init__(self):
        """Initialize DSS-19 simulator."""
        self.num_steps = 3  # Simulate 3 steps ahead

    def simulate_scenario(
        self,
        uif_state: UIFState,
        phase_inputs: dict[str, Any],
    ) -> ScenarioMap:
        """Simulate deterministic scenario evolution.

        Args:
            uif_state: Current Unified Intelligence Field state
            phase_inputs: Original phase inputs for temporal/scalar data

        Returns:
            ScenarioMap with 1-3 step projections
        """
        seed = seed_from_input(phase_inputs)
        rng = DeterministicRNG(seed)

        # Extract current state
        current_coherence = uif_state.field_vector.get("dim_140", 0.5)
        current_ethical = uif_state.ethical_warp
        current_governance = uif_state.governance_weight

        # Save initial values for trajectory classification
        initial_ethical = current_ethical
        initial_governance = current_governance

        # Initialize tracking
        steps = []
        prev_ethical = current_ethical
        prev_governance = current_governance
        critical_points = []

        # Extract phase-specific evolution factors
        phase12 = phase_inputs.get("phase12", {})
        phase13 = phase_inputs.get("phase13", {})
        phase14 = phase_inputs.get("phase14", {})

        # Coherence evolution rate (from Phase 12)
        coherence_rate = phase12.get("coherence_score", 0.5) * 0.1

        # Probability evolution (from Phase 13)
        probability = phase13.get("probability", 0.5)

        # Prediction influence (from Phase 14)
        prediction_score = phase14.get("prediction_score", 0.5)

        # Simulate each step
        for step_num in range(1, self.num_steps + 1):
            # Evolve state deterministically
            state_vector = {}

            # Evolve coherence with harmonic influence
            coherence_delta = (rng.next_float() * 0.1 - 0.05) * coherence_rate
            new_coherence = max(0.0, min(1.0, current_coherence + coherence_delta))
            state_vector["coherence"] = new_coherence

            # Evolve ethical score with temporal influence
            ethical_delta = (rng.next_float() * 0.08 - 0.04) * probability
            new_ethical = max(0.0, min(1.0, prev_ethical + ethical_delta))
            state_vector["ethical"] = new_ethical

            # Evolve governance with predictive recursion
            governance_delta = (rng.next_float() * 0.08 - 0.04) * prediction_score
            new_governance = max(0.0, min(1.0, prev_governance + governance_delta))
            state_vector["governance"] = new_governance

            # Evolve other dimensions
            state_vector["stability"] = max(
                0.0, min(1.0, 0.5 + rng.next_float() * 0.3 - 0.15)
            )
            state_vector["meta_awareness"] = max(
                0.0, min(1.0, 0.5 + rng.next_float() * 0.3 - 0.15)
            )

            # Calculate deltas
            ethical_delta_abs = new_ethical - prev_ethical
            governance_delta_abs = new_governance - prev_governance

            # Assess risk based on trajectory
            risk_level = self._assess_risk(
                new_coherence,
                new_ethical,
                new_governance,
                ethical_delta_abs,
                governance_delta_abs,
            )

            # Check for critical points (large changes)
            if abs(ethical_delta_abs) > 0.15 or abs(governance_delta_abs) > 0.15:
                critical_points.append(step_num)

            # Create step
            step = ScenarioStep(
                step_number=step_num,
                state_vector=state_vector,
                ethical_delta=ethical_delta_abs,
                governance_delta=governance_delta_abs,
                risk_level=risk_level,
            )
            steps.append(step)

            # Update for next iteration
            current_coherence = new_coherence
            prev_ethical = new_ethical
            prev_governance = new_governance

        # Classify trajectory
        trajectory_type = self._classify_trajectory(
            steps, initial_ethical, initial_governance
        )

        # Assess reversibility
        reversibility = self._assess_reversibility(steps, phase_inputs)

        # Generate scenario ID
        scenario_id = sha256_hex(
            {
                "steps": [step.model_dump() for step in steps],
                "seed": seed,
            }
        )

        return ScenarioMap(
            scenario_id=scenario_id,
            steps=steps,
            trajectory_type=trajectory_type,
            reversibility=reversibility,
            critical_points=critical_points,
        )

    def _assess_risk(
        self,
        coherence: float,
        ethical: float,
        governance: float,
        ethical_delta: float,
        governance_delta: float,
    ) -> str:
        """Assess risk level for a scenario step."""
        # Check for critical thresholds
        if (
            coherence < 0.4
            or ethical < 0.4
            or governance < 0.4
            or abs(ethical_delta) > 0.2
            or abs(governance_delta) > 0.2
        ):
            return "high"

        if (
            coherence < 0.6
            or ethical < 0.6
            or governance < 0.6
            or abs(ethical_delta) > 0.1
            or abs(governance_delta) > 0.1
        ):
            return "moderate"

        if (
            coherence < 0.75
            or ethical < 0.75
            or governance < 0.75
            or abs(ethical_delta) > 0.05
            or abs(governance_delta) > 0.05
        ):
            return "low"

        return "none"

    def _classify_trajectory(
        self,
        steps: list[ScenarioStep],
        initial_ethical: float,
        initial_governance: float,
    ) -> str:
        """Classify the overall trajectory type."""
        if not steps:
            return "stable"

        # Get final state
        final_step = steps[-1]
        final_ethical = final_step.state_vector.get("ethical", 0.5)
        final_governance = final_step.state_vector.get("governance", 0.5)

        # Calculate overall change
        ethical_change = final_ethical - initial_ethical
        governance_change = final_governance - initial_governance
        total_change = (ethical_change + governance_change) / 2

        # Classify based on change
        if total_change > 0.1:
            return "improving"
        elif total_change < -0.1:
            return "degrading"
        else:
            return "stable"

    def _assess_reversibility(
        self,
        steps: list[ScenarioStep],
        phase_inputs: dict[str, Any],
    ) -> bool:
        """Assess whether scenario changes are reversible.

        Reversibility is determined by checking three criteria:
        1. No high-risk steps in the scenario
        2. Phase 17 (REC-17) ethical projection indicates reversibility
        3. No large changes (>0.2) that would be difficult to reverse

        Args:
            steps: List of scenario steps to evaluate
            phase_inputs: Original phase inputs including Phase 17 data

        Returns:
            True if scenario changes are reversible, False otherwise
        """
        # Check if any step has high risk
        has_high_risk = any(step.risk_level == "high" for step in steps)

        # Check Phase 17 reversibility
        phase17 = phase_inputs.get("phase17", {})
        projection = phase17.get("ethical_projection", {})
        rec17_reversible = projection.get("reversible", True)

        # Check for large changes
        has_large_changes = any(
            abs(step.ethical_delta) > 0.2 or abs(step.governance_delta) > 0.2
            for step in steps
        )

        # Reversible if:
        # - No high risk steps
        # - REC-17 says reversible
        # - No large irreversible changes
        return not has_high_risk and rec17_reversible and not has_large_changes
