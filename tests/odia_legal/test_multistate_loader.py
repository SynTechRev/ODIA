"""Tests for MultiStateCodeLoader (OR, WA, TX public records corpus)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from odia_legal.corpus.multistate_loader import MultiStateCodeLoader


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    """Write minimal corpus JSON files to a temp directory."""
    oregon = {
        "state": "oregon",
        "code_id": "or_pub_records",
        "code_name": "Oregon Public Records Law (ORS Chapter 192)",
        "source_url": "https://example.com",
        "as_of": "2025-01-01",
        "sections": [
            {
                "section": "192.314",
                "title": "Right to inspect public records",
                "text": "Every person has the right to inspect any public record.",
                "url": "https://example.com/192.314",
            },
            {
                "section": "192.324",
                "title": "Response time",
                "text": "A public body shall respond within five business days.",
                "url": "https://example.com/192.324",
            },
        ],
    }
    washington = {
        "state": "washington",
        "code_id": "wa_pub_records",
        "code_name": "Washington Public Records Act (RCW Chapter 42.56)",
        "source_url": "https://example.com",
        "as_of": "2025-01-01",
        "sections": [
            {
                "section": "42.56.070",
                "title": "Access to public records",
                "text": "Each agency shall make available for public inspection.",
                "url": "https://example.com/42.56.070",
            },
            {
                "section": "42.56.550",
                "title": "Judicial review",
                "text": "Any person denied access may petition superior court.",
                "url": "https://example.com/42.56.550",
            },
        ],
    }
    texas = {
        "state": "texas",
        "code_id": "tx_pub_info",
        "code_name": "Texas Public Information Act (Gov. Code Chapter 552)",
        "source_url": "https://example.com",
        "as_of": "2025-01-01",
        "sections": [
            {
                "section": "552.221",
                "title": "Application for public information; response",
                "text": "Officer shall promptly produce public information within 10 business days.",
                "url": "https://example.com/552.221",
            },
            {
                "section": "552.301",
                "title": "AG opinion process",
                "text": "Governmental body must request AG decision before withholding.",
                "url": "https://example.com/552.301",
            },
        ],
    }

    (tmp_path / "oregon_ors192.json").write_text(json.dumps(oregon), encoding="utf-8")
    (tmp_path / "washington_rcw4256.json").write_text(
        json.dumps(washington), encoding="utf-8"
    )
    (tmp_path / "texas_gc552.json").write_text(json.dumps(texas), encoding="utf-8")
    return tmp_path


@pytest.fixture
def loader(corpus_dir: Path) -> MultiStateCodeLoader:
    ldr = MultiStateCodeLoader(corpus_dir)
    ldr.initialize()
    return ldr


# ===========================================================================
# initialize()
# ===========================================================================


def test_initialize_returns_per_state_counts(loader):
    counts = loader.statistics()
    assert counts["or_pub_records"] == 2
    assert counts["wa_pub_records"] == 2
    assert counts["tx_pub_info"] == 2
    assert counts["total_sections"] == 6


def test_initialize_missing_root_returns_empty():
    ldr = MultiStateCodeLoader("/nonexistent/path/xyz")
    counts = ldr.initialize()
    assert counts == {}


def test_available_states(loader):
    states = loader.available_states()
    assert "oregon" in states
    assert "washington" in states
    assert "texas" in states


def test_section_count_per_state(loader):
    assert loader.section_count("oregon") == 2
    assert loader.section_count("washington") == 2
    assert loader.section_count("texas") == 2
    assert loader.section_count("california") == 0


# ===========================================================================
# resolve_citation() — Oregon
# ===========================================================================


def test_resolve_ors_section(loader):
    result = loader.resolve_citation("ORS 192.314")
    assert result is not None
    assert result.corpus_id == "or_pub_records"
    assert "inspect" in result.text.lower()
    assert result.title == "Right to inspect public records"


def test_resolve_ors_with_section_symbol(loader):
    result = loader.resolve_citation("ORS § 192.324")
    assert result is not None
    assert "five business days" in result.text.lower()


def test_resolve_ors_unknown_section_returns_none(loader):
    assert loader.resolve_citation("ORS 192.999") is None


# ===========================================================================
# resolve_citation() — Washington
# ===========================================================================


def test_resolve_rcw_section(loader):
    result = loader.resolve_citation("RCW 42.56.070")
    assert result is not None
    assert result.corpus_id == "wa_pub_records"
    assert "inspect" in result.text.lower()


def test_resolve_rcw_with_symbol(loader):
    result = loader.resolve_citation("RCW § 42.56.550")
    assert result is not None
    assert "superior court" in result.text.lower()


def test_resolve_rcw_unknown_returns_none(loader):
    assert loader.resolve_citation("RCW 42.56.999") is None


# ===========================================================================
# resolve_citation() — Texas
# ===========================================================================


def test_resolve_tex_gov_code(loader):
    result = loader.resolve_citation("Tex. Gov. Code 552.221")
    assert result is not None
    assert result.corpus_id == "tx_pub_info"
    assert "10 business days" in result.text.lower()


def test_resolve_tex_govt_code_alternate(loader):
    result = loader.resolve_citation("Tex. Gov't Code § 552.301")
    assert result is not None
    assert "AG" in result.text or "attorney general" in result.text.lower()


def test_resolve_tex_unknown_returns_none(loader):
    assert loader.resolve_citation("Tex. Gov. Code 552.999") is None


# ===========================================================================
# resolve_citation() — unrecognized form
# ===========================================================================


def test_unrecognized_citation_returns_none(loader):
    assert loader.resolve_citation("Cal. Gov. Code § 7922.000") is None
    assert loader.resolve_citation("42 U.S.C. § 1983") is None
    assert loader.resolve_citation("random text") is None


# ===========================================================================
# search_text()
# ===========================================================================


def test_search_text_finds_results(loader):
    results = loader.search_text("business days")
    assert len(results) >= 1


def test_search_text_case_insensitive(loader):
    results = loader.search_text("PUBLIC RECORD")
    assert len(results) >= 1


def test_search_text_respects_limit(loader):
    results = loader.search_text("public", limit=2)
    assert len(results) <= 2


def test_search_text_no_match(loader):
    results = loader.search_text("xyzzynotarealword")
    assert results == []


# ===========================================================================
# list_amendments / statistics
# ===========================================================================


def test_list_amendments_returns_empty(loader):
    assert loader.list_amendments("ORS 192.314") == []


def test_statistics_includes_total(loader):
    stats = loader.statistics()
    assert "total_sections" in stats
    assert stats["total_sections"] == 6


# ===========================================================================
# LegalText structure
# ===========================================================================


def test_legaltext_fields(loader):
    result = loader.resolve_citation("ORS 192.314")
    assert result is not None
    assert result.corpus_id == "or_pub_records"
    assert result.citation == "ORS § 192.314"
    assert result.title
    assert result.text
    assert result.url == "https://example.com/192.314"
    assert result.as_of is not None
