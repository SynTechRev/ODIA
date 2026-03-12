# src/oraculus_di_auditor/aei19/intelligence_publisher.py
"""AIP-19: Applied Intelligence Publisher.

Generates the final actionable intelligence bundle:
- Narrative explanation
- Structured JSON packet
- Audit chain & governance signature
- Counterfactual options
- Reversibility instructions
"""
from __future__ import annotations

from typing import Any

from .schemas import (
    AEI19Result,
    AlignmentReport,
    InsightPacket,
    ScenarioMap,
    ScenarioStep,
    UIFState,
)
from .utils import sha256_hex


class AppliedIntelligencePublisher:
    """Publishes final applied intelligence packets."""

    def __init__(self):
        """Initialize AIP-19 publisher."""
        pass

    def publish_intelligence(
        self,
        uif_state: UIFState,
        insights: list[InsightPacket],
        alignment_report: AlignmentReport,
        scenario_map: ScenarioMap,
        phase_inputs: dict[str, Any],
    ) -> AEI19Result:
        """Generate final applied intelligence packet.

        Args:
            uif_state: Unified Intelligence Field state
            insights: Generated insights from ISE-19
            alignment_report: Alignment check from EGA-19
            scenario_map: Scenario simulation from DSS-19
            phase_inputs: Original phase inputs

        Returns:
            AEI19Result with complete intelligence package
        """
        # Generate result ID
        result_id = sha256_hex(
            {
                "uif_id": uif_state.uif_id,
                "alignment_id": alignment_report.alignment_id,
                "scenario_id": scenario_map.scenario_id,
            }
        )

        # Generate narrative explanation
        explanation = self._generate_explanation(
            uif_state, insights, alignment_report, scenario_map
        )

        # Build structured packet
        structured_packet = self._build_structured_packet(
            uif_state, insights, alignment_report, scenario_map
        )

        # Generate counterfactuals
        counterfactuals = self._generate_counterfactuals(insights, scenario_map)

        # Extract ethical basis
        ethical_basis = self._extract_ethical_basis(phase_inputs, alignment_report)

        # Extract governance basis
        governance_basis = self._extract_governance_basis(
            phase_inputs, alignment_report
        )

        # Generate determinism signature
        determinism_signature = sha256_hex(
            {
                "uif_state": uif_state.model_dump(),
                "insights": [i.model_dump() for i in insights],
                "alignment": alignment_report.model_dump(),
                "scenario": scenario_map.model_dump(),
            }
        )

        # Generate reversibility protocol
        reversibility_protocol = self._generate_reversibility_protocol(
            scenario_map, alignment_report
        )

        return AEI19Result(
            result_id=result_id,
            explanation=explanation,
            structured_packet=structured_packet,
            counterfactuals=counterfactuals,
            ethical_basis=ethical_basis,
            governance_basis=governance_basis,
            determinism_signature=determinism_signature,
            reversibility_protocol=reversibility_protocol,
        )

    def _generate_explanation(
        self,
        uif_state: UIFState,
        insights: list[InsightPacket],
        alignment_report: AlignmentReport,
        scenario_map: ScenarioMap,
    ) -> str:
        """Generate human-readable narrative explanation."""
        parts = []

        # Overview
        parts.append("# Applied Emergent Intelligence Analysis (AEI-19)")
        parts.append("")

        # UIF State Summary
        coherence = uif_state.field_vector.get("dim_140", 0.5)
        alignment = uif_state.field_vector.get("dim_141", 0.5)
        parts.append("## System State")
        parts.append(
            f"The Unified Intelligence Field demonstrates {coherence:.1%} coherence "
            f"and {alignment:.1%} cross-phase alignment. "
        )
        parts.append(
            f"Ethical alignment: {uif_state.ethical_warp:.1%}, "
            f"Governance compliance: {uif_state.governance_weight:.1%}."
        )
        parts.append("")

        # Key Insights
        parts.append("## Key Insights")
        if insights:
            for i, insight in enumerate(insights[:5], 1):  # Top 5 insights
                parts.append(f"{i}. [{insight.insight_type.upper()}] {insight.content}")
        else:
            parts.append("No significant insights generated.")
        parts.append("")

        # Alignment Status
        parts.append("## Compliance Status")
        if alignment_report.rec17_compliant and alignment_report.rgk18_compliant:
            parts.append(
                "✓ System is FULLY COMPLIANT with ethical (REC-17) and "
                "governance (RGK-18) requirements."
            )
        else:
            parts.append("⚠ System has COMPLIANCE ISSUES that require attention:")
            for violation in alignment_report.violations[:3]:  # Top 3
                parts.append(f"  - {violation}")
        parts.append("")

        # Scenario Projection
        parts.append("## Forward Projection")
        parts.append(
            "Scenario simulation shows a "
            f"{scenario_map.trajectory_type.upper()} "
            f"trajectory over {len(scenario_map.steps)} steps."
        )
        if scenario_map.reversibility:
            parts.append("Changes are REVERSIBLE.")
        else:
            parts.append("⚠ Changes may be IRREVERSIBLE - proceed with caution.")

        if scenario_map.critical_points:
            critical_str = ", ".join(map(str, scenario_map.critical_points))
            parts.append(f"Critical decision points at steps: {critical_str}")
        parts.append("")

        # Recommendations
        parts.append("## Recommendations")
        if alignment_report.recommendations:
            for rec in alignment_report.recommendations[:3]:  # Top 3
                parts.append(f"• {rec}")
        parts.append("")

        return "\n".join(parts)

    def _build_structured_packet(
        self,
        uif_state: UIFState,
        insights: list[InsightPacket],
        alignment_report: AlignmentReport,
        scenario_map: ScenarioMap,
    ) -> dict[str, Any]:
        """Build machine-readable structured intelligence packet."""
        return {
            "uif_summary": {
                "uif_id": uif_state.uif_id,
                "coherence": uif_state.field_vector.get("dim_140", 0.5),
                "alignment": uif_state.field_vector.get("dim_141", 0.5),
                "ethical_warp": uif_state.ethical_warp,
                "governance_weight": uif_state.governance_weight,
            },
            "insights": {
                "total": len(insights),
                "by_type": {
                    "analytic": len(
                        [i for i in insights if i.insight_type == "analytic"]
                    ),
                    "contextual": len(
                        [i for i in insights if i.insight_type == "contextual"]
                    ),
                    "emergent": len(
                        [i for i in insights if i.insight_type == "emergent"]
                    ),
                    "counterfactual": len(
                        [i for i in insights if i.insight_type == "counterfactual"]
                    ),
                },
                "high_confidence": len([i for i in insights if i.confidence > 0.8]),
            },
            "compliance": {
                "rec17_compliant": alignment_report.rec17_compliant,
                "rgk18_compliant": alignment_report.rgk18_compliant,
                "ethical_score": alignment_report.ethical_score,
                "governance_score": alignment_report.governance_score,
                "violations_count": len(alignment_report.violations),
            },
            "scenario": {
                "scenario_id": scenario_map.scenario_id,
                "trajectory": scenario_map.trajectory_type,
                "reversible": scenario_map.reversibility,
                "steps": len(scenario_map.steps),
                "critical_points": scenario_map.critical_points,
                "max_risk": self._get_max_risk_level(scenario_map.steps),
            },
        }

    def _get_max_risk_level(self, steps: list[ScenarioStep]) -> str:
        """Get the maximum risk level from scenario steps.

        Args:
            steps: List of scenario steps

        Returns:
            Maximum risk level: 'none', 'low', 'moderate', or 'high'
        """
        if not steps:
            return "none"

        # Define risk level ordering
        risk_order = {"none": 0, "low": 1, "moderate": 2, "high": 3}

        # Find max risk level
        max_risk = "none"
        max_value = 0

        for step in steps:
            risk_value = risk_order.get(step.risk_level, 0)
            if risk_value > max_value:
                max_value = risk_value
                max_risk = step.risk_level

        return max_risk

    def _generate_counterfactuals(
        self,
        insights: list[InsightPacket],
        scenario_map: ScenarioMap,
    ) -> list[str]:
        """Generate counterfactual scenario descriptions."""
        counterfactuals = []

        # Extract counterfactual insights
        cf_insights = [i for i in insights if i.insight_type == "counterfactual"]
        for insight in cf_insights:
            counterfactuals.append(insight.content)

        # Generate scenario-based counterfactuals
        if scenario_map.trajectory_type == "improving":
            counterfactuals.append(
                "If current positive trends were reversed, system would likely "
                "require additional oversight and approval gates."
            )
        elif scenario_map.trajectory_type == "degrading":
            counterfactuals.append(
                "If negative trends were arrested early, system could maintain "
                "current compliance levels without intervention."
            )

        # Reversibility counterfactual
        if not scenario_map.reversibility:
            counterfactuals.append(
                "If changes were designed to be reversible from the start, "
                "operational flexibility would increase significantly."
            )

        return counterfactuals

    def _extract_ethical_basis(
        self,
        phase_inputs: dict[str, Any],
        alignment_report: AlignmentReport,
    ) -> dict[str, Any]:
        """Extract ethical reasoning foundation."""
        phase17 = phase_inputs.get("phase17", {})

        return {
            "global_ethics_score": phase17.get("global_ethics_score", 0.5),
            "primary_ethic": phase17.get("ethical_lattice", {}).get(
                "primary_ethic", "unknown"
            ),
            "rec17_compliant": alignment_report.rec17_compliant,
            "ethical_framework": "REC-17 Recursive Ethical Cognition",
            "key_principles": [
                "beneficence",
                "non-maleficence",
                "justice",
                "autonomy",
                "human_primacy",
            ],
        }

    def _extract_governance_basis(
        self,
        phase_inputs: dict[str, Any],
        alignment_report: AlignmentReport,
    ) -> dict[str, Any]:
        """Extract governance reasoning foundation."""
        phase18 = phase_inputs.get("phase18", {})

        return {
            "governance_score": phase18.get("score", 0.5),
            "outcome": phase18.get("outcome", {}).get("outcome", "unknown"),
            "rgk18_compliant": alignment_report.rgk18_compliant,
            "governance_framework": "RGK-18 Recursive Governance Kernel",
            "policy_enforcement": "Deterministic multi-phase consensus",
        }

    def _generate_reversibility_protocol(
        self,
        scenario_map: ScenarioMap,
        alignment_report: AlignmentReport,
    ) -> str:
        """Generate instructions for reversing this intelligence."""
        parts = []

        parts.append("# Reversibility Protocol")
        parts.append("")

        if scenario_map.reversibility:
            parts.append("## Status: REVERSIBLE")
            parts.append("")
            parts.append("This intelligence can be safely reversed using:")
            parts.append("1. Restore previous UIF state from provenance chain")
            parts.append("2. Re-run Phase 17 (REC-17) ethical analysis")
            parts.append("3. Re-run Phase 18 (RGK-18) governance evaluation")
            parts.append("4. Verify alignment scores return to baseline")
            parts.append("5. Confirm no critical state changes occurred")
        else:
            parts.append("## Status: LIMITED REVERSIBILITY")
            parts.append("")
            parts.append("⚠ This intelligence may have irreversible components:")
            parts.append("1. Review critical decision points in scenario map")
            parts.append("2. Identify non-reversible state changes")
            parts.append("3. Require human approval before reversal")
            parts.append("4. Document reversal justification")
            parts.append("5. Execute partial rollback with governance oversight")

        parts.append("")
        parts.append("## Compliance Requirements")
        if alignment_report.rec17_compliant and alignment_report.rgk18_compliant:
            parts.append("✓ No special compliance requirements for reversal")
        else:
            parts.append("⚠ Address compliance violations before reversal:")
            for violation in alignment_report.violations:
                parts.append(f"  - {violation}")

        return "\n".join(parts)
