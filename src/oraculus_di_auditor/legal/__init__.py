"""Legal reference module for ODIA — case law, definitions, doctrine, and L-detectors."""

from oraculus_di_auditor.legal.detectors import (
    PHASE2_DETECTORS,
    DocContext,
    L1StatutoryApplicability,
    L2ProceduralCompliance,
    L3ExemptionMisapplication,
    L4MinisterialDuty,
    L5FederalGrantCompliance,
    L6ConstitutionalImplication,
    L7RegulatoryAuthority,
    L8CaseLawCurrency,
    L9StatuteCitationAuditor,
    L10BalancingTest,
    LegalDetector,
    LegalFinding,
)
from oraculus_di_auditor.legal.cpra_corpus import CPRACorpusLoader
from oraculus_di_auditor.legal.statute_citation import (
    CalCitation,
    parse_cal_citations,
    parse_cal_single,
)
from oraculus_di_auditor.legal.case_law_builder import (
    CaseLawBuilder,
    CaseLawRecord,
    KeyQuote,
    LegalDefinition,
)
from oraculus_di_auditor.legal.definition_extractor import (
    CaseDefinition,
    CaseLawDictionary,
    DefinitionExtractor,
)
from oraculus_di_auditor.legal.reference_service import (
    DefinitionEntry,
    DoctrineLookupResult,
    LegalReferenceService,
    TermLookupResult,
)

__all__ = [
    # Phase 2 L-detectors
    "PHASE2_DETECTORS",
    "DocContext",
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
    "LegalDetector",
    "LegalFinding",
    # Phase 1 corpus / citation tools
    "CPRACorpusLoader",
    "CalCitation",
    "parse_cal_citations",
    "parse_cal_single",
    "CaseLawBuilder",
    "CaseLawRecord",
    "KeyQuote",
    "LegalDefinition",
    "CaseDefinition",
    "CaseLawDictionary",
    "DefinitionExtractor",
    "DefinitionEntry",
    "DoctrineLookupResult",
    "LegalReferenceService",
    "TermLookupResult",
]
