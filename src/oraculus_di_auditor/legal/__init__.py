"""Legal reference module for ODIA — case law, definitions, and doctrine indexing."""

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
