"""Temporal Governance Policy Synthesizer (TGPS) for Phase 15.

Generates governance recommendations that consider time-dependent effects:
- Cascading future failures
- Retrocausal corrections
- Drift-risk advisories
- Multi-timeline consensus planning
- Temporal contradiction minimization

Integrates:
- Anomalies from Phase 14
- CRI (Causal Responsibility Index)
- Scalar harmonics from Phase 12
- QDCL probabilities from Phase 13
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .temporal_context_graph import TemporalContextGraph


class TemporalGovernanceSynthesizer:
    """Temporal Governance Policy Synthesizer for Phase 15.

    Generates time-aware governance recommendations based on temporal
    analysis and multi-phase integration.
    """

    def __init__(self):
        """Initialize Temporal Governance Synthesizer."""
        self.version = "1.0.0"
        self.synthesis_history: list[dict[str, Any]] = []

    def synthesize_governance_policy(
        self,
        tcg: TemporalContextGraph,
        stability_report: dict[str, Any],
        phase14_anomalies: list[dict[str, Any]] | None = None,
        cri_rankings: list[dict[str, Any]] | None = None,
        scalar_harmonics: dict[int, float] | None = None,
        qdcl_probabilities: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Synthesize temporal governance policy.

        Args:
            tcg: Temporal Context Graph
            stability_report: Temporal stability analysis
            phase14_anomalies: Anomalies from Phase 14
            cri_rankings: CRI rankings from Phase 14
            scalar_harmonics: Phase 12 scalar harmonics
            qdcl_probabilities: Phase 13 QDCL probabilities

        Returns:
            Comprehensive governance policy with recommendations
        """
        timestamp = datetime.now(UTC)

        # Generate different types of recommendations
        cascading_failures = self._analyze_cascading_failures(
            tcg, phase14_anomalies or []
        )
        retrocausal_corrections = self._identify_retrocausal_corrections(
            tcg, phase14_anomalies or []
        )
        drift_advisories = self._generate_drift_advisories(
            stability_report, scalar_harmonics or {}
        )
        multi_timeline_consensus = self._plan_multi_timeline_consensus(tcg)
        contradiction_minimization = self._minimize_temporal_contradictions(
            tcg, phase14_anomalies or []
        )

        # Integrate CRI for prioritization
        priority_map = self._build_priority_map(cri_rankings or [])

        # Generate comprehensive recommendations
        recommendations = self._generate_recommendations(
            cascading_failures,
            retrocausal_corrections,
            drift_advisories,
            multi_timeline_consensus,
            contradiction_minimization,
            priority_map,
        )

        policy = {
            "version": self.version,
            "timestamp": timestamp.isoformat(),
            "stability_score": stability_report.get("stability_score", 0.0),
            "temporal_context": {
                "node_count": len(tcg.nodes),
                "branch_count": len(tcg.timeline_branches),
                "anomaly_count": len(phase14_anomalies or []),
            },
            "analysis": {
                "cascading_failure_risks": cascading_failures,
                "retrocausal_corrections": retrocausal_corrections,
                "drift_risk_advisories": drift_advisories,
                "multi_timeline_consensus": multi_timeline_consensus,
                "temporal_contradiction_minimization": contradiction_minimization,
            },
            "recommendations": recommendations,
            "priority_map": priority_map,
            "deterministic": True,
        }

        self.synthesis_history.append(policy)
        return policy

    def _analyze_cascading_failures(
        self, tcg: TemporalContextGraph, anomalies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze potential cascading failures in future timelines.

        Args:
            tcg: Temporal Context Graph
            anomalies: Detected anomalies

        Returns:
            Cascading failure analysis
        """
        cascade_risks = []

        # Build anomaly map
        anomaly_nodes = {a.get("node_id") for a in anomalies if a.get("node_id")}

        # Check each leaf node (future endpoints)
        for leaf in tcg.get_leaf_nodes():
            # Trace backward to see how many anomalies are in the causal chain
            backward_path = tcg.traverse_backward(leaf.node_id)
            affected_nodes = [
                n.node_id for n in backward_path if n.node_id in anomaly_nodes
            ]

            if affected_nodes:
                # Calculate cascade probability
                cascade_probability = min(
                    1.0, len(affected_nodes) / max(len(backward_path), 1)
                )

                # Weight by QDCL probability
                weighted_probability = cascade_probability * leaf.qdcl_probability

                if weighted_probability > 0.3:
                    cascade_risks.append(
                        {
                            "target_node_id": leaf.node_id,
                            "timestamp": leaf.timestamp.isoformat(),
                            "cascade_probability": round(weighted_probability, 4),
                            "affected_ancestor_count": len(affected_nodes),
                            "path_length": len(backward_path),
                            "severity": (
                                "critical"
                                if weighted_probability > 0.7
                                else "high" if weighted_probability > 0.5 else "medium"
                            ),
                        }
                    )

        return {
            "total_cascade_risks": len(cascade_risks),
            "high_severity_count": sum(
                1 for r in cascade_risks if r["severity"] in ["critical", "high"]
            ),
            "risks": sorted(
                cascade_risks, key=lambda r: r["cascade_probability"], reverse=True
            ),
        }

    def _identify_retrocausal_corrections(
        self, tcg: TemporalContextGraph, anomalies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Identify retrocausal correction opportunities.

        Args:
            tcg: Temporal Context Graph
            anomalies: Detected anomalies

        Returns:
            Retrocausal correction recommendations
        """
        corrections = []

        for anomaly in anomalies:
            node_id = anomaly.get("node_id")
            if not node_id or node_id not in tcg.nodes:
                continue

            # Access node via tcg when needed; avoid unused variable warning
            # node = tcg.nodes[node_id]

            # Look backward to find potential correction points
            backward_path = tcg.traverse_backward(node_id, max_depth=5)

            for ancestor in backward_path[1:]:  # Skip the anomalous node itself
                # Correction potential based on harmonic weight and probability
                correction_potential = (
                    ancestor.harmonic_weight * ancestor.qdcl_probability
                )

                if correction_potential > 0.6:
                    corrections.append(
                        {
                            "anomaly_node_id": node_id,
                            "correction_node_id": ancestor.node_id,
                            "correction_potential": round(correction_potential, 4),
                            "temporal_distance": tcg.compute_temporal_distance(
                                node_id, ancestor.node_id
                            ),
                            "recommendation": (
                                f"Apply correction at {ancestor.node_id} "
                                f"to prevent anomaly at {node_id}"
                            ),
                        }
                    )

        return {
            "total_corrections": len(corrections),
            "corrections": sorted(
                corrections, key=lambda c: c["correction_potential"], reverse=True
            )[
                :10
            ],  # Top 10
        }

    def _generate_drift_advisories(
        self, stability_report: dict[str, Any], scalar_harmonics: dict[int, float]
    ) -> dict[str, Any]:
        """Generate drift risk advisories.

        Args:
            stability_report: Temporal stability analysis
            scalar_harmonics: Phase 12 scalar harmonics

        Returns:
            Drift risk advisories
        """
        advisories = []

        # Check temporal drift warnings
        drift_warnings = stability_report.get("temporal_drift_warnings", [])
        for warning in drift_warnings:
            advisories.append(
                {
                    "type": warning.get("type"),
                    "severity": warning.get("severity"),
                    "message": warning.get("message"),
                    "recommendation": self._get_drift_recommendation(warning),
                }
            )

        # Check harmonic deviations
        if scalar_harmonics:
            harmonic_values = list(scalar_harmonics.values())
            if harmonic_values:
                mean_harmonic = sum(harmonic_values) / len(harmonic_values)
                for layer, harmonic in scalar_harmonics.items():
                    deviation = abs(harmonic - mean_harmonic)
                    if deviation > 0.5:
                        advisories.append(
                            {
                                "type": "harmonic_deviation",
                                "severity": "medium",
                                "layer": layer,
                                "deviation": round(deviation, 4),
                                "message": (
                                    f"Layer {layer} harmonic deviates by "
                                    f"{deviation:.2f} from mean"
                                ),
                                "recommendation": f"Rebalance layer {layer} harmonics",
                            }
                        )

        return {"total_advisories": len(advisories), "advisories": advisories}

    def _get_drift_recommendation(self, warning: dict[str, Any]) -> str:
        """Get specific recommendation for drift warning.

        Args:
            warning: Drift warning

        Returns:
            Recommendation string
        """
        warning_type = warning.get("type")

        if warning_type == "harmonic_drift":
            return "Stabilize scalar harmonics across timeline branch"
        elif warning_type == "probability_drift":
            return "Recalibrate QDCL probabilities for consistency"
        elif warning_type == "increasing_uncertainty":
            return "Inject additional observational data to reduce uncertainty"
        else:
            return "Monitor and investigate drift pattern"

    def _plan_multi_timeline_consensus(
        self, tcg: TemporalContextGraph
    ) -> dict[str, Any]:
        """Plan multi-timeline consensus strategy.

        Args:
            tcg: Temporal Context Graph

        Returns:
            Multi-timeline consensus plan
        """
        if not tcg.timeline_branches:
            return {
                "branches_analyzed": 0,
                "consensus_required": False,
                "plan": [],
            }

        # Analyze parallel timelines for divergence
        branch_analysis = []

        for branch_id, node_ids in tcg.timeline_branches.items():
            if len(node_ids) < 2:
                continue

            branch_nodes = [tcg.nodes[nid] for nid in node_ids if nid in tcg.nodes]
            if not branch_nodes:
                continue

            # Compute branch characteristics
            avg_probability = sum(n.qdcl_probability for n in branch_nodes) / len(
                branch_nodes
            )
            avg_harmonic = sum(n.harmonic_weight for n in branch_nodes) / len(
                branch_nodes
            )

            branch_analysis.append(
                {
                    "branch_id": branch_id,
                    "node_count": len(branch_nodes),
                    "avg_probability": round(avg_probability, 4),
                    "avg_harmonic": round(avg_harmonic, 4),
                    "consensus_weight": round(avg_probability * avg_harmonic, 4),
                }
            )

        # Determine consensus plan
        if branch_analysis:
            # Sort by consensus weight
            branch_analysis.sort(key=lambda b: b["consensus_weight"], reverse=True)

            plan = [
                {
                    "action": "prioritize_branch",
                    "branch_id": branch_analysis[0]["branch_id"],
                    "reason": "Highest consensus weight",
                    "weight": branch_analysis[0]["consensus_weight"],
                }
            ]

            # Check for significant divergence
            if len(branch_analysis) > 1:
                weight_diff = (
                    branch_analysis[0]["consensus_weight"]
                    - branch_analysis[-1]["consensus_weight"]
                )
                if weight_diff > 0.3:
                    plan.append(
                        {
                            "action": "merge_or_prune_branches",
                            "reason": "Significant divergence detected",
                            "divergence": round(weight_diff, 4),
                        }
                    )
        else:
            plan = []

        return {
            "branches_analyzed": len(branch_analysis),
            "consensus_required": len(branch_analysis) > 1,
            "branch_analysis": branch_analysis,
            "plan": plan,
        }

    def _minimize_temporal_contradictions(
        self, tcg: TemporalContextGraph, anomalies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Identify and minimize temporal contradictions.

        Args:
            tcg: Temporal Context Graph
            anomalies: Detected anomalies

        Returns:
            Contradiction minimization strategy
        """
        contradictions = []

        # Check for causal-temporal contradictions
        for node in tcg.nodes.values():
            for parent_id in node.causal_parent_ids:
                if parent_id in tcg.nodes:
                    parent = tcg.nodes[parent_id]
                    # Contradiction if causal parent is temporally later
                    if parent.timestamp >= node.timestamp:
                        contradictions.append(
                            {
                                "type": "causal_temporal_contradiction",
                                "node_id": node.node_id,
                                "parent_id": parent_id,
                                "severity": "high",
                                "message": ("Causal parent is temporally after effect"),
                                "resolution": (
                                    "Adjust temporal ordering or causal links"
                                ),
                            }
                        )

        # Check for probability contradictions in parallel timelines
        for node in tcg.nodes.values():
            parallel_nodes = tcg.get_parallel_timelines(node.node_id)
            for parallel in parallel_nodes:
                prob_diff = abs(node.qdcl_probability - parallel.qdcl_probability)
                if prob_diff > 0.7:
                    contradictions.append(
                        {
                            "type": "probability_contradiction",
                            "node_id": node.node_id,
                            "parallel_id": parallel.node_id,
                            "severity": "medium",
                            "probability_diff": round(prob_diff, 4),
                            "message": (
                                "Parallel timelines have contradictory probabilities"
                            ),
                            "resolution": "Reconcile probability assignments",
                        }
                    )

        return {
            "total_contradictions": len(contradictions),
            "high_severity_count": sum(
                1 for c in contradictions if c.get("severity") == "high"
            ),
            "contradictions": contradictions,
        }

    def _build_priority_map(
        self, cri_rankings: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Build priority map from CRI rankings.

        Args:
            cri_rankings: CRI rankings from Phase 14

        Returns:
            Priority map (node_id -> priority score)
        """
        priority_map = {}

        for ranking in cri_rankings:
            node_id = ranking.get("node_id")
            cri_score = ranking.get("cri", 0.0)
            if node_id:
                priority_map[node_id] = cri_score

        return priority_map

    def _generate_recommendations(
        self,
        cascading_failures: dict[str, Any],
        retrocausal_corrections: dict[str, Any],
        drift_advisories: dict[str, Any],
        multi_timeline_consensus: dict[str, Any],
        contradiction_minimization: dict[str, Any],
        priority_map: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Generate prioritized recommendations.

        Args:
            cascading_failures: Cascading failure analysis
            retrocausal_corrections: Retrocausal corrections
            drift_advisories: Drift advisories
            multi_timeline_consensus: Timeline consensus plan
            contradiction_minimization: Contradiction minimization
            priority_map: Priority map

        Returns:
            Prioritized list of recommendations
        """
        recommendations = []

        # Critical: Address temporal contradictions
        high_contradictions = [
            c
            for c in contradiction_minimization.get("contradictions", [])
            if c.get("severity") == "high"
        ]
        if high_contradictions:
            recommendations.append(
                {
                    "priority": 1,
                    "category": "temporal_contradiction",
                    "action": "resolve_contradictions",
                    "description": (
                        f"Resolve {len(high_contradictions)} high-severity "
                        "temporal contradictions"
                    ),
                    "urgency": "critical",
                }
            )

        # High: Address cascading failures
        high_cascade_risks = cascading_failures.get("high_severity_count", 0)
        if high_cascade_risks > 0:
            recommendations.append(
                {
                    "priority": 2,
                    "category": "cascading_failure",
                    "action": "mitigate_cascades",
                    "description": (
                        f"Mitigate {high_cascade_risks} high-severity cascade risks"
                    ),
                    "urgency": "high",
                }
            )

        # Medium: Apply retrocausal corrections
        if retrocausal_corrections.get("total_corrections", 0) > 0:
            top_corrections = retrocausal_corrections.get("corrections", [])[:3]
            if top_corrections:
                recommendations.append(
                    {
                        "priority": 3,
                        "category": "retrocausal_correction",
                        "action": "apply_corrections",
                        "description": (
                            f"Apply top {len(top_corrections)} retrocausal corrections"
                        ),
                        "corrections": top_corrections,
                        "urgency": "medium",
                    }
                )

        # Medium: Address drift advisories
        if drift_advisories.get("total_advisories", 0) > 0:
            recommendations.append(
                {
                    "priority": 4,
                    "category": "drift_management",
                    "action": "stabilize_drift",
                    "description": "Address temporal drift patterns",
                    "urgency": "medium",
                }
            )

        # Low: Implement multi-timeline consensus
        if multi_timeline_consensus.get("consensus_required", False):
            recommendations.append(
                {
                    "priority": 5,
                    "category": "timeline_consensus",
                    "action": "achieve_consensus",
                    "description": "Implement multi-timeline consensus plan",
                    "plan": multi_timeline_consensus.get("plan", []),
                    "urgency": "low",
                }
            )

        # Sort by priority
        recommendations.sort(key=lambda r: r["priority"])

        return recommendations

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "synthesis_count": len(self.synthesis_history),
        }
