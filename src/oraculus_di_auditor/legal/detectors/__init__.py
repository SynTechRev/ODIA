"""odia_legal Phase 2 -- L-detectors package.

Exports Phase 2 detectors (L-1 through L-10, complete) and their shared base types.
"""

from ._base import DocContext, LegalDetector, LegalFinding, Severity
from .l1_statutory_applicability import L1StatutoryApplicability
from .l2_procedural_compliance import L2ProceduralCompliance
from .l3_exemption_misapplication import L3ExemptionMisapplication
from .l4_ministerial_duty import L4MinisterialDuty
from .l5_federal_grant_compliance import L5FederalGrantCompliance
from .l6_constitutional_implication import L6ConstitutionalImplication
from .l7_regulatory_authority import L7RegulatoryAuthority
from .l8_case_law_currency import L8CaseLawCurrency
from .l9_statute_citation_auditor import L9StatuteCitationAuditor
from .l10_balancing_test import L10BalancingTest

__all__ = [
    "DocContext",
    "LegalDetector",
    "LegalFinding",
    "Severity",
    "L1StatutoryApplicability",
    "L2ProceduralCompliance",
    "L3ExemptionMisapplication",
    "L4MinisterialDuty",
    "L5FederalGrantCompliance",
    "L6ConstitutionalImplication",
    "L7RegulatoryAuthority",
    "L8CaseLawCurrency",
    "L9StatuteCitationAuditor",
    "L10BalancingTest",
]

# Canonical Phase 2 detector registry -- ordered by pipeline priority
PHASE2_DETECTORS: list[LegalDetector] = [
    L1StatutoryApplicability(),    # type: ignore[list-item]
    L2ProceduralCompliance(),      # type: ignore[list-item]
    L3ExemptionMisapplication(),   # type: ignore[list-item]
    L4MinisterialDuty(),           # type: ignore[list-item]
    L5FederalGrantCompliance(),    # type: ignore[list-item]
    L6ConstitutionalImplication(), # type: ignore[list-item]
    L7RegulatoryAuthority(),       # type: ignore[list-item]
    L8CaseLawCurrency(),           # type: ignore[list-item]
    L9StatuteCitationAuditor(),    # type: ignore[list-item]
    L10BalancingTest(),            # type: ignore[list-item]
]
