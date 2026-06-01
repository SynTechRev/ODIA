"""Tests for CaliforniaCodeLoader and LegalCorpus."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from odia_legal.corpus.california_loader import CaliforniaCodeLoader
from odia_legal.corpus.legal_corpus import LegalCorpus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cal_corpus_dir(tmp_path: Path) -> Path:
    """Write minimal cal_gov_code.json for tests."""
    data = {
        "code_id": "cal_gov_code",
        "code_name": "California Government Code",
        "as_of": "2025-01-01",
        "sections": [
            {
                "section": "7923.650",
                "title": "Law enforcement investigative records",
                "text": "A state or local agency may withhold law enforcement records.",
                "url": "https://leginfo.legislature.ca.gov/example",
            },
            {
                "section": "7922.000",
                "title": "Public interest balancing test",
                "text": "The agency shall justify withholding by public interest.",
                "url": None,
            },
            {
                "section": "7920.000",
                "title": "Legislative findings and intent",
                "text": "The Legislature declares...",
                "url": None,
            },
        ],
    }
    (tmp_path / "gov_code.json").write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


@pytest.fixture
def loader(cal_corpus_dir: Path) -> CaliforniaCodeLoader:
    ldr = CaliforniaCodeLoader(submodule_path=cal_corpus_dir)
    ldr.initialize()
    return ldr


# ---------------------------------------------------------------------------
# CaliforniaCodeLoader — initialization
# ---------------------------------------------------------------------------


def test_initialize_returns_counts(cal_corpus_dir: Path):
    ldr = CaliforniaCodeLoader(submodule_path=cal_corpus_dir)
    counts = ldr.initialize()
    assert "cal_gov_code" in counts
    assert counts["cal_gov_code"] == 3


def test_initialize_missing_root_returns_empty(tmp_path: Path):
    ldr = CaliforniaCodeLoader(submodule_path=tmp_path / "nonexistent")
    counts = ldr.initialize()
    assert counts == {}


def test_statistics_after_init(loader: CaliforniaCodeLoader):
    stats = loader.statistics()
    assert stats["total_sections"] == 3
    assert stats.get("cal_gov_code") == 3


# ---------------------------------------------------------------------------
# CaliforniaCodeLoader — resolve_citation
# ---------------------------------------------------------------------------


def test_resolve_new_form_section(loader: CaliforniaCodeLoader):
    result = loader.resolve_citation("Gov. Code § 7923.650")
    assert result is not None
    assert "law enforcement" in result.title.lower()
    assert result.corpus_id == "cal_gov_code"
    assert result.as_of == date(2025, 1, 1)


def test_resolve_old_form_section_via_crosswalk(loader: CaliforniaCodeLoader):
    # § 6254(f) → crosswalk → 7923.650 → resolve
    result = loader.resolve_citation("Gov. Code § 6254(f)")
    assert result is not None
    assert result.title  # title present
    assert "law enforcement" in result.title.lower()


def test_resolve_unknown_section_returns_none(loader: CaliforniaCodeLoader):
    result = loader.resolve_citation("Gov. Code § 9999.999")
    assert result is None


def test_resolve_returns_url_when_present(loader: CaliforniaCodeLoader):
    result = loader.resolve_citation("Gov. Code § 7923.650")
    assert result is not None
    assert result.url is not None
    assert "leginfo" in result.url


def test_resolve_url_none_when_absent(loader: CaliforniaCodeLoader):
    result = loader.resolve_citation("Gov. Code § 7922.000")
    assert result is not None
    assert result.url is None


# ---------------------------------------------------------------------------
# CaliforniaCodeLoader — search_text
# ---------------------------------------------------------------------------


def test_search_finds_matching_section(loader: CaliforniaCodeLoader):
    results = loader.search_text("withhold")
    assert len(results) >= 1
    titles = [r.title for r in results]
    assert any(
        "law enforcement" in t.lower() or "balancing" in t.lower() for t in titles
    )  # noqa: E501


def test_search_returns_empty_for_no_match(loader: CaliforniaCodeLoader):
    results = loader.search_text("zzz-no-match-xyz")
    assert results == []


def test_search_respects_limit(loader: CaliforniaCodeLoader):
    results = loader.search_text("a", limit=1)
    assert len(results) <= 1


def test_list_amendments_returns_empty(loader: CaliforniaCodeLoader):
    assert loader.list_amendments("Gov. Code § 7923.650") == []


# ---------------------------------------------------------------------------
# LegalCorpus — with explicit Cal. loader
# ---------------------------------------------------------------------------


def test_legal_corpus_initializes_with_explicit_loaders(cal_corpus_dir: Path):
    ldr = CaliforniaCodeLoader(submodule_path=cal_corpus_dir)
    corpus = LegalCorpus(loaders=[ldr])
    stats = corpus.initialize()
    assert "cal_codes" in stats


def test_legal_corpus_resolve_delegates_to_loader(cal_corpus_dir: Path):
    ldr = CaliforniaCodeLoader(submodule_path=cal_corpus_dir)
    corpus = LegalCorpus(loaders=[ldr])
    corpus.initialize()

    result = corpus.resolve("Gov. Code § 7923.650")
    assert result is not None
    assert "law enforcement" in result.title.lower()


def test_legal_corpus_resolve_returns_none_if_not_found(cal_corpus_dir: Path):
    ldr = CaliforniaCodeLoader(submodule_path=cal_corpus_dir)
    corpus = LegalCorpus(loaders=[ldr])
    corpus.initialize()

    assert corpus.resolve("Gov. Code § 9999.001") is None


def test_legal_corpus_search(cal_corpus_dir: Path):
    ldr = CaliforniaCodeLoader(submodule_path=cal_corpus_dir)
    corpus = LegalCorpus(loaders=[ldr])
    corpus.initialize()

    results = corpus.search("legislative")
    assert any("legislative" in r.title.lower() for r in results)


def test_legal_corpus_empty_loaders():
    corpus = LegalCorpus(loaders=[])
    corpus.initialize()
    assert corpus.is_empty()


def test_legal_corpus_statistics(cal_corpus_dir: Path):
    ldr = CaliforniaCodeLoader(submodule_path=cal_corpus_dir)
    corpus = LegalCorpus(loaders=[ldr])
    corpus.initialize()
    stats = corpus.statistics()
    assert "cal_codes" in stats
    assert stats["cal_codes"]["total_sections"] == 3
