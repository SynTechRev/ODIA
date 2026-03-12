"""Temporal Integrity Auditor (TIA-15) for Phase 15.

Produces 7 mandatory temporal audit outputs:
1. Timeline consistency report
2. Temporal contradiction detection
3. Drift vectors
4. Retrocausal impact matrix
5. Forward-cascade criticality
6. Cross-branch divergence analysis
7. Recommended stabilizers
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .temporal_context_graph import TemporalContextGraph


class TemporalIntegrityAuditor:
    """Temporal Integrity Auditor for Phase 15.

    Produces comprehensive temporal integrity audits with 7 mandatory outputs.
    """

    # Output limits
    MAX_IMPACT_MATRIX_RESULTS = 20  # Maximum number of nodes in impact matrix output

    def __init__(self):
        """Initialize Temporal Integrity Auditor."""
        self.version = "1.0.0"
        self.audit_history: list[dict[str, Any]] = []

    def perform_temporal_audit(
        self,
        tcg: TemporalContextGraph,
        stability_report: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform complete temporal integrity audit.

        Args:
            tcg: Temporal Context Graph
            stability_report: Temporal stability analysis
            governance_policy: Temporal governance policy

        Returns:
            Complete audit with 7 mandatory outputs
        """
        timestamp = datetime.now(UTC)

        # Generate 7 mandatory outputs
        output1_timeline_consistency = self._audit_timeline_consistency(tcg)
        output2_temporal_contradictions = self._detect_temporal_contradictions(tcg)
        output3_drift_vectors = self._compute_drift_vectors(tcg, stability_report)
        output4_retrocausal_impact = self._build_retrocausal_impact_matrix(tcg)
        output5_cascade_criticality = self._assess_forward_cascade_criticality(
            tcg, governance_policy
        )
        output6_branch_divergence = self._analyze_cross_branch_divergence(tcg)
        output7_recommended_stabilizers = self._recommend_stabilizers(
            tcg, stability_report, governance_policy
        )

        audit = {
            "version": self.version,
            "timestamp": timestamp.isoformat(),
            "audit_id": f"audit_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            "temporal_context": {
                "node_count": len(tcg.nodes),
                "branch_count": len(tcg.timeline_branches),
                "stability_score": stability_report.get("stability_score", 0.0),
            },
            "output_1_timeline_consistency_report": output1_timeline_consistency,
            "output_2_temporal_contradiction_detection": (
                output2_temporal_contradictions
            ),
            "output_3_drift_vectors": output3_drift_vectors,
            "output_4_retrocausal_impact_matrix": output4_retrocausal_impact,
            "output_5_forward_cascade_criticality": output5_cascade_criticality,
            "output_6_cross_branch_divergence_analysis": output6_branch_divergence,
            "output_7_recommended_stabilizers": output7_recommended_stabilizers,
            "overall_integrity_score": self._compute_overall_integrity(
                output1_timeline_consistency,
                output2_temporal_contradictions,
                output3_drift_vectors,
                output4_retrocausal_impact,
                output5_cascade_criticality,
                output6_branch_divergence,
            ),
        }

        self.audit_history.append(audit)
        return audit

    def _audit_timeline_consistency(self, tcg: TemporalContextGraph) -> dict[str, Any]:
        """Generate timeline consistency report (Output 1).

        Args:
            tcg: Temporal Context Graph

        Returns:
            Timeline consistency report
        """
        validation = tcg.validate_temporal_consistency()

        # Analyze temporal ordering
        temporal_violations = [
            issue
            for issue in validation.get("issues", [])
            if issue.get("type") == "temporal_violation"
        ]

        # Check for gaps in timeline
        sorted_nodes = sorted(tcg.nodes.values(), key=lambda n: n.timestamp)
        temporal_gaps = []

        for i in range(len(sorted_nodes) - 1):
            gap_seconds = (
                sorted_nodes[i + 1].timestamp - sorted_nodes[i].timestamp
            ).total_seconds()
            if gap_seconds > 3600:  # Gaps larger than 1 hour
                temporal_gaps.append(
                    {
                        "from_node": sorted_nodes[i].node_id,
                        "to_node": sorted_nodes[i + 1].node_id,
                        "gap_seconds": gap_seconds,
                    }
                )

        consistency_score = (
            0.0
            if temporal_violations
            else 1.0 - (len(temporal_gaps) / max(len(sorted_nodes), 1))
        )

        return {
            "is_consistent": validation.get("valid", False),
            "consistency_score": round(max(0.0, consistency_score), 4),
            "temporal_violations": temporal_violations,
            "temporal_gaps": temporal_gaps,
            "orphaned_nodes": [
                issue
                for issue in validation.get("issues", [])
                if issue.get("type") == "orphaned_node"
            ],
            "total_nodes_analyzed": len(tcg.nodes),
        }

    def _detect_temporal_contradictions(
        self, tcg: TemporalContextGraph
    ) -> dict[str, Any]:
        """Detect temporal contradictions (Output 2).

        Split into helper analyses to reduce complexity:
        1. Causal-temporal ordering violations
        2. Probability discontinuities between neighbors
        3. Parallel timeline harmonic contradictions
        """
        contradictions: list[dict[str, Any]] = []

        contradictions.extend(self._find_causal_temporal_contradictions(tcg))
        contradictions.extend(self._find_probability_discontinuities(tcg))
        contradictions.extend(self._find_parallel_harmonic_contradictions(tcg))

        severity_breakdown = {
            "critical": sum(1 for c in contradictions if c["severity"] == "critical"),
            "high": sum(1 for c in contradictions if c["severity"] == "high"),
            "medium": sum(1 for c in contradictions if c["severity"] == "medium"),
        }

        return {
            "total_contradictions": len(contradictions),
            "severity_breakdown": severity_breakdown,
            "contradictions": contradictions,
            "requires_immediate_action": severity_breakdown["critical"] > 0,
        }

    def _find_causal_temporal_contradictions(
        self, tcg: TemporalContextGraph
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for node in tcg.nodes.values():
            for parent_id in node.causal_parent_ids:
                if parent_id in tcg.nodes:
                    parent = tcg.nodes[parent_id]
                    if parent.timestamp >= node.timestamp:
                        results.append(
                            {
                                "type": "causal_temporal",
                                "node_id": node.node_id,
                                "parent_id": parent_id,
                                "severity": "critical",
                                "message": "Effect precedes cause temporally",
                            }
                        )
        return results

    def _find_probability_discontinuities(
        self, tcg: TemporalContextGraph
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for node in tcg.nodes.values():
            for future_id in node.temporal_neighbors["future"]:
                if future_id in tcg.nodes:
                    future_node = tcg.nodes[future_id]
                    prob_change = abs(
                        node.qdcl_probability - future_node.qdcl_probability
                    )
                    if prob_change > 0.8:
                        results.append(
                            {
                                "type": "probability_discontinuity",
                                "node_id": node.node_id,
                                "future_id": future_id,
                                "severity": "high",
                                "probability_change": round(prob_change, 4),
                                "message": "Abrupt probability shift",
                            }
                        )
        return results

    def _find_parallel_harmonic_contradictions(
        self, tcg: TemporalContextGraph
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for node in tcg.nodes.values():
            for parallel in tcg.get_parallel_timelines(node.node_id):
                harmonic_ratio = node.harmonic_weight / max(
                    parallel.harmonic_weight, 0.01
                )
                if harmonic_ratio > 3.0 or harmonic_ratio < 0.33:
                    results.append(
                        {
                            "type": "parallel_harmonic_contradiction",
                            "node_id": node.node_id,
                            "parallel_id": parallel.node_id,
                            "severity": "medium",
                            "harmonic_ratio": round(harmonic_ratio, 4),
                            "message": "Parallel timelines exhibit harmonic mismatch",
                        }
                    )
        return results

    def _compute_drift_vectors(
        self, tcg: TemporalContextGraph, stability_report: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute drift vectors (Output 3).

        Args:
            tcg: Temporal Context Graph
            stability_report: Stability analysis

        Returns:
            Drift vector analysis
        """
        drift_vectors = []

        # Compute drift for each timeline branch
        for branch_id, node_ids in tcg.timeline_branches.items():
            branch_nodes = [tcg.nodes[nid] for nid in node_ids if nid in tcg.nodes]
            if len(branch_nodes) < 2:
                continue

            # Sort by timestamp
            branch_nodes.sort(key=lambda n: n.timestamp)

            # Compute harmonic drift vector
            harmonic_values = [n.harmonic_weight for n in branch_nodes]
            harmonic_drift = harmonic_values[-1] - harmonic_values[0]
            harmonic_rate = harmonic_drift / max(len(branch_nodes) - 1, 1)

            # Compute probability drift vector
            prob_values = [n.qdcl_probability for n in branch_nodes]
            prob_drift = prob_values[-1] - prob_values[0]
            prob_rate = prob_drift / max(len(branch_nodes) - 1, 1)

            # Compute uncertainty drift vector
            uncertainty_values = [n.uncertainty_index for n in branch_nodes]
            uncertainty_drift = uncertainty_values[-1] - uncertainty_values[0]
            uncertainty_rate = uncertainty_drift / max(len(branch_nodes) - 1, 1)

            drift_vectors.append(
                {
                    "branch_id": branch_id,
                    "node_count": len(branch_nodes),
                    "harmonic_drift": {
                        "total": round(harmonic_drift, 4),
                        "rate": round(harmonic_rate, 4),
                        "direction": (
                            "increasing" if harmonic_drift > 0 else "decreasing"
                        ),
                    },
                    "probability_drift": {
                        "total": round(prob_drift, 4),
                        "rate": round(prob_rate, 4),
                        "direction": "increasing" if prob_drift > 0 else "decreasing",
                    },
                    "uncertainty_drift": {
                        "total": round(uncertainty_drift, 4),
                        "rate": round(uncertainty_rate, 4),
                        "direction": (
                            "increasing" if uncertainty_drift > 0 else "decreasing"
                        ),
                    },
                    "drift_magnitude": round(
                        abs(harmonic_drift) + abs(prob_drift) + abs(uncertainty_drift),
                        4,
                    ),
                }
            )

        return {
            "total_drift_vectors": len(drift_vectors),
            "drift_vectors": drift_vectors,
            "max_drift_magnitude": (
                max((dv["drift_magnitude"] for dv in drift_vectors), default=0.0)
            ),
        }

    def _build_retrocausal_impact_matrix(
        self, tcg: TemporalContextGraph
    ) -> dict[str, Any]:
        """Build retrocausal impact matrix (Output 4).

        Args:
            tcg: Temporal Context Graph

        Returns:
            Retrocausal impact matrix
        """
        impact_matrix = []

        # For each node, compute its retrocausal impact
        for node_id, node in tcg.nodes.items():
            # Trace forward to see impact on future
            forward_path = tcg.traverse_forward(node_id, max_depth=5)

            # Compute impact score based on:
            # - Number of affected future nodes
            # - Weighted by their probabilities
            # - Weighted by harmonic values
            impact_score = 0.0
            for future_node in forward_path[1:]:  # Skip self
                impact_score += (
                    future_node.qdcl_probability * future_node.harmonic_weight
                )

            # Normalize
            normalized_impact = (
                impact_score / max(len(forward_path) - 1, 1)
                if len(forward_path) > 1
                else 0.0
            )

            impact_matrix.append(
                {
                    "node_id": node_id,
                    "timestamp": node.timestamp.isoformat(),
                    "retrocausal_impact_score": round(normalized_impact, 4),
                    "affected_future_nodes": len(forward_path) - 1,
                    "impact_category": (
                        "high"
                        if normalized_impact > 0.7
                        else "medium" if normalized_impact > 0.4 else "low"
                    ),
                }
            )

        # Sort by impact
        impact_matrix.sort(key=lambda im: im["retrocausal_impact_score"], reverse=True)

        return {
            "total_nodes": len(impact_matrix),
            "high_impact_nodes": sum(
                1 for im in impact_matrix if im["impact_category"] == "high"
            ),
            "impact_matrix": impact_matrix[: self.MAX_IMPACT_MATRIX_RESULTS],  # Top N
        }

    def _assess_forward_cascade_criticality(
        self, tcg: TemporalContextGraph, governance_policy: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess forward-cascade criticality (Output 5).

        Args:
            tcg: Temporal Context Graph
            governance_policy: Governance policy

        Returns:
            Forward-cascade criticality assessment
        """
        cascade_analysis = governance_policy.get("analysis", {}).get(
            "cascading_failure_risks", {}
        )

        cascade_risks = cascade_analysis.get("risks", [])

        # Compute criticality scores
        criticality_assessments = []

        for risk in cascade_risks:
            # Extract risk information
            cascade_prob = risk.get("cascade_probability", 0.0)
            affected_count = risk.get("affected_ancestor_count", 0)
            severity = risk.get("severity", "low")

            # Compute criticality score
            criticality_score = cascade_prob * (1.0 + affected_count * 0.1)

            criticality_assessments.append(
                {
                    "target_node_id": risk.get("target_node_id"),
                    "cascade_probability": cascade_prob,
                    "affected_ancestors": affected_count,
                    "criticality_score": round(min(criticality_score, 1.0), 4),
                    "severity": severity,
                    "requires_mitigation": criticality_score > 0.6,
                }
            )

        return {
            "total_cascade_points": len(criticality_assessments),
            "critical_cascade_count": sum(
                1 for ca in criticality_assessments if ca["requires_mitigation"]
            ),
            "criticality_assessments": sorted(
                criticality_assessments,
                key=lambda ca: ca["criticality_score"],
                reverse=True,
            ),
        }

    def _analyze_cross_branch_divergence(
        self, tcg: TemporalContextGraph
    ) -> dict[str, Any]:
        """Analyze cross-branch divergence (Output 6).

        Args:
            tcg: Temporal Context Graph

        Returns:
            Cross-branch divergence analysis
        """
        divergence_analysis = []

        # Compare all pairs of branches
        branch_ids = list(tcg.timeline_branches.keys())
        for i in range(len(branch_ids)):
            for j in range(i + 1, len(branch_ids)):
                branch1_id = branch_ids[i]
                branch2_id = branch_ids[j]

                branch1_nodes = [
                    tcg.nodes[nid]
                    for nid in tcg.timeline_branches[branch1_id]
                    if nid in tcg.nodes
                ]
                branch2_nodes = [
                    tcg.nodes[nid]
                    for nid in tcg.timeline_branches[branch2_id]
                    if nid in tcg.nodes
                ]

                if not branch1_nodes or not branch2_nodes:
                    continue

                # Compute divergence metrics
                avg_prob1 = sum(n.qdcl_probability for n in branch1_nodes) / len(
                    branch1_nodes
                )
                avg_prob2 = sum(n.qdcl_probability for n in branch2_nodes) / len(
                    branch2_nodes
                )
                prob_divergence = abs(avg_prob1 - avg_prob2)

                avg_harmonic1 = sum(n.harmonic_weight for n in branch1_nodes) / len(
                    branch1_nodes
                )
                avg_harmonic2 = sum(n.harmonic_weight for n in branch2_nodes) / len(
                    branch2_nodes
                )
                harmonic_divergence = abs(avg_harmonic1 - avg_harmonic2)

                # Overall divergence
                overall_divergence = (prob_divergence + harmonic_divergence) / 2.0

                divergence_analysis.append(
                    {
                        "branch1_id": branch1_id,
                        "branch2_id": branch2_id,
                        "probability_divergence": round(prob_divergence, 4),
                        "harmonic_divergence": round(harmonic_divergence, 4),
                        "overall_divergence": round(overall_divergence, 4),
                        "severity": (
                            "high"
                            if overall_divergence > 0.5
                            else "medium" if overall_divergence > 0.3 else "low"
                        ),
                    }
                )

        return {
            "total_branch_comparisons": len(divergence_analysis),
            "high_divergence_count": sum(
                1 for da in divergence_analysis if da["severity"] == "high"
            ),
            "divergence_analysis": sorted(
                divergence_analysis,
                key=lambda da: da["overall_divergence"],
                reverse=True,
            ),
        }

    def _recommend_stabilizers(
        self,
        tcg: TemporalContextGraph,
        stability_report: dict[str, Any],
        governance_policy: dict[str, Any],
    ) -> dict[str, Any]:
        """Recommend stabilizers (Output 7).

        Args:
            tcg: Temporal Context Graph
            stability_report: Stability report
            governance_policy: Governance policy

        Returns:
            Recommended stabilizers
        """
        stabilizers = []

        # Stabilizer 1: Address destabilization hotspots
        hotspots = stability_report.get("destabilization_hotspots", [])
        if hotspots:
            stabilizers.append(
                {
                    "type": "hotspot_stabilization",
                    "priority": 1,
                    "target_nodes": [h["node_id"] for h in hotspots[:5]],
                    "action": (
                        "Inject harmonic corrections and probability recalibration"
                    ),
                    "expected_impact": "Reduce local instability",
                }
            )

        # Stabilizer 2: Drift correction
        drift_warnings = stability_report.get("temporal_drift_warnings", [])
        if drift_warnings:
            stabilizers.append(
                {
                    "type": "drift_correction",
                    "priority": 2,
                    "target_branches": list(
                        set(
                            w.get("branch_id")
                            for w in drift_warnings
                            if w.get("branch_id")
                        )
                    ),
                    "action": "Apply temporal smoothing and harmonic rebalancing",
                    "expected_impact": "Stabilize temporal drift",
                }
            )

        # Stabilizer 3: Cascade mitigation
        cascade_risks = governance_policy.get("analysis", {}).get(
            "cascading_failure_risks", {}
        )
        if cascade_risks.get("high_severity_count", 0) > 0:
            stabilizers.append(
                {
                    "type": "cascade_mitigation",
                    "priority": 3,
                    "action": (
                        "Strengthen causal chains and increase probability margins"
                    ),
                    "expected_impact": "Prevent cascading failures",
                }
            )

        # Stabilizer 4: Branch convergence
        if len(tcg.timeline_branches) > 3:
            stabilizers.append(
                {
                    "type": "branch_convergence",
                    "priority": 4,
                    "branch_count": len(tcg.timeline_branches),
                    "action": (
                        "Merge low-probability branches or prune divergent timelines"
                    ),
                    "expected_impact": "Reduce timeline complexity",
                }
            )

        # Stabilizer 5: Uncertainty reduction
        high_uncertainty_nodes = [
            node.node_id for node in tcg.nodes.values() if node.uncertainty_index > 0.7
        ]
        if high_uncertainty_nodes:
            stabilizers.append(
                {
                    "type": "uncertainty_reduction",
                    "priority": 5,
                    "target_nodes": high_uncertainty_nodes[:10],
                    "action": "Inject additional observational data",
                    "expected_impact": "Reduce temporal uncertainty",
                }
            )

        return {
            "total_stabilizers": len(stabilizers),
            "stabilizers": stabilizers,
        }

    def _compute_overall_integrity(
        self,
        timeline_consistency: dict[str, Any],
        contradictions: dict[str, Any],
        drift_vectors: dict[str, Any],
        retrocausal_impact: dict[str, Any],
        cascade_criticality: dict[str, Any],
        branch_divergence: dict[str, Any],
    ) -> float:
        """Compute overall temporal integrity score.

        Args:
            timeline_consistency: Timeline consistency report
            contradictions: Contradiction detection
            drift_vectors: Drift vectors
            retrocausal_impact: Retrocausal impact matrix
            cascade_criticality: Cascade criticality
            branch_divergence: Branch divergence analysis

        Returns:
            Overall integrity score (0.0-1.0)
        """
        # Component scores
        consistency_score = timeline_consistency.get("consistency_score", 0.0)

        contradiction_score = max(
            0.0, 1.0 - (contradictions.get("total_contradictions", 0) / 10.0)
        )

        drift_score = max(
            0.0, 1.0 - (drift_vectors.get("max_drift_magnitude", 0.0) / 3.0)
        )

        cascade_score = max(
            0.0, 1.0 - (cascade_criticality.get("critical_cascade_count", 0) / 5.0)
        )

        divergence_score = max(
            0.0, 1.0 - (branch_divergence.get("high_divergence_count", 0) / 5.0)
        )

        # Weighted overall score
        overall = (
            0.25 * consistency_score
            + 0.25 * contradiction_score
            + 0.20 * drift_score
            + 0.15 * cascade_score
            + 0.15 * divergence_score
        )

        return round(overall, 4)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "audit_count": len(self.audit_history),
        }
