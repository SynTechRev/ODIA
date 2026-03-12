# src/oraculus_di_auditor/rec17/legal_mapping.py
"""Legal & Constitutional Mapping (LCM-17) - Symbolic legal analysis."""
from __future__ import annotations

from typing import Any

from .schemas import LegalMap


class LegalConstitutionalMapper:
    """Maps actions to legal and constitutional frameworks.

    Note: This is SYMBOLIC analysis only, not legal advice.
    """

    # Constitutional concerns (US Constitution)
    CONSTITUTIONAL_FRAMEWORKS = {
        "first_amendment": [
            "freedom_of_speech",
            "freedom_of_press",
            "freedom_of_assembly",
        ],
        "fourth_amendment": ["unreasonable_search", "privacy_violation"],
        "fifth_amendment": ["due_process", "self_incrimination"],
        "fourteenth_amendment": ["equal_protection", "due_process"],
    }

    # International human rights
    HUMAN_RIGHTS_FRAMEWORKS = {
        "udhr_article_1": ["dignity", "equality"],
        "udhr_article_3": ["life", "liberty", "security"],
        "udhr_article_12": ["privacy", "family", "correspondence"],
        "udhr_article_19": ["freedom_of_opinion", "freedom_of_expression"],
    }

    def map_legal_concerns(
        self,
        ethical_lattice: dict[str, Any],
        ethical_projection: dict[str, Any],
        phase16_result: dict[str, Any],
    ) -> LegalMap:
        """Map ethical analysis to legal/constitutional frameworks.

        Args:
            ethical_lattice: Ethical lattice data
            ethical_projection: Projection data
            phase16_result: Phase 16 context

        Returns:
            LegalMap with flags and compliance score
        """
        constitutional_flags = self._check_constitutional(
            ethical_lattice, ethical_projection
        )
        human_rights_flags = self._check_human_rights(
            ethical_lattice, ethical_projection
        )

        # Compute compliance score
        compliance_score = self._compute_compliance(
            constitutional_flags, human_rights_flags, ethical_lattice
        )

        return LegalMap(
            constitutional_flags=constitutional_flags,
            human_rights_flags=human_rights_flags,
            compliance_score=compliance_score,
        )

    def _check_constitutional(
        self, ethical_lattice: dict[str, Any], ethical_projection: dict[str, Any]
    ) -> list[str]:
        """Check for constitutional concerns (symbolic).

        Returns list of concern strings.
        """
        flags = []
        vector = ethical_lattice.get("ethical_vector", {})
        risk = ethical_projection.get("risk", "none")

        # Check rights impact
        rights_impact = vector.get("rights_impact", 0.5)
        if rights_impact < 0.3:
            flags.append("first_amendment:potential_speech_restriction")

        # Check autonomy and privacy
        autonomy = vector.get("autonomy_effect", 0.5)
        if autonomy < 0.3:
            flags.append("fourth_amendment:privacy_concern")
            flags.append("fifth_amendment:due_process_concern")

        # Check equality/justice implications
        if risk in ["moderate", "high"]:
            flags.append("fourteenth_amendment:equal_protection_review")

        # Governance compliance issues
        compliance = vector.get("governance_compliance", 0.5)
        if compliance < 0.4:
            flags.append("fifth_amendment:procedural_due_process")

        return flags

    def _check_human_rights(
        self, ethical_lattice: dict[str, Any], ethical_projection: dict[str, Any]
    ) -> list[str]:
        """Check for human rights concerns (symbolic).

        Returns list of concern strings.
        """
        flags = []
        vector = ethical_lattice.get("ethical_vector", {})
        harm_prob = vector.get("harm_probability", 0.5)
        autonomy = vector.get("autonomy_effect", 0.5)
        rights_impact = vector.get("rights_impact", 0.5)

        # Article 1: Dignity and equality
        if rights_impact < 0.3:
            flags.append("udhr_article_1:dignity_concern")

        # Article 3: Life, liberty, security
        if harm_prob > 0.6:
            flags.append("udhr_article_3:security_risk")

        # Article 12: Privacy
        if autonomy < 0.3:
            flags.append("udhr_article_12:privacy_violation")

        # Article 19: Freedom of expression
        if rights_impact < 0.4 and autonomy < 0.4:
            flags.append("udhr_article_19:expression_concern")

        return flags

    def _compute_compliance(
        self,
        constitutional_flags: list[str],
        human_rights_flags: list[str],
        ethical_lattice: dict[str, Any],
    ) -> float:
        """Compute overall legal compliance score.

        Score is based on:
        - Number of flags (fewer is better)
        - Ethical vector values
        """
        # Start with base ethical compliance
        vector = ethical_lattice.get("ethical_vector", {})
        base_score = vector.get("governance_compliance", 0.5)

        # Penalty for flags
        total_flags = len(constitutional_flags) + len(human_rights_flags)
        flag_penalty = min(0.3, total_flags * 0.05)  # Max 0.3 penalty

        # Adjusted score
        compliance_score = max(0.0, base_score - flag_penalty)

        # Boost for strong rights protection
        rights_impact = vector.get("rights_impact", 0.5)
        if rights_impact > 0.7 and total_flags == 0:
            compliance_score = min(1.0, compliance_score + 0.1)

        return min(1.0, max(0.0, compliance_score))
