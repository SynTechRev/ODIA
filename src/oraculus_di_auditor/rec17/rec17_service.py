# src/oraculus_di_auditor/rec17/rec17_service.py
"""Phase17Service - Recursive Ethical Cognition orchestrator."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from .ethical_lattice import EthicalLatticeGenerator
from .ethical_projection import EthicalProjectionEngine
from .governance_invariants import GovernanceInvariantEngine
from .legal_mapping import LegalConstitutionalMapper

SERVICE_VERSION = "rec17-0.1.0"


def _sha256_hex(obj: Any) -> str:
    """Generate deterministic hash from object.

    Uses json.dumps with sort_keys for robust determinism.
    """
    json_str = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


class Phase17Service:
    """Orchestrates Phase 17: Recursive Ethical Cognition."""

    def __init__(self):
        self.lattice_generator = EthicalLatticeGenerator()
        self.projection_engine = EthicalProjectionEngine()
        self.legal_mapper = LegalConstitutionalMapper()
        self.invariant_engine = GovernanceInvariantEngine()

    def run_ethical_analysis(
        self,
        phase16_result: dict[str, Any],
        dry_run: bool = True,
        auto_apply: bool = False,
    ) -> dict[str, Any]:
        """Run complete ethical analysis cycle.

        Args:
            phase16_result: Result from Phase 16 EMCS
            dry_run: If True, suggest but do not apply changes (default: True)
            auto_apply: Allow auto-application of recommendations (default: False)

        Returns:
            Phase17Result dict with complete ethical analysis
        """
        # Compute input hash for provenance
        input_hash = _sha256_hex(phase16_result)

        # Step 1: Generate ethical lattice
        ethical_lattice_obj = self.lattice_generator.generate_lattice(phase16_result)
        ethical_lattice = ethical_lattice_obj.model_dump()

        # Step 2: Project ethical consequences
        ethical_projection_obj = self.projection_engine.project_ethics(
            ethical_lattice, phase16_result
        )
        ethical_projection = ethical_projection_obj.model_dump()

        # Step 3: Map to legal/constitutional frameworks
        legal_map_obj = self.legal_mapper.map_legal_concerns(
            ethical_lattice, ethical_projection, phase16_result
        )
        legal_map = legal_map_obj.model_dump()

        # Step 4: Check governance invariants
        governance_invariants_obj = self.invariant_engine.check_invariants(
            ethical_lattice, legal_map, phase16_result
        )
        governance_invariants = governance_invariants_obj.model_dump()

        # Step 5: Compute global ethics score
        global_ethics_score = self._compute_global_score(
            ethical_lattice, ethical_projection, legal_map, governance_invariants
        )

        # Step 6: Generate action suggestions
        action_suggestions = self._generate_action_suggestions(
            ethical_lattice,
            ethical_projection,
            legal_map,
            governance_invariants,
            dry_run,
            auto_apply,
        )

        # Step 7: Build provenance
        provenance = self._build_provenance(input_hash, dry_run, auto_apply)

        # Compose result
        result = {
            "ethical_lattice": ethical_lattice,
            "ethical_projection": ethical_projection,
            "legal_map": legal_map,
            "governance_invariants": governance_invariants,
            "global_ethics_score": global_ethics_score,
            "action_suggestions": action_suggestions,
            "provenance": provenance,
            "timestamp": datetime.now(UTC),
        }

        return result

    def _compute_global_score(
        self,
        ethical_lattice: dict[str, Any],
        ethical_projection: dict[str, Any],
        legal_map: dict[str, Any],
        governance_invariants: dict[str, Any],
    ) -> float:
        """Compute overall global ethics score.

        Weighted combination of:
        - Ethical lattice scores (40%)
        - Projection risk (20%)
        - Legal compliance (20%)
        - Governance alignment (20%)
        """
        # Ethical lattice contribution
        vector = ethical_lattice.get("ethical_vector", {})
        lattice_score = (
            vector.get("rights_impact", 0.5) * 0.3
            + (1.0 - vector.get("harm_probability", 0.5)) * 0.3
            + vector.get("autonomy_effect", 0.5) * 0.2
            + vector.get("system_stability", 0.5) * 0.1
            + vector.get("governance_compliance", 0.5) * 0.1
        )

        # Projection risk penalty
        risk = ethical_projection.get("risk", "none")
        risk_penalties = {"none": 0.0, "low": 0.05, "moderate": 0.15, "high": 0.30}
        projection_score = 1.0 - risk_penalties.get(risk, 0.15)

        # Legal compliance
        legal_score = legal_map.get("compliance_score", 0.5)

        # Governance alignment
        governance_score = governance_invariants.get("alignment_score", 0.5)

        # Weighted average
        global_score = (
            lattice_score * 0.4
            + projection_score * 0.2
            + legal_score * 0.2
            + governance_score * 0.2
        )

        return min(1.0, max(0.0, global_score))

    def _generate_action_suggestions(
        self,
        ethical_lattice: dict[str, Any],
        ethical_projection: dict[str, Any],
        legal_map: dict[str, Any],
        governance_invariants: dict[str, Any],
        dry_run: bool,
        auto_apply: bool,
    ) -> list[str]:
        """Generate actionable recommendations."""
        suggestions = []

        # Check for violations and risks
        violations = governance_invariants.get("invariant_violations", [])
        risk = ethical_projection.get("risk", "none")
        const_flags = legal_map.get("constitutional_flags", [])
        hr_flags = legal_map.get("human_rights_flags", [])

        # Add suggestions based on violations
        if "voluntary_consent" in violations:
            suggestions.append(
                "CRITICAL: Enhance user consent mechanisms to ensure "
                "voluntary participation"
            )

        if "human_primacy" in violations:
            suggestions.append(
                "HIGH: Review automated decisions for human oversight " "requirements"
            )

        if "non_discrimination" in violations or any(
            "equal_protection" in flag for flag in const_flags
        ):
            suggestions.append(
                "HIGH: Audit system for potential discriminatory impacts"
            )

        if "proportionality" in violations:
            suggestions.append(
                "MEDIUM: Reduce potential harm through proportionality review"
            )

        # Risk-based suggestions
        if risk in ["high", "moderate"]:
            suggestions.append(
                f"MEDIUM: Ethical risk level is {risk} - conduct thorough "
                "review before proceeding"
            )

        # Legal concerns
        if const_flags:
            suggestions.append(
                f"MEDIUM: Address {len(const_flags)} constitutional "
                "concern(s) identified"
            )

        if hr_flags:
            suggestions.append(
                f"LOW: Review {len(hr_flags)} human rights consideration(s)"
            )

        # Transparency
        if "transparency" in violations:
            suggestions.append(
                "LOW: Improve documentation and transparency of " "decision-making"
            )

        # Positive reinforcement
        vector = ethical_lattice.get("ethical_vector", {})
        if (
            not violations
            and risk == "none"
            and vector.get("governance_compliance", 0) > 0.8
        ):
            suggestions.append(
                "POSITIVE: Ethical analysis shows strong alignment with "
                "governance principles"
            )

        # Dry-run reminder
        if dry_run:
            suggestions.append(
                "INFO: Running in dry-run mode - no actions will be "
                "automatically applied"
            )

        # Auto-apply note
        if auto_apply and not dry_run:
            suggestions.append(
                "INFO: Auto-apply enabled - low-risk recommendations may be "
                "applied with governance approval"
            )

        return suggestions

    def _build_provenance(
        self, input_hash: str, dry_run: bool, auto_apply: bool
    ) -> dict[str, Any]:
        """Build provenance metadata."""
        return {
            "input_hash": input_hash,
            "service_version": SERVICE_VERSION,
            "timestamp": datetime.now(UTC),
            "dry_run": dry_run,
            "auto_apply": auto_apply,
        }
