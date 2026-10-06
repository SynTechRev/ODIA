"""Tests for CPRACorpusLoader — embedded CCPA/CPRA statutory corpus."""

from __future__ import annotations

import pytest
from oraculus_di_auditor.legal.cpra_corpus import CPRACorpusLoader


@pytest.fixture(scope="module")
def loader() -> CPRACorpusLoader:
    l = CPRACorpusLoader()
    l.initialize()
    return l


class TestInitialization:
    def test_stats_after_init(self, loader):
        stats = loader.statistics()
        assert stats["provisions"] >= 13
        assert stats["anchors_mapped"] >= 13

    def test_auto_init_on_resolve(self):
        l = CPRACorpusLoader()
        result = l.resolve_citation("CCPA_121")
        assert result is not None


class TestResolveByAnchorId:
    def test_ccpa_121_by_anchor(self, loader):
        result = loader.resolve_anchor("CCPA_121")
        assert result is not None
        assert "sensitive" in result.text.lower()
        assert "1798.121" in result.citation
        assert result.corpus_id == "cpra"
        assert result.url is not None

    def test_ccp_1281_97_by_anchor(self, loader):
        result = loader.resolve_anchor("CCP_1281_97")
        assert result is not None
        assert "30 days" in result.text

    def test_cal_labor_2699_by_anchor(self, loader):
        result = loader.resolve_anchor("CAL_LABOR_2699")
        assert result is not None
        assert (
            "civil penalty" in result.text.lower() or "aggrieved" in result.text.lower()
        )

    def test_ab_51_by_anchor(self, loader):
        result = loader.resolve_anchor("AB_51")
        assert result is not None
        assert "arbitration" in result.text.lower() or "waive" in result.text.lower()

    def test_unknown_anchor_returns_none(self, loader):
        assert loader.resolve_anchor("FAKE_ANCHOR_XYZ") is None


class TestResolveBySection:
    def test_resolve_by_section_number(self, loader):
        result = loader.resolve_citation("1798.100")
        assert result is not None
        assert "personal information" in result.text.lower()

    def test_resolve_by_formal_citation(self, loader):
        result = loader.resolve_citation("Cal. Civ. Code § 1798.121")
        assert result is not None
        assert "sensitive" in result.text.lower()

    def test_resolve_ccp_section(self, loader):
        result = loader.resolve_citation("CCP § 1281.97")
        assert result is not None
        assert "30 days" in result.text

    def test_resolve_ccpa_121_shorthand(self, loader):
        result = loader.resolve_citation("CCPA_121")
        assert result is not None

    def test_all_anchors_resolve(self, loader):
        from oraculus_di_auditor.legal.cpra_corpus import _ANCHOR_TO_SECTION

        for anchor_id in _ANCHOR_TO_SECTION:
            result = loader.resolve_anchor(anchor_id)
            assert result is not None, f"Anchor {anchor_id!r} did not resolve"


class TestLegalTextFields:
    def test_legal_text_as_of_date(self, loader):
        from datetime import date

        result = loader.resolve_citation("1798.121")
        assert result.as_of == date(2023, 1, 1)

    def test_legal_text_source_path(self, loader):
        result = loader.resolve_citation("1798.121")
        assert "cpra_corpus.py" in result.source_path

    def test_legal_text_url_is_leginfo(self, loader):
        result = loader.resolve_citation("1798.121")
        assert "leginfo.legislature.ca.gov" in (result.url or "")

    def test_no_amendment_history(self, loader):
        amendments = loader.list_amendments("1798.121")
        assert amendments == []


class TestSearch:
    def test_search_returns_matches(self, loader):
        results = loader.search_text("biometric", limit=5)
        assert len(results) >= 1
        assert any("biometric" in r.text.lower() for r in results)

    def test_search_limit_respected(self, loader):
        results = loader.search_text("personal information", limit=2)
        assert len(results) <= 2

    def test_search_no_match(self, loader):
        results = loader.search_text("zzz_no_match_xyzzy_99")
        assert results == []
