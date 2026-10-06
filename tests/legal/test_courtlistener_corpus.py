"""Tests for CourtListenerCorpusLoader — all offline (no real HTTP calls)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from oraculus_di_auditor.legal.case_law_builder import CaseLawRecord
from oraculus_di_auditor.legal.courtlistener_client import CourtListenerClient
from oraculus_di_auditor.legal.courtlistener_corpus import (
    ODIA_HARVEST_QUERIES,
    CourtListenerCorpusLoader,
    _cluster_to_case_record,
)

# ---- helpers ----


def _make_cluster(
    cluster_id: int = 1,
    case_name: str = "Test v. Agency",
    date_filed: str = "2021-06-01",
    court_id: str = "cal",
    cite: str = "50 Cal.5th 100",
) -> dict:
    return {
        "id": cluster_id,
        "case_name": case_name,
        "date_filed": date_filed,
        "court_id": court_id,
        "citations": [{"cite": cite}],
        "citation_string": cite,
        "sub_opinions": [{"id": 999}],
    }


def _make_opinion(text: str = "The court held that...") -> dict:
    return {"id": 999, "plain_text": text}


def _loader_with_tmp_dir(client=None) -> tuple[CourtListenerCorpusLoader, Path]:
    tmp = tempfile.mkdtemp()
    cases_dir = Path(tmp) / "cases"
    cases_dir.mkdir()
    cl = client or MagicMock(spec=CourtListenerClient)
    return CourtListenerCorpusLoader(cases_dir=cases_dir, client=cl), cases_dir


# ---- _cluster_to_case_record ----


class TestClusterToCaseRecord:
    def test_basic_conversion(self):
        cluster = _make_cluster()
        record = _cluster_to_case_record(cluster, topic="cpra")
        assert record is not None
        assert record.case_id == "cl_1"
        assert record.name == "Test v. Agency"
        assert record.citation == "50 Cal.5th 100"
        assert record.year == 2021
        assert record.court == "California Supreme Court"
        assert record.doctrine == "cpra"

    def test_with_opinion_text(self):
        cluster = _make_cluster()
        opinion = _make_opinion("The statute requires disclosure within 10 days.")
        record = _cluster_to_case_record(cluster, opinion, topic="cpra")
        assert record is not None
        assert "disclosure" in record.summary

    def test_missing_case_name_returns_none(self):
        cluster = _make_cluster()
        cluster["case_name"] = ""
        record = _cluster_to_case_record(cluster)
        assert record is None

    def test_missing_cluster_id_returns_none(self):
        cluster = _make_cluster()
        del cluster["id"]
        record = _cluster_to_case_record(cluster)
        assert record is None

    def test_year_extraction(self):
        cluster = _make_cluster(date_filed="2019-01-15")
        record = _cluster_to_case_record(cluster)
        assert record is not None
        assert record.year == 2019

    def test_court_mapping_ninth_circuit(self):
        cluster = _make_cluster(court_id="ca9")
        record = _cluster_to_case_record(cluster)
        assert record is not None
        assert record.court == "9th Circuit"

    def test_court_mapping_scotus(self):
        cluster = _make_cluster(court_id="scotus")
        record = _cluster_to_case_record(cluster)
        assert record is not None
        assert record.court == "SCOTUS"

    def test_source_url_contains_cluster_id(self):
        cluster = _make_cluster(cluster_id=42)
        record = _cluster_to_case_record(cluster)
        assert record is not None
        assert "42" in record.source_url


# ---- CourtListenerCorpusLoader ----


class TestCorpusLoaderInitialize:
    def test_empty_corpus(self):
        loader, _ = _loader_with_tmp_dir()
        stats = loader.initialize()
        assert stats["cases_loaded"] == 0

    def test_with_existing_cases(self):
        loader, cases_dir = _loader_with_tmp_dir()
        record = _cluster_to_case_record(_make_cluster(cluster_id=1), topic="cpra")
        loader._builder.save_case(record)
        loader._invalidate_cache()
        stats = loader.initialize()
        assert stats["cases_loaded"] == 1


class TestCorpusLoaderResolve:
    def test_resolve_exact_citation_match(self):
        loader, _ = _loader_with_tmp_dir()
        record = _cluster_to_case_record(
            _make_cluster(cluster_id=5, cite="55 Cal.5th 200"), topic="cpra"
        )
        loader._builder.save_case(record)
        loader._invalidate_cache()
        result = loader.resolve_citation("55 Cal.5th 200")
        assert result is not None
        assert result.citation == "55 Cal.5th 200"

    def test_resolve_case_name_fragment(self):
        loader, _ = _loader_with_tmp_dir()
        record = _cluster_to_case_record(
            _make_cluster(cluster_id=6, case_name="Smith v. City of Tulare"),
            topic="cpra",
        )
        loader._builder.save_case(record)
        loader._invalidate_cache()
        result = loader.resolve_citation("Smith v. City of Tulare")
        assert result is not None

    def test_resolve_falls_back_to_api(self):
        mock_client = MagicMock(spec=CourtListenerClient)
        cluster = _make_cluster(cluster_id=7, case_name="API Result Case")
        mock_client.search_opinions.return_value = [{"id": 7, "cluster_id": 7}]
        mock_client.get_cluster.return_value = cluster
        mock_client.get_opinion.return_value = None

        loader, _ = _loader_with_tmp_dir(client=mock_client)
        result = loader.resolve_citation("API Result Case")
        assert result is not None
        mock_client.search_opinions.assert_called_once()

    def test_resolve_returns_none_on_miss(self):
        mock_client = MagicMock(spec=CourtListenerClient)
        mock_client.search_opinions.return_value = []
        loader, _ = _loader_with_tmp_dir(client=mock_client)
        result = loader.resolve_citation("Totally Unknown Citation v. Nobody")
        assert result is None


class TestCorpusLoaderSearch:
    def test_search_local_only(self):
        loader, _ = _loader_with_tmp_dir()
        record = _cluster_to_case_record(
            _make_cluster(cluster_id=10, case_name="CPRA Exemption Case"), topic="cpra"
        )
        record = CaseLawRecord.model_validate(
            {
                **record.model_dump(),
                "summary": "This case concerns CPRA exemption for law enforcement",
            }
        )
        loader._builder.save_case(record)
        loader._invalidate_cache()

        mock_client = MagicMock(spec=CourtListenerClient)
        mock_client.search_opinions.return_value = []
        loader._client = mock_client

        results = loader.search_text("CPRA exemption", limit=5)
        assert len(results) >= 1

    def test_search_hits_api_when_local_empty(self):
        mock_client = MagicMock(spec=CourtListenerClient)
        cluster = _make_cluster(cluster_id=99, case_name="API Case")
        mock_client.search_opinions.return_value = [{"cluster_id": 99}]
        mock_client.get_cluster.return_value = cluster
        mock_client.get_opinion.return_value = None

        loader, _ = _loader_with_tmp_dir(client=mock_client)
        results = loader.search_text("CPRA", limit=3)
        mock_client.search_opinions.assert_called_once()


class TestCorpusLoaderStatistics:
    def test_empty_statistics(self):
        loader, _ = _loader_with_tmp_dir()
        stats = loader.statistics()
        assert stats["total_cases"] == 0
        assert stats["with_citations"] == 0

    def test_statistics_with_cases(self):
        loader, _ = _loader_with_tmp_dir()
        for i in range(3):
            record = _cluster_to_case_record(
                _make_cluster(cluster_id=i + 1), topic="cpra"
            )
            loader._builder.save_case(record)
        loader._invalidate_cache()
        stats = loader.statistics()
        assert stats["total_cases"] == 3
        assert stats["with_citations"] == 3


class TestCorpusLoaderHarvest:
    def test_harvest_saves_new_cases(self):
        mock_client = MagicMock(spec=CourtListenerClient)
        cluster = _make_cluster(cluster_id=200, case_name="Harvest Case")
        mock_client.search_opinions.return_value = [{"cluster_id": 200}]
        mock_client.get_cluster.return_value = cluster
        mock_client.get_opinion.return_value = None

        loader, cases_dir = _loader_with_tmp_dir(client=mock_client)
        queries = [{"query": "test", "topic": "cpra", "max_results": 5}]
        stats = loader.harvest(queries=queries)

        assert stats["new_cases"] == 1
        assert stats["errors"] == 0
        saved = list(cases_dir.glob("*.json"))
        assert len(saved) == 1

    def test_harvest_skips_existing(self):
        mock_client = MagicMock(spec=CourtListenerClient)
        cluster = _make_cluster(cluster_id=201)
        mock_client.search_opinions.return_value = [{"cluster_id": 201}]
        mock_client.get_cluster.return_value = cluster
        mock_client.get_opinion.return_value = None

        loader, _ = _loader_with_tmp_dir(client=mock_client)
        queries = [{"query": "test", "topic": "cpra", "max_results": 5}]
        loader.harvest(queries=queries)
        loader._invalidate_cache()
        mock_client.get_cluster.reset_mock()

        stats2 = loader.harvest(queries=queries, skip_existing=True)
        assert stats2["new_cases"] == 0
        assert stats2["skipped"] == 1
        mock_client.get_cluster.assert_not_called()

    def test_harvest_handles_api_error(self):
        mock_client = MagicMock(spec=CourtListenerClient)
        mock_client.search_opinions.side_effect = OSError("network down")
        loader, _ = _loader_with_tmp_dir(client=mock_client)
        queries = [{"query": "test", "topic": "cpra", "max_results": 5}]
        stats = loader.harvest(queries=queries)
        assert stats["errors"] == 1
        assert stats["new_cases"] == 0


class TestOdiaHarvestQueries:
    def test_all_queries_have_required_fields(self):
        for q in ODIA_HARVEST_QUERIES:
            assert "query" in q, f"Missing 'query' in {q}"
            assert "topic" in q, f"Missing 'topic' in {q}"
            assert "max_results" in q, f"Missing 'max_results' in {q}"
            assert isinstance(q["max_results"], int)
            assert q["max_results"] > 0

    def test_topics_are_nonempty_strings(self):
        for q in ODIA_HARVEST_QUERIES:
            assert isinstance(q["topic"], str)
            assert len(q["topic"]) > 0

    def test_expected_topics_present(self):
        topics = {q["topic"] for q in ODIA_HARVEST_QUERIES}
        for expected in ["cpra", "surveillance", "probation", "federal_grants"]:
            assert expected in topics, f"Expected topic {expected!r} missing"
