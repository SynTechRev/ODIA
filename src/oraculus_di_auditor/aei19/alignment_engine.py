# src/oraculus_di_auditor/aei19/alignment_engine.py
"""EGA-19: Ethical-Governance Alignment Engine.

Ensures all insights comply with REC-17 ethics and RGK-18 governance policies,
including Constitutional and UDHR mapping and human primacy requirements.
"""
from __future__ import annotations

from typing import Any

from .schemas import AlignmentReport
from .utils import sha256_hex


class EthicalGovernanceAlignmentEngine:
    """Validates ethical and governance compliance of insights."""

    def __init__(self):
        """Initialize EGA-19 engine."""
        # Define alignment thresholds
        self.ethical_threshold = 0.6
        self.governance_threshold = 0.6

    def check_alignment(
        self,
        phase_inputs: dict[str, Any],
    ) -> AlignmentReport:
        """Check ethical and governance alignment.

        Args:
            phase_inputs: Original phase inputs including Phase 17 and 18 results

        Returns:
            AlignmentReport with compliance assessment
        """
        # Extract Phase 17 (REC-17) and Phase 18 (RGK-18) data
        phase17 = phase_inputs.get("phase17", {})
        phase18 = phase_inputs.get("phase18", {})

        # Check REC-17 ethical compliance
        ethical_score = phase17.get("global_ethics_score", 0.5)
        rec17_compliant = ethical_score >= self.ethical_threshold

        # Check for ethical violations in Phase 17
        ethical_violations = []
        governance_violations_phase17 = phase17.get("governance_invariants", {}).get(
            "invariant_violations", []
        )

        for violation in governance_violations_phase17:
            if violation in [
                "voluntary_consent",
                "human_primacy",
                "non_discrimination",
            ]:
                ethical_violations.append(
                    f"REC-17 violation: {violation} invariant failed"
                )
                rec17_compliant = False

        # Check RGK-18 governance compliance
        governance_score = phase18.get("score", 0.5)
        rgk18_compliant = governance_score >= self.governance_threshold

        # Check for governance policy violations
        governance_violations = []
        policy_violations = phase18.get("policy_violations", [])

        for violation in policy_violations:
            # Handle both dict and object formats
            if isinstance(violation, dict):
                severity = violation.get("severity", "unknown")
                policy_id = violation.get("policy_id", "unknown")
            else:
                severity = getattr(violation, "severity", "unknown")
                policy_id = getattr(violation, "policy_id", "unknown")

            if severity in ["high", "critical"]:
                governance_violations.append(f"RGK-18 policy violation: {policy_id}")
                rgk18_compliant = False

        # Combine violations
        all_violations = ethical_violations + governance_violations

        # Generate recommendations
        recommendations = self._generate_recommendations(
            rec17_compliant,
            rgk18_compliant,
            ethical_score,
            governance_score,
            all_violations,
        )

        # Create alignment ID
        alignment_id = sha256_hex(
            {
                "ethical_score": ethical_score,
                "governance_score": governance_score,
                "violations": all_violations,
            }
        )

        return AlignmentReport(
            alignment_id=alignment_id,
            rec17_compliant=rec17_compliant,
            rgk18_compliant=rgk18_compliant,
            ethical_score=ethical_score,
            governance_score=governance_score,
            violations=all_violations,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        rec17_compliant: bool,
        rgk18_compliant: bool,
        ethical_score: float,
        governance_score: float,
        violations: list[str],
    ) -> list[str]:
        """Generate alignment improvement recommendations (refactored)."""
        recs: list[str] = []
        recs.extend(self._overall_recs(rec17_compliant, rgk18_compliant))
        if not rec17_compliant:
            recs.extend(self._rec17_specific_recs(ethical_score, violations))
        if not rgk18_compliant:
            recs.extend(self._rgk18_specific_recs(governance_score, violations))
        recs.extend(
            self._positive_recs(
                rec17_compliant,
                rgk18_compliant,
                ethical_score,
                governance_score,
            )
        )
        if not rec17_compliant:
            recs.append(
                "LEGAL: Review against Constitutional protections & UDHR Articles."
            )
        recs.append("HUMAN PRIMACY: Maintain human oversight and respect agency.")
        return recs

    def _overall_recs(self, rec17: bool, rgk18: bool) -> list[str]:
        if rec17 and rgk18:
            return [
                (
                    "System shows full ethical & governance compliance; "
                    "insights safe for autonomous application."
                )
            ]
        return [
            (
                "ATTENTION: Compliance issues must be addressed before "
                "autonomous insight application."
            )
        ]

    def _rec17_specific_recs(
        self, ethical_score: float, violations: list[str]
    ) -> list[str]:
        recs: list[str] = [
            (
                "REC-17: Ethical score "
                f"({ethical_score:.3f}) below threshold "
                f"({self.ethical_threshold:.3f}); review lattice & "
                "violations."
            )
        ]
        if any("voluntary_consent" in v for v in violations):
            recs.append(
                "CRITICAL: Voluntary consent violation; require explicit "
                "informed consent."
            )
        if any("human_primacy" in v for v in violations):
            recs.append(
                "CRITICAL: Human primacy violation; restore human decision authority."
            )
        if any("non_discrimination" in v for v in violations):
            recs.append("HIGH: Non-discrimination violation; audit for bias impacts.")
        return recs

    def _rgk18_specific_recs(
        self, governance_score: float, violations: list[str]
    ) -> list[str]:
        recs: list[str] = [
            (
                "RGK-18: Governance score "
                f"({governance_score:.3f}) below threshold "
                f"({self.governance_threshold:.3f}); review policy "
                "violations."
            )
        ]
        if any("high" in v or "critical" in v for v in violations):
            recs.append(
                "HIGH SEVERITY: Critical policy violations; escalate to "
                "governance board."
            )
        return recs

    def _positive_recs(
        self,
        rec17: bool,
        rgk18: bool,
        ethical_score: float,
        governance_score: float,
    ) -> list[str]:
        recs: list[str] = []
        if rec17 and ethical_score > 0.85:
            recs.append(
                "POSITIVE: Strong ethical alignment; reinforces "
                "responsible AI principles."
            )
        if rgk18 and governance_score > 0.85:
            recs.append(
                "POSITIVE: High governance compliance; robust policy adherence."
            )
        return recs
