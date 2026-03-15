"""Tests for DefinitionExtractor and CaseLawDictionary (Prompt 8.4)."""

from pathlib import Path

import pytest

from oraculus_di_auditor.legal import (
    CaseLawBuilder,
    CaseLawRecord,
)
from oraculus_di_auditor.legal.definition_extractor import (
    CaseDefinition,
    CaseLawDictionary,
    DefinitionExtractor,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CASES_DIR = Path(__file__).parent.parent / "legal" / "cases"


def _make_case(
    case_id: str,
    name: str,
    year: int,
    court: str = "SCOTUS",
    definitions: list[dict] | None = None,
) -> CaseLawRecord:
    return CaseLawRecord.model_validate(
        {
            "case_id": case_id,
            "name": name,
            "citation": f"100 U.S. {year} ({year})",
            "year": year,
            "court": court,
            "doctrine": "fourth_amendment",
            "summary": f"Summary of {name}.",
            "holding": f"Holding of {name}.",
            "legal_definitions": definitions or [],
        }
    )


def _extractor_with_cases(
    tmp_path: Path, cases: list[CaseLawRecord]
) -> DefinitionExtractor:
    builder = CaseLawBuilder(tmp_path)
    for case in cases:
        builder.save_case(case)
    return DefinitionExtractor(builder)


# ---------------------------------------------------------------------------
# CaseDefinition model
# ---------------------------------------------------------------------------


def test_case_definition_defaults():
    defn = CaseDefinition(
        term="probable cause",
        definition="A fair probability that evidence will be found.",
        case_name="Test v. Example",
        citation="100 U.S. 1 (2024)",
        year=2024,
        court="SCOTUS",
    )
    assert defn.is_holding is True
    assert defn.superseded_by is None
    assert defn.context == ""


def test_case_definition_superseded():
    defn = CaseDefinition(
        term="Chevron deference",
        definition="Courts defer to agency interpretation of ambiguous statutes.",
        case_name="Chevron v. NRDC",
        citation="467 U.S. 837 (1984)",
        year=1984,
        court="SCOTUS",
        superseded_by="Loper Bright Enterprises v. Raimondo (2024)",
    )
    assert defn.superseded_by is not None


# ---------------------------------------------------------------------------
# extract_all_definitions
# ---------------------------------------------------------------------------


def test_extract_definitions_from_cases_with_legal_definitions(tmp_path):
    cases = [
        _make_case(
            "case_a",
            "Case A",
            2010,
            definitions=[
                {
                    "term": "probable cause",
                    "definition": "Fair probability that evidence will be found.",
                    "pinpoint_citation": "100 U.S. 1, 5",
                }
            ],
        ),
        _make_case(
            "case_b",
            "Case B",
            2015,
            definitions=[
                {
                    "term": "curtilage",
                    "definition": "The area immediately surrounding a home.",
                    "pinpoint_citation": "100 U.S. 2, 8",
                }
            ],
        ),
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    all_defs = extractor.extract_all_definitions()

    assert "probable cause" in all_defs
    assert "curtilage" in all_defs
    assert len(all_defs["probable cause"]) == 1
    assert all_defs["probable cause"][0].case_name == "Case A"
    assert all_defs["curtilage"][0].year == 2015


def test_extract_returns_empty_dict_for_empty_case_set(tmp_path):
    extractor = DefinitionExtractor(CaseLawBuilder(tmp_path))
    assert extractor.extract_all_definitions() == {}


def test_multiple_definitions_for_same_term_are_preserved(tmp_path):
    cases = [
        _make_case(
            "early_case",
            "Early Case",
            1967,
            definitions=[
                {
                    "term": "reasonable expectation of privacy",
                    "definition": "Original 1967 formulation.",
                }
            ],
        ),
        _make_case(
            "later_case",
            "Later Case",
            2018,
            definitions=[
                {
                    "term": "reasonable expectation of privacy",
                    "definition": "Extended to long-term digital tracking.",
                }
            ],
        ),
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    all_defs = extractor.extract_all_definitions()

    defs = all_defs["reasonable expectation of privacy"]
    assert len(defs) == 2
    # Should be sorted chronologically
    assert defs[0].year == 1967
    assert defs[1].year == 2018


def test_extract_skips_cases_without_definitions(tmp_path):
    cases = [
        _make_case("no_defs", "No Defs Case", 2020),
        _make_case(
            "has_defs",
            "Has Defs Case",
            2021,
            definitions=[
                {"term": "warrant", "definition": "A judicial authorization."}
            ],
        ),
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    all_defs = extractor.extract_all_definitions()

    assert "warrant" in all_defs
    assert len(all_defs) == 1


# ---------------------------------------------------------------------------
# get_authoritative_definition
# ---------------------------------------------------------------------------


def test_get_authoritative_returns_most_recent_scotus(tmp_path):
    cases = [
        _make_case(
            "old_case",
            "Old Case",
            1967,
            court="SCOTUS",
            definitions=[
                {
                    "term": "search",
                    "definition": "Old definition of search.",
                }
            ],
        ),
        _make_case(
            "new_case",
            "New Case",
            2018,
            court="SCOTUS",
            definitions=[
                {
                    "term": "search",
                    "definition": "Modern digital-age definition of search.",
                }
            ],
        ),
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    best = extractor.get_authoritative_definition("search")

    assert best is not None
    assert best.year == 2018
    assert "digital" in best.definition.lower()


def test_get_authoritative_returns_none_for_unknown_term(tmp_path):
    extractor = DefinitionExtractor(CaseLawBuilder(tmp_path))
    assert extractor.get_authoritative_definition("nonexistent term") is None


def test_get_authoritative_prefers_scotus_over_lower_court(tmp_path):
    cases = [
        _make_case(
            "circuit_case",
            "Circuit Case",
            2022,
            court="9th Circuit",
            definitions=[
                {"term": "curtilage", "definition": "Circuit court definition."}
            ],
        ),
        _make_case(
            "scotus_case",
            "SCOTUS Case",
            2015,
            court="SCOTUS",
            definitions=[
                {"term": "curtilage", "definition": "Supreme Court definition."}
            ],
        ),
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    best = extractor.get_authoritative_definition("curtilage")

    assert best is not None
    assert best.court == "SCOTUS"


def test_get_authoritative_case_insensitive(tmp_path):
    cases = [
        _make_case(
            "test_case",
            "Test Case",
            2020,
            definitions=[{"term": "Probable Cause", "definition": "Fair probability."}],
        )
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    # Should find regardless of case
    assert extractor.get_authoritative_definition("probable cause") is not None
    assert extractor.get_authoritative_definition("Probable Cause") is not None


# ---------------------------------------------------------------------------
# build_case_law_dictionary
# ---------------------------------------------------------------------------


def test_build_case_law_dictionary_valid_output(tmp_path):
    cases = [
        _make_case(
            "dict_case",
            "Dictionary Case",
            2020,
            definitions=[
                {
                    "term": "warrant",
                    "definition": "A judicial authorization for search.",
                },
                {
                    "term": "probable cause",
                    "definition": "Reasonable basis to believe a crime occurred.",
                },
            ],
        )
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    dictionary = extractor.build_case_law_dictionary()

    assert isinstance(dictionary, CaseLawDictionary)
    assert dictionary.term_count == 2
    assert dictionary.case_count == 1
    assert "warrant" in dictionary.terms
    assert "probable cause" in dictionary.terms
    assert dictionary.version == "1.0.0"
    assert dictionary.generated_at != ""


def test_build_dictionary_empty_case_set(tmp_path):
    extractor = DefinitionExtractor(CaseLawBuilder(tmp_path))
    dictionary = extractor.build_case_law_dictionary()

    assert dictionary.term_count == 0
    assert dictionary.case_count == 0
    assert dictionary.terms == {}
    assert dictionary.all_definitions == {}


def test_build_dictionary_all_definitions_populated(tmp_path):
    cases = [
        _make_case(
            "early",
            "Early Case",
            1967,
            definitions=[{"term": "search", "definition": "Physical intrusion test."}],
        ),
        _make_case(
            "later",
            "Later Case",
            1967,
            definitions=[{"term": "search", "definition": "Katz expectation test."}],
        ),
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    dictionary = extractor.build_case_law_dictionary()

    # all_definitions preserves both; terms has only one (authoritative)
    assert len(dictionary.all_definitions["search"]) == 2
    assert "search" in dictionary.terms


def test_build_dictionary_coverage_stats(tmp_path):
    cases = [
        _make_case(
            "c1",
            "Case One",
            2010,
            definitions=[{"term": "term_a", "definition": "Def A."}],
        ),
        _make_case(
            "c2",
            "Case Two",
            2012,
            definitions=[
                {"term": "term_b", "definition": "Def B."},
                {"term": "term_c", "definition": "Def C."},
            ],
        ),
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    d = extractor.build_case_law_dictionary()
    assert d.term_count == 3
    assert d.case_count == 2


# ---------------------------------------------------------------------------
# export_for_rag
# ---------------------------------------------------------------------------


def test_export_for_rag_produces_chunks(tmp_path):
    cases = [
        _make_case(
            "rag_case",
            "RAG Case",
            2020,
            definitions=[
                {"term": "warrant", "definition": "Judicial authorization."},
            ],
        )
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    chunks = extractor.export_for_rag()

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["source_type"] == "case_law_definition"
    assert "document_id" in chunk
    assert "content" in chunk
    assert "warrant" in chunk["content"].lower()
    assert chunk["metadata"]["chunk_type"] == "case_law_definition"


def test_export_for_rag_empty_produces_no_chunks(tmp_path):
    extractor = DefinitionExtractor(CaseLawBuilder(tmp_path))
    assert extractor.export_for_rag() == []


def test_export_for_rag_includes_superseded_note(tmp_path):
    # Save a case that will have superseded_by set via _SUPERSEDED_BY
    case = _make_case(
        "auer_v_robbins_1997",
        "Auer v. Robbins",
        1997,
        definitions=[
            {
                "term": "Auer deference",
                "definition": "Courts defer to agency interpretation of ambiguous regs.",  # noqa: E501
            }
        ],
    )
    extractor = _extractor_with_cases(tmp_path, [case])
    chunks = extractor.export_for_rag()
    assert len(chunks) == 1
    # superseded note should appear in content
    assert "superseded" in chunks[0]["content"].lower()


def test_export_for_rag_chunk_structure(tmp_path):
    cases = [
        _make_case(
            "struct_case",
            "Structure Case",
            2021,
            definitions=[
                {
                    "term": "exclusionary rule",
                    "definition": (
                        "Evidence obtained in violation of the Fourth"
                        " Amendment is inadmissible."
                    ),
                    "context": "Fourth Amendment remedy question.",
                }
            ],
        )
    ]
    extractor = _extractor_with_cases(tmp_path, cases)
    chunks = extractor.export_for_rag()
    chunk = chunks[0]

    assert "document_id" in chunk
    assert chunk["document_id"].startswith("case_def__")
    assert "title" in chunk
    assert "Case-Law Definition:" in chunk["title"]
    assert "content" in chunk
    assert "Context:" in chunk["content"]
    assert "metadata" in chunk
    meta = chunk["metadata"]
    assert meta["term"] == "exclusionary rule"
    assert meta["year"] == 2021
    assert meta["court"] == "SCOTUS"


# ---------------------------------------------------------------------------
# Integration: real cases dir (if present)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_extract_from_real_cases_dir():
    builder = CaseLawBuilder(CASES_DIR)
    extractor = DefinitionExtractor(builder)
    all_defs = extractor.extract_all_definitions()

    assert len(all_defs) >= 1
    assert all(isinstance(v, list) for v in all_defs.values())
    assert all(
        isinstance(d, CaseDefinition) for defs in all_defs.values() for d in defs
    )


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_build_dictionary_from_real_cases():
    builder = CaseLawBuilder(CASES_DIR)
    extractor = DefinitionExtractor(builder)
    dictionary = extractor.build_case_law_dictionary()

    assert dictionary.term_count >= 1
    assert dictionary.case_count >= 1
    assert len(dictionary.terms) == dictionary.term_count
    # All authoritative defs are CaseDefinition instances
    assert all(isinstance(v, CaseDefinition) for v in dictionary.terms.values())


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_get_authoritative_katz_reasonable_expectation():
    builder = CaseLawBuilder(CASES_DIR)
    extractor = DefinitionExtractor(builder)
    best = extractor.get_authoritative_definition("reasonable expectation of privacy")
    assert best is not None
    assert "katz" in best.case_name.lower()


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_chevron_deference_marked_superseded():
    builder = CaseLawBuilder(CASES_DIR)
    extractor = DefinitionExtractor(builder)
    all_defs = extractor.extract_all_definitions()
    chevron_defs = all_defs.get("Chevron deference", [])
    assert len(chevron_defs) >= 1
    # The 1984 definition should be marked superseded
    old = next((d for d in chevron_defs if d.year == 1984), None)
    assert old is not None
    assert old.superseded_by is not None


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_real_export_for_rag_chunks():
    builder = CaseLawBuilder(CASES_DIR)
    extractor = DefinitionExtractor(builder)
    chunks = extractor.export_for_rag()
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk["source_type"] == "case_law_definition"
        assert "document_id" in chunk
        assert "content" in chunk
        assert "metadata" in chunk
