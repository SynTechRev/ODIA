"""Phase 15 Service - Omni-Contextual Temporal Governance Engine (OTGE-15).

Main orchestrator for Phase 15 that unifies:
- Phase 12: Scalar Harmonics (structural weighting)
- Phase 13: QDCL trajectory fields (quantum probabilities)
- Phase 14: Meta-Causal Predictive Governance (causal links, anomalies)

Pipeline:
1. Build Temporal Context Graph
2. Compute Temporal Stability Field
3. Run RPG-14 (existing Phase14Service)
4. Merge QDCL (Phase 13) flows
5. Apply Scalar Harmonics (Phase 12) weights
6. Generate Governance Policy Synthesis
7. Produce Temporal Integrity Audit
8. Return structured deterministic output
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .temporal_context_graph import TemporalContextGraph
from .temporal_governance_synthesizer import TemporalGovernanceSynthesizer
from .temporal_integrity_audit import TemporalIntegrityAuditor
from .temporal_stability_field import TemporalStabilityField

logger = logging.getLogger(__name__)


class Phase15Service:
    """Phase 15 Service: Omni-Contextual Temporal Governance Engine.

    The temporal-aware governance intelligence layer that sits above Phases 12-14.

    Capabilities:
    - Temporal context tracking across past/present/future
    - Multi-timeline management and branching
    - Temporal stability analysis
    - Time-aware governance synthesis
    - Comprehensive temporal integrity auditing
    """

    def __init__(self):
        """Initialize Phase 15 service."""
        self.version = "1.0.0"
        self.phase = 15

        # Initialize components
        self.tcg = TemporalContextGraph()
        self.tsf = TemporalStabilityField()
        self.tgps = TemporalGovernanceSynthesizer()
        self.tia = TemporalIntegrityAuditor()

        self.created_at = datetime.now(UTC)
        self.cycle_count = 0
        self.execution_history: list[dict[str, Any]] = []

        logger.info("Phase 15 Service initialized - OTGE-15 active")

    def run_cycle(
        self,
        system_state: dict[str, Any],
        phase12_harmonics: dict[int, float] | None = None,
        phase13_probabilities: dict[str, float] | None = None,
        phase14_outputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a complete OTGE-15 cycle.

        Args:
            system_state: Current system state
            phase12_harmonics: Scalar harmonic weights from Phase 12
            phase13_probabilities: QDCL probabilities from Phase 13
            phase14_outputs: Complete outputs from Phase 14 (RPG-14)

        Returns:
            Complete OTGE-15 cycle output with all temporal analysis
        """
        cycle_start = datetime.now(UTC)
        self.cycle_count += 1

        logger.info(f"Starting OTGE-15 cycle {self.cycle_count}")

        # Step 1: Build Temporal Context Graph
        logger.info("Step 1: Building Temporal Context Graph")
        self._build_temporal_context(
            system_state, phase12_harmonics, phase13_probabilities, phase14_outputs
        )

        # Step 2: Compute Temporal Stability Field
        logger.info("Step 2: Computing Temporal Stability Field")
        anomalies = self._extract_anomalies(phase14_outputs)
        stability_report = self.tsf.compute_stability(self.tcg, anomalies)

        # Step 3: Extract Phase 14 outputs
        logger.info("Step 3: Extracting Phase 14 outputs")
        phase14_data = self._process_phase14_outputs(phase14_outputs or {})

        # Step 4: Merge QDCL inputs
        logger.info("Step 4: Merging QDCL inputs")
        qdcl_inputs = self._merge_qdcl_inputs(phase13_probabilities or {})

        # Step 5: Apply Scalar Harmonics
        logger.info("Step 5: Applying Scalar Harmonics")
        harmonic_inputs = self._apply_scalar_harmonics(phase12_harmonics or {})

        # Step 6: Generate Governance Policy Synthesis
        logger.info("Step 6: Generating Governance Policy Synthesis")
        cri_rankings = phase14_data.get("cri_rankings", [])
        governance_policy = self.tgps.synthesize_governance_policy(
            self.tcg,
            stability_report,
            anomalies,
            cri_rankings,
            phase12_harmonics,
            phase13_probabilities,
        )

        # Step 7: Produce Temporal Integrity Audit
        logger.info("Step 7: Producing Temporal Integrity Audit")
        temporal_audit = self.tia.perform_temporal_audit(
            self.tcg, stability_report, governance_policy
        )

        cycle_end = datetime.now(UTC)
        execution_time = (cycle_end - cycle_start).total_seconds()

        result = {
            "version": self.version,
            "phase": self.phase,
            "cycle": self.cycle_count,
            "timestamp": cycle_start.isoformat(),
            "execution_time_seconds": round(execution_time, 4),
            "temporal_graph": self._serialize_temporal_graph(),
            "temporal_stability": stability_report,
            "temporal_governance": governance_policy,
            "temporal_audit": temporal_audit,
            "phase14_outputs": phase14_data,
            "qdcl_inputs": qdcl_inputs,
            "harmonic_inputs": harmonic_inputs,
            "summary": {
                "total_temporal_nodes": len(self.tcg.nodes),
                "timeline_branches": len(self.tcg.timeline_branches),
                "stability_score": stability_report.get("stability_score", 0.0),
                "integrity_score": temporal_audit.get("overall_integrity_score", 0.0),
                "anomaly_count": len(anomalies),
                "recommendation_count": len(
                    governance_policy.get("recommendations", [])
                ),
            },
        }

        self.execution_history.append(result)
        logger.info(f"OTGE-15 cycle {self.cycle_count} complete")

        return result

    def _build_temporal_context(
        self,
        system_state: dict[str, Any],
        phase12_harmonics: dict[int, float] | None,
        phase13_probabilities: dict[str, float] | None,
        phase14_outputs: dict[str, Any] | None,
    ):
        """Build temporal context graph from inputs.

        Args:
            system_state: System state
            phase12_harmonics: Phase 12 harmonics
            phase13_probabilities: Phase 13 probabilities
            phase14_outputs: Phase 14 outputs
        """
        # Add current state as temporal slice
        components = system_state.get("components", [])
        if isinstance(components, dict):
            components = list(components.values())

        # Compute average harmonic and probability
        avg_harmonic = 1.0
        if phase12_harmonics:
            harmonics = list(phase12_harmonics.values())
            avg_harmonic = sum(harmonics) / len(harmonics) if harmonics else 1.0

        avg_probability = 1.0
        if phase13_probabilities:
            probabilities = list(phase13_probabilities.values())
            avg_probability = (
                sum(probabilities) / len(probabilities) if probabilities else 1.0
            )

        # Add temporal slices for system components
        node_map = {}
        for i, component in enumerate(components):
            if isinstance(component, dict):
                comp_id = component.get("id", f"comp_{i}")
                harmonic = (
                    phase12_harmonics.get(i, avg_harmonic)
                    if phase12_harmonics
                    else avg_harmonic
                )
                probability = (
                    phase13_probabilities.get(comp_id, avg_probability)
                    if phase13_probabilities
                    else avg_probability
                )

                # Extract causal parents from phase14 if available
                causal_parents = []
                if phase14_outputs:
                    # Simplified: treat component dependencies as causal links
                    # Removed previously unused variable reference
                    _ = phase14_outputs.get("causal_graph", {})

                node = self.tcg.add_temporal_slice(
                    state_vector=component,
                    harmonic_weight=harmonic,
                    qdcl_probability=probability,
                    causal_parent_ids=causal_parents,
                    uncertainty_index=component.get("uncertainty", 0.0),
                    metadata={"component_id": comp_id, "cycle": self.cycle_count},
                )
                node_map[comp_id] = node.node_id

        # Link temporal neighbors based on dependencies
        dependencies = system_state.get("dependencies", [])
        for dep in dependencies:
            if isinstance(dep, dict):
                source = dep.get("source")
                target = dep.get("target")
                if source in node_map and target in node_map:
                    # Link target to source as past neighbor (source precedes target)
                    self.tcg.link_temporal_neighbors(
                        node_map[target], past_ids=[node_map[source]]
                    )
                    self.tcg.link_temporal_neighbors(
                        node_map[source], future_ids=[node_map[target]]
                    )

    def _extract_anomalies(
        self, phase14_outputs: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """Extract anomalies from Phase 14 outputs.

        Args:
            phase14_outputs: Phase 14 outputs

        Returns:
            List of anomalies
        """
        if not phase14_outputs:
            return []

        anomaly_report = phase14_outputs.get("anomaly_report", {})
        if not anomaly_report:
            return []

        anomalies = []

        # Extract from break locations
        breaks = anomaly_report.get("output_2_break_locations", {}).get("locations", [])
        for break_item in breaks:
            anomalies.append(
                {
                    "type": "causal_break",
                    "node_id": break_item.get("node_id"),
                    "severity": break_item.get("severity"),
                    "source": "phase14",
                }
            )

        # Extract from contradictions
        contradictions = anomaly_report.get("output_3_contradiction_map", {}).get(
            "contradictions", []
        )
        for contradiction in contradictions:
            anomalies.append(
                {
                    "type": "contradiction",
                    "node_id": contradiction.get("node_id"),
                    "severity": contradiction.get("severity"),
                    "source": "phase14",
                }
            )

        return anomalies

    def _process_phase14_outputs(
        self, phase14_outputs: dict[str, Any]
    ) -> dict[str, Any]:
        """Process Phase 14 outputs for integration.

        Args:
            phase14_outputs: Raw Phase 14 outputs

        Returns:
            Processed Phase 14 data
        """
        if not phase14_outputs:
            return {
                "available": False,
                "cri_rankings": [],
                "anomaly_count": 0,
                "governance_health": "unknown",
            }

        cri_data = phase14_outputs.get("cri_rankings", {})
        cri_rankings = (
            cri_data.get("rankings", []) if isinstance(cri_data, dict) else []
        )

        anomaly_report = phase14_outputs.get("anomaly_report", {})
        anomaly_summary = anomaly_report.get("output_1_anomaly_summary", {})
        anomaly_count = anomaly_summary.get("total_anomalies", 0)

        governance_audit = phase14_outputs.get("governance_audit", {})
        governance_health = governance_audit.get("health_status", "unknown")

        return {
            "available": True,
            "cri_rankings": cri_rankings,
            "anomaly_count": anomaly_count,
            "governance_health": governance_health,
            "phase14_cycle": phase14_outputs.get("cycle", 0),
        }

    def _merge_qdcl_inputs(
        self, phase13_probabilities: dict[str, float]
    ) -> dict[str, Any]:
        """Merge QDCL inputs from Phase 13.

        Args:
            phase13_probabilities: QDCL probabilities

        Returns:
            Merged QDCL inputs
        """
        if not phase13_probabilities:
            return {
                "available": False,
                "probability_count": 0,
                "avg_probability": 1.0,
            }

        probabilities = list(phase13_probabilities.values())
        avg_probability = (
            sum(probabilities) / len(probabilities) if probabilities else 1.0
        )

        return {
            "available": True,
            "probability_count": len(phase13_probabilities),
            "avg_probability": round(avg_probability, 4),
            "min_probability": round(min(probabilities), 4) if probabilities else 1.0,
            "max_probability": round(max(probabilities), 4) if probabilities else 1.0,
        }

    def _apply_scalar_harmonics(
        self, phase12_harmonics: dict[int, float]
    ) -> dict[str, Any]:
        """Apply scalar harmonics from Phase 12.

        Args:
            phase12_harmonics: Scalar harmonic weights

        Returns:
            Applied harmonic inputs
        """
        if not phase12_harmonics:
            return {
                "available": False,
                "layer_count": 0,
                "avg_harmonic": 1.0,
            }

        harmonics = list(phase12_harmonics.values())
        avg_harmonic = sum(harmonics) / len(harmonics) if harmonics else 1.0

        return {
            "available": True,
            "layer_count": len(phase12_harmonics),
            "avg_harmonic": round(avg_harmonic, 4),
            "min_harmonic": round(min(harmonics), 4) if harmonics else 1.0,
            "max_harmonic": round(max(harmonics), 4) if harmonics else 1.0,
        }

    def _serialize_temporal_graph(self) -> dict[str, Any]:
        """Serialize temporal graph for output.

        Returns:
            Serialized temporal graph
        """
        graph_dict = self.tcg.to_dict()

        # Add summary statistics
        graph_dict["summary"] = {
            "total_nodes": len(self.tcg.nodes),
            "root_nodes": len(self.tcg.get_root_nodes()),
            "leaf_nodes": len(self.tcg.get_leaf_nodes()),
            "timeline_branches": len(self.tcg.timeline_branches),
            "validation": self.tcg.validate_temporal_consistency(),
        }

        return graph_dict

    def add_temporal_slice(
        self,
        state_vector: dict[str, Any],
        harmonic_weight: float = 1.0,
        qdcl_probability: float = 1.0,
        causal_parent_ids: list[str] | None = None,
        uncertainty_index: float = 0.0,
    ) -> str:
        """Add a temporal slice to the graph.

        Args:
            state_vector: State vector for this slice
            harmonic_weight: Phase 12 harmonic weight
            qdcl_probability: Phase 13 probability
            causal_parent_ids: Phase 14 causal parent IDs
            uncertainty_index: Uncertainty measure

        Returns:
            Node ID of created slice
        """
        node = self.tcg.add_temporal_slice(
            state_vector=state_vector,
            harmonic_weight=harmonic_weight,
            qdcl_probability=qdcl_probability,
            causal_parent_ids=causal_parent_ids,
            uncertainty_index=uncertainty_index,
        )
        return node.node_id

    def create_timeline_branch(
        self, branch_point_id: str, branch_name: str | None = None
    ) -> str:
        """Create a new timeline branch.

        Args:
            branch_point_id: Node ID to branch from
            branch_name: Optional branch name

        Returns:
            Branch ID
        """
        return self.tcg.create_timeline_branch(branch_point_id, branch_name)

    def compute_stability(self) -> dict[str, Any]:
        """Compute current temporal stability.

        Returns:
            Stability report
        """
        return self.tsf.compute_stability(self.tcg)

    def get_service_info(self) -> dict[str, Any]:
        """Get service information.

        Returns:
            Service information
        """
        return {
            "version": self.version,
            "phase": self.phase,
            "created_at": self.created_at.isoformat(),
            "cycle_count": self.cycle_count,
            "temporal_graph": {
                "node_count": len(self.tcg.nodes),
                "branch_count": len(self.tcg.timeline_branches),
            },
            "components": {
                "temporal_context_graph": self.tcg.version,
                "temporal_stability_field": self.tsf.version,
                "temporal_governance_synthesizer": self.tgps.version,
                "temporal_integrity_auditor": self.tia.version,
            },
        }

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Get execution history.

        Returns:
            List of cycle outputs
        """
        return self.execution_history

    def to_dict(self) -> dict[str, Any]:
        """Convert service to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "phase": self.phase,
            "cycle_count": self.cycle_count,
            "service_info": self.get_service_info(),
            "temporal_graph": self.tcg.to_dict(),
            "components": {
                "temporal_stability_field": self.tsf.to_dict(),
                "temporal_governance_synthesizer": self.tgps.to_dict(),
                "temporal_integrity_auditor": self.tia.to_dict(),
            },
        }
