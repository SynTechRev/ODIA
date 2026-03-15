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

__all__ = [
    "CaseLawBuilder",
    "CaseLawRecord",
    "KeyQuote",
    "LegalDefinition",
    "CaseDefinition",
    "CaseLawDictionary",
    "DefinitionExtractor",
]
