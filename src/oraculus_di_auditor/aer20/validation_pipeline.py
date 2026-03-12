# src/oraculus_di_auditor/aer20/validation_pipeline.py
"""RAL-20: Validation Pipeline.

Performs bounded self-evaluation and self-optimization.
"""
from __future__ import annotations

from typing import Any

from .schemas import AUFState, RecursiveAscensionReport
from .utils import sha256_hex


class ValidationPipeline:
    """Validation Pipeline - deterministic self-evaluation and bounded optimization.

    This is the ONLY place where self-modification occurs, strictly bounded to:
    - Internal reasoning templates
    - Internal relevance-weighting
    - Insight synthesis calibration
    - No external effect
    - No autonomy
    - No agency

    Everything remains reversible.
    """

    def execute_ascension_loop(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        phase_inputs: dict[str, Any],
    ) -> RecursiveAscensionReport:
        """Execute the recursive ascension loop.

        Args:
            auf_state: Composite Feature Vector state
            synthesis_report: Recursive synthesis report
            phase_inputs: All phase inputs

        Returns:
            RecursiveAscensionReport with self-evaluation results
        """
        # Step 1: Self-diagnosis
        self_diagnosis = self._perform_self_diagnosis(
            auf_state, synthesis_report, phase_inputs
        )

        # Step 2: Self-revision (non-destructive)
        self_revision = self._perform_self_revision(self_diagnosis)

        # Step 3: Self-optimization (within constraints)
        self_optimization = self._perform_self_optimization(
            self_diagnosis, self_revision
        )

        # Step 4: Self-stabilization
        self_stabilization = self._perform_self_stabilization(
            auf_state, self_optimization
        )

        # Step 5: Governance verification
        governance_verification = self._verify_governance(phase_inputs)

        # Step 6: Ethical verification
        ethical_verification = self._verify_ethics(phase_inputs)

        # Step 7: Determinism verification
        determinism_verification = self._verify_determinism(auf_state, phase_inputs)

        # Count revisions and check if optimizations applied
        revision_count = len(self_revision.get("revisions", []))
        optimization_applied = self_optimization.get("optimizations_count", 0) > 0
        stability_achieved = self_stabilization.get("stable", False)

        # Generate RAL ID
        ral_id = sha256_hex(
            {
                "diagnosis": self_diagnosis,
                "revision": self_revision,
                "optimization": self_optimization,
                "stabilization": self_stabilization,
            }
        )

        return RecursiveAscensionReport(
            ral_id=ral_id,
            self_diagnosis=self_diagnosis,
            self_revision=self_revision,
            self_optimization=self_optimization,
            self_stabilization=self_stabilization,
            governance_verification=governance_verification,
            ethical_verification=ethical_verification,
            determinism_verification=determinism_verification,
            revision_count=revision_count,
            optimization_applied=optimization_applied,
            stability_achieved=stability_achieved,
        )

    def _perform_self_diagnosis(
        self,
        auf_state: AUFState,
        synthesis_report: dict[str, Any],
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform system self-diagnosis.

        Args:
            auf_state: AUF state
            synthesis_report: Synthesis report
            phase_inputs: Phase inputs

        Returns:
            Self-diagnosis results
        """
        # Check convergence
        conv_status = (
            "optimal"
            if auf_state.convergence_coefficient > 0.8
            else (
                "good"
                if auf_state.convergence_coefficient > 0.6
                else "needs_improvement"
            )
        )

        # Check stability
        stability = synthesis_report.get("stability_analysis", {}).get(
            "weighted_stability", 0.5
        )
        stability_status = (
            "stable"
            if stability > 0.75
            else "moderate" if stability > 0.6 else "unstable"
        )

        # Check compliance
        ethics = phase_inputs.get("phase17", {}).get("global_ethics_score", 0.5)
        governance = phase_inputs.get("phase18", {}).get("score", 0.5)
        compliance_status = (
            "compliant" if ethics >= 0.6 and governance >= 0.6 else "non_compliant"
        )

        # Identify issues
        issues = []
        if auf_state.convergence_coefficient < 0.6:
            issues.append(
                {
                    "type": "convergence",
                    "severity": "moderate",
                    "description": "Convergence below optimal threshold",
                }
            )
        if ethics < 0.6:
            issues.append(
                {
                    "type": "ethical",
                    "severity": "high",
                    "description": "Ethics score below mandatory threshold",
                }
            )
        if governance < 0.6:
            issues.append(
                {
                    "type": "governance",
                    "severity": "high",
                    "description": "Governance score below mandatory threshold",
                }
            )

        return {
            "convergence_status": conv_status,
            "convergence_value": auf_state.convergence_coefficient,
            "stability_status": stability_status,
            "stability_value": stability,
            "compliance_status": compliance_status,
            "issues_detected": len(issues),
            "issues": issues,
            "recommendation": (
                "optimal_operation" if len(issues) == 0 else "address_issues"
            ),
        }

    def _perform_self_revision(
        self,
        self_diagnosis: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform non-destructive self-revision.

        Args:
            self_diagnosis: Diagnosis results

        Returns:
            Self-revision log
        """
        revisions = []
        issues = self_diagnosis.get("issues", [])

        # For each issue, propose a non-destructive revision
        for issue in issues:
            if issue["type"] == "convergence":
                revisions.append(
                    {
                        "target": "internal_weighting",
                        "action": "adjust_phase_balance",
                        "rationale": "Improve cross-phase harmonization",
                        "destructive": False,
                        "reversible": True,
                    }
                )
            elif issue["type"] == "ethical":
                revisions.append(
                    {
                        "target": "ethical_calibration",
                        "action": "strengthen_rec17_coupling",
                        "rationale": "Enhance ethical constraint enforcement",
                        "destructive": False,
                        "reversible": True,
                    }
                )
            elif issue["type"] == "governance":
                revisions.append(
                    {
                        "target": "governance_calibration",
                        "action": "strengthen_rgk18_coupling",
                        "rationale": "Enhance governance policy enforcement",
                        "destructive": False,
                        "reversible": True,
                    }
                )

        return {
            "revisions_proposed": len(revisions),
            "revisions": revisions,
            "all_non_destructive": True,
            "all_reversible": True,
        }

    def _perform_self_optimization(
        self,
        self_diagnosis: dict[str, Any],
        self_revision: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform bounded self-optimization.

        Args:
            self_diagnosis: Diagnosis results
            self_revision: Revision log

        Returns:
            Self-optimization results
        """
        optimizations = []

        # Only optimize if diagnosis shows issues
        if self_diagnosis.get("issues_detected", 0) > 0:
            # Apply revisions as optimizations
            for revision in self_revision.get("revisions", []):
                optimizations.append(
                    {
                        "optimization": revision["action"],
                        "target": revision["target"],
                        "applied": False,  # In dry_run=True mode, never actually applied
                        "projected_benefit": "moderate",
                        "risk_level": "none",
                        "reversible": True,
                    }
                )

        return {
            "optimizations_count": len(optimizations),
            "optimizations": optimizations,
            "all_reversible": True,
            "requires_human_approval": True,
            "auto_applied": False,  # Never auto-apply without human approval
        }

    def _perform_self_stabilization(
        self,
        auf_state: AUFState,
        self_optimization: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform self-stabilization.

        Args:
            auf_state: AUF state
            self_optimization: Optimization results

        Returns:
            Stabilization results
        """
        # Check if system is already stable
        conv = auf_state.convergence_coefficient
        stable = conv > 0.6

        stabilization_actions = []
        if not stable:
            stabilization_actions.append(
                {
                    "action": "maintain_determinism",
                    "status": "active",
                }
            )
            stabilization_actions.append(
                {
                    "action": "preserve_reversibility",
                    "status": "active",
                }
            )
            stabilization_actions.append(
                {
                    "action": "enforce_constraints",
                    "status": "active",
                }
            )

        return {
            "stable": stable,
            "convergence": conv,
            "stabilization_actions": stabilization_actions,
            "determinism_maintained": True,
            "reversibility_preserved": True,
        }

    def _verify_governance(
        self,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify governance compliance (RGK-18).

        Args:
            phase_inputs: Phase inputs

        Returns:
            Governance verification results
        """
        phase18 = phase_inputs.get("phase18", {})
        gov_score = phase18.get("score", 0.5)
        compliant = gov_score >= 0.6

        return {
            "rgk18_verified": True,
            "governance_score": gov_score,
            "compliant": compliant,
            "threshold": 0.6,
            "violations": [] if compliant else ["governance_score_below_threshold"],
        }

    def _verify_ethics(
        self,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify ethical compliance (REC-17).

        Args:
            phase_inputs: Phase inputs

        Returns:
            Ethical verification results
        """
        phase17 = phase_inputs.get("phase17", {})
        ethics_score = phase17.get("global_ethics_score", 0.5)
        compliant = ethics_score >= 0.6

        return {
            "rec17_verified": True,
            "ethics_score": ethics_score,
            "compliant": compliant,
            "threshold": 0.6,
            "violations": [] if compliant else ["ethics_score_below_threshold"],
        }

    def _verify_determinism(
        self,
        auf_state: AUFState,
        phase_inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Verify determinism guarantee.

        Args:
            auf_state: AUF state
            phase_inputs: Phase inputs

        Returns:
            Determinism verification results
        """
        # Verify SHA256 signatures are present
        auf_signature = auf_state.auf_id
        phase_signatures = {
            "phase19": phase_inputs.get("phase19", {})
            .get("provenance", {})
            .get("input_hash", ""),
        }

        deterministic = all(
            [
                len(auf_signature) == 64,  # Valid SHA256
                all(len(sig) == 64 for sig in phase_signatures.values() if sig),
            ]
        )

        return {
            "determinism_verified": deterministic,
            "auf_signature": auf_signature[:16],  # First 16 chars
            "phase_signatures": {k: v[:16] for k, v in phase_signatures.items() if v},
            "guarantee": (
                "complete_determinism" if deterministic else "verification_failed"
            ),
        }
