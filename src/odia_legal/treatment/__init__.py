"""odia_legal.treatment — case-law currency and treatment signal extraction."""

from odia_legal.treatment.case_currency import (
    TreatmentSignal,
    check_document_currency,
    get_treatment,
    is_good_law,
    treatment_table,
)

__all__ = [
    "TreatmentSignal",
    "get_treatment",
    "is_good_law",
    "treatment_table",
    "check_document_currency",
]
