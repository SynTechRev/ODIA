"""Tests for CaseLawBuilder and CaseLawRecord models (Prompt 8.1)."""

from pathlib import Path

import pytest

from oraculus_di_auditor.legal import CaseLawBuilder, CaseLawRecord, LegalDefinition
from oraculus_di_auditor.legal.case_law_builder import KeyQuote

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CASES_DIR = Path(__file__).parent.parent / "legal" / "cases"


def _sample_case(**overrides) -> CaseLawRecord:
    data = {
        "case_id": "test_v_example_2024",
        "name": "Test v. Example",
        "citation": "100 U.S. 1 (2024)",
        "year": 2024,
        "court": "SCOTUS",
        "doctrine": "fourth_amendment",
        "secondary_doctrines": ["due_process"],
        "summary": "A test case summary.",
        "holding": "The test holding.",
        "issue_tags": ["warrant_requirement", "digital_privacy"],
        "constitutional_basis": ["Fourth Amendment"],
        "relevance_to_audit": "Relevant to audit analysis.",
        "vote": "9-0",
        "majority_author": "Roberts, C.J.",
    }
    data.update(overrides)
    return CaseLawRecord.model_validate(data)


# ---------------------------------------------------------------------------
# CaseLawRecord model tests
# ---------------------------------------------------------------------------


def test_case_law_record_validates():
    case = _sample_case()
    assert case.case_id == "test_v_example_2024"
    assert case.year == 2024
    assert case.court == "SCOTUS"


def test_constitutional_basis_coerced_from_string():
    """Existing case files store constitutional_basis as a plain string."""
    case = CaseLawRecord.model_validate(
        {
            "case_id": "old_format",
            "name": "Old Format Case",
            "year": 1990,
            "constitutional_basis": "Fourth Amendment",
        }
    )
    assert isinstance(case.constitutional_basis, list)
    assert case.constitutional_basis == ["Fourth Amendment"]


def test_constitutional_basis_none_becomes_empty_list():
    case = CaseLawRecord.model_validate(
        {"case_id": "no_basis", "name": "No Basis", "year": 2000}
    )
    assert case.constitutional_basis == []


def test_legal_definition_model():
    defn = LegalDefinition(
        term="probable cause",
        definition="Fair probability that evidence will be found.",
        pinpoint_citation="462 U.S. 213, 238",
    )
    assert defn.binding_authority is True


def test_key_quote_under_50_words():
    quote = KeyQuote(
        text="Modern cell phones are not just another technological convenience.",
        pinpoint_citation="573 U.S. 373, 393",
        context="Establishing heightened digital privacy protection.",
    )
    assert "cell phones" in quote.text


def test_key_quote_rejects_over_50_words():
    with pytest.raises(ValueError, match="50 words"):
        KeyQuote(
            text=" ".join(["word"] * 51),
            pinpoint_citation="1 U.S. 1",
        )


def test_case_with_definitions_and_quotes():
    case = _sample_case(
        legal_definitions=[
            {
                "term": "warrant",
                "definition": "A judicial order authorizing a search.",
                "pinpoint_citation": "100 U.S. 1, 5",
            }
        ],
        key_quotes=[
            {
                "text": "Privacy in the digital age requires heightened protection.",
                "pinpoint_citation": "100 U.S. 1, 10",
            }
        ],
    )
    assert len(case.legal_definitions) == 1
    assert case.legal_definitions[0].term == "warrant"
    assert len(case.key_quotes) == 1


# ---------------------------------------------------------------------------
# CaseLawBuilder — load from existing cases dir
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_load_all_cases_returns_records():
    builder = CaseLawBuilder(CASES_DIR)
    cases = builder.load_all_cases()
    assert len(cases) >= 1
    assert all(isinstance(c, CaseLawRecord) for c in cases)


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_load_skips_index_files():
    builder = CaseLawBuilder(CASES_DIR)
    cases = builder.load_all_cases()
    ids = [c.case_id for c in cases]
    assert "SCOTUS_INDEX" not in ids
    assert "CASE_LAW_EXPANSION_INDEX" not in ids


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_load_riley_v_california():
    builder = CaseLawBuilder(CASES_DIR)
    cases = builder.load_all_cases()
    riley = next((c for c in cases if c.case_id == "riley_v_california_2014"), None)
    assert riley is not None
    assert riley.year == 2014
    assert riley.doctrine == "fourth_amendment"


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_search_by_doctrine():
    builder = CaseLawBuilder(CASES_DIR)
    results = builder.search_by_doctrine("fourth_amendment")
    assert len(results) >= 1
    assert all(
        c.doctrine == "fourth_amendment" or "fourth_amendment" in c.secondary_doctrines
        for c in results
    )


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_search_by_tag():
    builder = CaseLawBuilder(CASES_DIR)
    results = builder.search_by_tag("fourth_amendment")
    assert len(results) >= 1


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_build_doctrine_index():
    builder = CaseLawBuilder(CASES_DIR)
    index = builder.build_doctrine_index()
    assert isinstance(index, dict)
    assert len(index) >= 1
    assert all(isinstance(v, list) for v in index.values())
    # fourth_amendment should be present
    assert "fourth_amendment" in index


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_build_definition_index_empty_for_existing_simple_cases():
    """Existing simple case files have no legal_definitions."""
    builder = CaseLawBuilder(CASES_DIR)
    index = builder.build_definition_index()
    assert isinstance(index, dict)


@pytest.mark.skipif(not CASES_DIR.exists(), reason="legal/cases dir not present")
def test_export_for_rag_produces_chunks():
    builder = CaseLawBuilder(CASES_DIR)
    chunks = builder.export_for_rag()
    assert len(chunks) >= 1
    for chunk in chunks:
        assert "document_id" in chunk
        assert "content" in chunk
        assert "source_type" in chunk
        assert chunk["source_type"] == "case_law"


# ---------------------------------------------------------------------------
# CaseLawBuilder — save / reload round-trip (uses tmp_path)
# ---------------------------------------------------------------------------


def test_save_and_reload_case(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    case = _sample_case(
        legal_definitions=[
            {
                "term": "warrant",
                "definition": "Judicial authorization for a search.",
                "pinpoint_citation": "100 U.S. 1, 5",
            }
        ]
    )
    saved_path = builder.save_case(case)
    assert saved_path.exists()

    reloaded = builder.load_all_cases()
    assert len(reloaded) == 1
    assert reloaded[0].case_id == case.case_id
    assert reloaded[0].name == case.name
    assert len(reloaded[0].legal_definitions) == 1
    assert reloaded[0].legal_definitions[0].term == "warrant"


def test_save_overwrites_existing(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    case = _sample_case()
    builder.save_case(case)
    updated = _sample_case(summary="Updated summary.")
    builder.save_case(updated)
    cases = builder.load_all_cases()
    assert len(cases) == 1
    assert cases[0].summary == "Updated summary."


def test_search_by_doctrine_in_tmp(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    builder.save_case(_sample_case(doctrine="fourth_amendment"))
    builder.save_case(
        _sample_case(
            case_id="due_process_case", name="Due Process Case", doctrine="due_process"
        )
    )
    results = builder.search_by_doctrine("fourth_amendment")
    assert len(results) == 1
    assert results[0].case_id == "test_v_example_2024"


def test_search_by_doctrine_includes_secondary(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    builder.save_case(
        _sample_case(doctrine="due_process", secondary_doctrines=["fourth_amendment"])
    )
    results = builder.search_by_doctrine("fourth_amendment")
    assert len(results) == 1


def test_get_definitions_for_term(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    case = _sample_case(
        legal_definitions=[
            {
                "term": "probable cause",
                "definition": "Fair probability that evidence will be found.",
                "pinpoint_citation": "100 U.S. 1, 8",
            }
        ]
    )
    builder.save_case(case)
    defns = builder.get_definitions_for_term("probable cause")
    assert len(defns) == 1
    assert "fair probability" in defns[0].definition.lower()


def test_get_definitions_no_match(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    builder.save_case(_sample_case())
    defns = builder.get_definitions_for_term("nonexistent term")
    assert defns == []


def test_build_doctrine_index_tmp(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    builder.save_case(_sample_case(doctrine="fourth_amendment"))
    builder.save_case(
        _sample_case(
            case_id="sep_powers_case",
            name="Sep Powers Case",
            doctrine="separation_of_powers",
        )
    )
    index = builder.build_doctrine_index()
    assert "fourth_amendment" in index
    assert "due_process" in index  # secondary doctrine from _sample_case
    assert "separation_of_powers" in index
    assert "test_v_example_2024" in index["fourth_amendment"]


def test_export_for_rag_chunks(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    case = _sample_case(
        legal_definitions=[
            {
                "term": "warrant",
                "definition": "Judicial authorization.",
                "pinpoint_citation": "100 U.S. 1, 5",
            }
        ],
        key_quotes=[
            {
                "text": "Privacy in the digital age requires heightened protection.",
                "pinpoint_citation": "100 U.S. 1, 10",
            }
        ],
    )
    builder.save_case(case)
    chunks = builder.export_for_rag()
    # should produce 3 chunks: main, definitions, quotes
    assert len(chunks) == 3
    types = {c["metadata"]["chunk_type"] for c in chunks}
    assert types == {"main", "definitions", "quotes"}


def test_export_for_rag_empty_dir(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    chunks = builder.export_for_rag()
    assert chunks == []


def test_load_empty_dir(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    assert builder.load_all_cases() == []


def test_search_by_tag_tmp(tmp_path):
    builder = CaseLawBuilder(tmp_path)
    builder.save_case(
        _sample_case(issue_tags=["digital_privacy", "warrant_requirement"])
    )
    results = builder.search_by_tag("digital_privacy")
    assert len(results) == 1
    assert builder.search_by_tag("unrelated_tag") == []
