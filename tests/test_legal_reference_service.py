"""Tests for LegalReferenceService (Prompt 8.5)."""

from pathlib import Path

import pytest

from oraculus_di_auditor.legal import (
    CaseLawBuilder,
    CaseLawRecord,
    LegalReferenceService,
    TermLookupResult,
)
from oraculus_di_auditor.rag.retriever_engine import RetrievalEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LEGAL_DIR = Path(__file__).parent.parent / "legal"


def _write_dict(lexicon_dir: Path, filename: str, data: dict) -> None:
    import json

    lexicon_dir.mkdir(parents=True, exist_ok=True)
    (lexicon_dir / filename).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _make_case(
    case_id: str,
    name: str,
    year: int,
    doctrine: str = "fourth_amendment",
    court: str = "SCOTUS",
    definitions: list[dict] | None = None,
    issue_tags: list[str] | None = None,
    holding: str = "",
    relevance: str = "",
) -> CaseLawRecord:
    return CaseLawRecord.model_validate(
        {
            "case_id": case_id,
            "name": name,
            "citation": f"100 U.S. {year} ({year})",
            "year": year,
            "court": court,
            "doctrine": doctrine,
            "summary": f"Summary of {name}.",
            "holding": holding or f"Holding of {name}.",
            "issue_tags": issue_tags or [],
            "relevance_to_audit": relevance,
            "legal_definitions": definitions or [],
        }
    )


def _build_service(tmp_path: Path) -> LegalReferenceService:
    """Build a minimal LegalReferenceService with fixture data."""
    cases_dir = tmp_path / "cases"
    lexicon_dir = tmp_path / "lexicon"

    # Cases
    builder = CaseLawBuilder(cases_dir)
    builder.save_case(
        _make_case(
            "riley_v_california_2014",
            "Riley v. California",
            2014,
            doctrine="fourth_amendment",
            issue_tags=["digital_privacy", "warrant_requirement", "cell_phone"],
            holding=(
                "Police must obtain a warrant before searching a cell phone"
                " seized incident to arrest."
            ),
            relevance="Critical for digital records analysis.",
            definitions=[
                {
                    "term": "digital search",
                    "definition": (
                        "A search of digital information on a cell phone"
                        " requires a warrant."
                    ),
                }
            ],
        )
    )
    builder.save_case(
        _make_case(
            "katz_v_us_1967",
            "Katz v. United States",
            1967,
            doctrine="fourth_amendment",
            issue_tags=["reasonable_expectation", "wiretap"],
            holding="The Fourth Amendment protects people, not places.",
            relevance="Foundational privacy doctrine.",
            definitions=[
                {
                    "term": "reasonable expectation of privacy",
                    "definition": (
                        "A privacy interest that society recognizes as reasonable."
                    ),
                }
            ],
        )
    )
    builder.save_case(
        _make_case(
            "chevron_1984",
            "Chevron v. NRDC",
            1984,
            doctrine="administrative_law",
            issue_tags=["agency_deference", "statutory_interpretation"],
            holding="Courts defer to agency interpretations of ambiguous statutes.",
        )
    )

    # Dictionaries
    _write_dict(
        lexicon_dir,
        "bouvier_1856.json",
        {
            "dictionary": "bouviers_law_dictionary",
            "terms": [
                {
                    "term": "warrant",
                    "definition": (
                        "A writ issued by a magistrate authorizing an officer to"
                        " make an arrest or conduct a search."
                    ),
                    "citation": "Vol. II, p. 699",
                    "category": "civil_procedure",
                    "origin_language": "Germanic",
                },
                {
                    "term": "probable cause",
                    "definition": (
                        "Reasonable ground for belief that a crime has been committed."
                    ),
                    "citation": "Vol. II, p. 346",
                    "category": "criminal_procedure",
                    "origin_language": "Latin",
                },
            ],
        },
    )
    _write_dict(
        lexicon_dir,
        "anderson_1889.json",
        {
            "dictionary": "andersons_law_dictionary",
            "terms": [
                {
                    "term": "municipal officer",
                    "definition": (
                        "A person holding an office in a municipal corporation."
                    ),
                    "citation": "p. 764",
                    "category": "municipal_law",
                    "origin_language": "Latin",
                }
            ],
        },
    )
    _write_dict(
        lexicon_dir,
        "latin_foundational.json",
        {
            "dictionary": "latin_legal_maxims",
            "terms": [
                {
                    "latin": "habeas corpus",
                    "translation": "you have the body",
                    "jurisprudential_usage": (
                        "A writ requiring a person under arrest to be brought before"
                        " a judge to determine if detention is lawful."
                    ),
                    "doctrinal_mapping": ["constitutional_law", "due_process"],
                    "origin_language": "Latin",
                    "relevance_to_audit": (
                        "Relevant to unlawful detention systems in audit analysis."
                    ),
                }
            ],
        },
    )
    _write_dict(
        lexicon_dir,
        "wex_cornell.json",
        {
            "dictionary": "wex_cornell_legal_dictionary",
            "terms": [
                {
                    "term": "qualified immunity",
                    "definition": (
                        "Immunity protecting government officials from civil liability"
                        " unless rights were clearly established."
                    ),
                    "citation": "42 U.S.C. § 1983",
                    "category": "civil_rights",
                    "origin_language": "English",
                }
            ],
        },
    )

    svc = LegalReferenceService(legal_dir=tmp_path)
    svc.initialize()
    return svc


# ---------------------------------------------------------------------------
# initialize
# ---------------------------------------------------------------------------


def test_initialize_returns_counts(tmp_path):
    svc = _build_service(tmp_path)
    counts = svc.initialize()  # reinitialize to get fresh counts

    assert "cases" in counts
    assert counts["cases"] >= 1
    assert "bouvier_1856_terms" in counts
    assert counts["bouvier_1856_terms"] >= 1


def test_initialize_loads_all_sources(tmp_path):
    svc = _build_service(tmp_path)
    counts = svc.initialize()

    assert counts.get("bouvier_1856_terms", 0) >= 1
    assert counts.get("anderson_1889_terms", 0) >= 1
    assert counts.get("latin_foundational_terms", 0) >= 1
    assert counts.get("wex_cornell_terms", 0) >= 1


def test_initialize_auto_triggered_on_first_call(tmp_path):
    """Service auto-initializes on first method call without explicit init."""
    cases_dir = tmp_path / "cases"
    lexicon_dir = tmp_path / "lexicon"
    builder = CaseLawBuilder(cases_dir)
    builder.save_case(_make_case("c1", "Case One", 2020))
    _write_dict(lexicon_dir, "bouvier_1856.json", {"terms": []})
    _write_dict(lexicon_dir, "anderson_1889.json", {"terms": []})
    _write_dict(lexicon_dir, "latin_foundational.json", {"terms": []})
    _write_dict(lexicon_dir, "wex_cornell.json", {"terms": []})

    svc = LegalReferenceService(legal_dir=tmp_path)
    # No explicit initialize — should auto-initialize
    result = svc.lookup_term("warrant")
    assert isinstance(result, TermLookupResult)


# ---------------------------------------------------------------------------
# lookup_term
# ---------------------------------------------------------------------------


def test_lookup_term_finds_dictionary_definition(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_term("warrant")

    assert result.found is True
    assert any(d.source == "bouvier_1856" for d in result.definitions)


def test_lookup_term_finds_case_law_definition(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_term("digital search")

    assert result.found is True
    assert any(d.authority_level == "supreme_court" for d in result.definitions)
    assert any("riley" in d.source_detail.lower() for d in result.definitions)


def test_lookup_term_finds_from_multiple_sources(tmp_path):
    svc = _build_service(tmp_path)
    # "probable cause" is in bouvier and referenced in case holdings
    result = svc.lookup_term("probable cause")

    assert result.found is True
    assert len(result.definitions) >= 1
    sources = {d.source for d in result.definitions}
    assert "bouvier_1856" in sources


def test_lookup_term_ranks_by_authority(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_term("digital search")

    if len(result.definitions) >= 2:
        # SCOTUS definitions should come before dictionary entries
        first_auth = result.definitions[0].authority_level
        assert first_auth == "supreme_court"


def test_lookup_term_unknown_returns_not_found(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_term("nonexistent xyzzy term")

    assert result.found is False
    assert result.definitions == []
    assert result.case_references == []


def test_lookup_term_includes_case_references(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_term("digital")

    # riley_v_california has "digital_privacy" in issue_tags
    assert result.found is True
    case_ids = [c["case_id"] for c in result.case_references]
    assert any("riley" in cid for cid in case_ids)


def test_lookup_term_latin_maxim(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_term("habeas corpus")

    assert result.found is True
    latin_defs = [d for d in result.definitions if d.source == "latin_foundational"]
    assert len(latin_defs) >= 1
    assert result.etymology is not None
    assert "habeas corpus" in result.etymology.get("latin", "")


def test_lookup_term_sources_searched_populated(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_term("warrant")

    assert len(result.sources_searched) >= 1


# ---------------------------------------------------------------------------
# lookup_doctrine
# ---------------------------------------------------------------------------


def test_lookup_doctrine_returns_key_cases(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_doctrine("fourth_amendment")

    assert result.found is True
    assert len(result.key_cases) >= 1
    doctrines = [c["doctrine"] for c in result.key_cases]
    assert "fourth_amendment" in doctrines


def test_lookup_doctrine_current_standard_from_most_recent(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_doctrine("fourth_amendment")

    # Most recent fourth_amendment case is riley (2014) vs katz (1967)
    assert (
        "riley" in result.current_standard.lower() or "2014" in result.current_standard
    )


def test_lookup_doctrine_evolution_is_chronological(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_doctrine("fourth_amendment")

    years = [e["year"] for e in result.evolution]
    assert years == sorted(years)


def test_lookup_doctrine_unknown_returns_not_found(tmp_path):
    svc = _build_service(tmp_path)
    result = svc.lookup_doctrine("nonexistent_doctrine_xyz")

    assert result.found is False
    assert result.key_cases == []
    assert result.current_standard == ""


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


def test_search_returns_relevant_results(tmp_path):
    svc = _build_service(tmp_path)
    results = svc.search("warrant cell phone digital", top_k=5)

    assert len(results) >= 1
    assert all("document_id" in r for r in results)
    assert all("content" in r for r in results)
    assert all("score" in r for r in results)


def test_search_empty_query_returns_empty(tmp_path):
    svc = _build_service(tmp_path)
    results = svc.search("")

    assert results == []


def test_search_respects_top_k(tmp_path):
    svc = _build_service(tmp_path)
    results = svc.search("law", top_k=2)

    assert len(results) <= 2


def test_search_scores_positive(tmp_path):
    svc = _build_service(tmp_path)
    results = svc.search("warrant digital privacy")

    for r in results:
        assert r["score"] > 0


def test_search_includes_dictionary_entries(tmp_path):
    svc = _build_service(tmp_path)
    results = svc.search("municipal officer")

    source_types = {r["source_type"] for r in results}
    assert "legal_dictionary" in source_types


# ---------------------------------------------------------------------------
# export_all_for_rag
# ---------------------------------------------------------------------------


def test_export_all_for_rag_produces_chunks(tmp_path):
    svc = _build_service(tmp_path)
    chunks = svc.export_all_for_rag()

    assert len(chunks) >= 1
    for chunk in chunks:
        assert "document_id" in chunk
        assert "content" in chunk
        assert "source_type" in chunk


def test_export_all_for_rag_covers_multiple_source_types(tmp_path):
    svc = _build_service(tmp_path)
    chunks = svc.export_all_for_rag()

    source_types = {c["source_type"] for c in chunks}
    # Should have case_law and legal_dictionary entries
    assert "case_law" in source_types
    assert "legal_dictionary" in source_types


def test_export_all_for_rag_includes_case_law_definitions(tmp_path):
    svc = _build_service(tmp_path)
    chunks = svc.export_all_for_rag()

    case_def_chunks = [c for c in chunks if c["source_type"] == "case_law_definition"]
    assert len(case_def_chunks) >= 1


def test_export_all_for_rag_metadata_present(tmp_path):
    svc = _build_service(tmp_path)
    chunks = svc.export_all_for_rag()

    for chunk in chunks:
        assert "metadata" in chunk


# ---------------------------------------------------------------------------
# get_statistics
# ---------------------------------------------------------------------------


def test_get_statistics_returns_coverage_data(tmp_path):
    svc = _build_service(tmp_path)
    stats = svc.get_statistics()

    assert "cases" in stats
    assert stats["cases"] >= 1
    assert "doctrines_covered" in stats
    assert "case_law_definitions" in stats
    assert "total_dictionary_terms" in stats
    assert "total_rag_chunks" in stats


def test_get_statistics_dictionary_breakdown(tmp_path):
    svc = _build_service(tmp_path)
    stats = svc.get_statistics()

    assert "dictionary_terms" in stats
    assert isinstance(stats["dictionary_terms"], dict)
    assert "bouvier_1856" in stats["dictionary_terms"]


def test_get_statistics_sources_list(tmp_path):
    svc = _build_service(tmp_path)
    stats = svc.get_statistics()

    assert "sources" in stats
    assert "case_law" in stats["sources"]
    assert "bouvier_1856" in stats["sources"]


# ---------------------------------------------------------------------------
# RAG integration: index_legal_references
# ---------------------------------------------------------------------------


def test_retrieval_engine_index_legal_references(tmp_path):
    svc = _build_service(tmp_path)
    chunks = svc.export_all_for_rag()

    engine = RetrievalEngine()
    count = engine.index_legal_references(chunks)

    assert count == len(chunks)
    assert count >= 1


def test_retrieval_engine_can_search_legal_references(tmp_path):
    svc = _build_service(tmp_path)
    chunks = svc.export_all_for_rag()

    engine = RetrievalEngine()
    engine.index_legal_references(chunks)

    results = engine.search("warrant digital privacy", top_k=5)
    assert len(results) >= 1
    source_types = {r.source_type for r in results}
    # Should retrieve legal reference chunks
    assert any(
        st in source_types
        for st in ("case_law", "legal_dictionary", "case_law_definition")
    )


def test_retrieval_engine_legal_filter(tmp_path):
    """Legal reference chunks are searchable via source_filter."""
    svc = _build_service(tmp_path)
    chunks = svc.export_all_for_rag()

    engine = RetrievalEngine()
    engine.index_legal_references(chunks)

    # Filter to legal_dictionary source type
    results = engine.search("warrant", top_k=10, source_filter="legal_dictionary")
    # All returned results should be legal_dictionary type
    assert all(r.source_type == "legal_dictionary" for r in results)


# ---------------------------------------------------------------------------
# Integration: real legal dir (if present)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not LEGAL_DIR.exists(), reason="legal/ dir not present")
def test_initialize_from_real_legal_dir():
    svc = LegalReferenceService(legal_dir=LEGAL_DIR)
    counts = svc.initialize()

    assert counts["cases"] >= 50
    assert counts.get("bouvier_1856_terms", 0) >= 100
    assert counts.get("wex_cornell_terms", 0) >= 50


@pytest.mark.skipif(not LEGAL_DIR.exists(), reason="legal/ dir not present")
def test_real_lookup_fourth_amendment():
    svc = LegalReferenceService(legal_dir=LEGAL_DIR)
    result = svc.lookup_doctrine("fourth_amendment")

    assert result.found is True
    assert len(result.key_cases) >= 5
    assert result.current_standard != ""


@pytest.mark.skipif(not LEGAL_DIR.exists(), reason="legal/ dir not present")
def test_real_lookup_reasonable_expectation():
    svc = LegalReferenceService(legal_dir=LEGAL_DIR)
    result = svc.lookup_term("reasonable expectation of privacy")

    assert result.found is True
    assert any(d.authority_level == "supreme_court" for d in result.definitions)


@pytest.mark.skipif(not LEGAL_DIR.exists(), reason="legal/ dir not present")
def test_real_export_for_rag_volume():
    svc = LegalReferenceService(legal_dir=LEGAL_DIR)
    chunks = svc.export_all_for_rag()

    # With 64 expanded cases + 387 dict terms + 35 case definitions
    # we expect several hundred chunks
    assert len(chunks) >= 200


@pytest.mark.skipif(not LEGAL_DIR.exists(), reason="legal/ dir not present")
def test_real_rag_integration():
    svc = LegalReferenceService(legal_dir=LEGAL_DIR)
    chunks = svc.export_all_for_rag()

    engine = RetrievalEngine()
    count = engine.index_legal_references(chunks)
    assert count == len(chunks)

    results = engine.search("Fourth Amendment warrant digital privacy", top_k=10)
    assert len(results) >= 1
