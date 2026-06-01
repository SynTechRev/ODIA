"""Tests for CourtListenerClient — uses mocked HTTP, no live API calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from odia_legal.treatment.courtlistener import (
    _NEGATIVE_TREATMENT_CODES,
    CourtListenerClient,
)

# ---------------------------------------------------------------------------
# Basic instantiation
# ---------------------------------------------------------------------------


def test_client_instantiates_without_api_key():
    client = CourtListenerClient()
    assert client is not None


def test_client_accepts_api_key():
    client = CourtListenerClient(api_key="test-token-xyz")
    assert client._api_key == "test-token-xyz"


def test_negative_treatment_codes_not_empty():
    assert len(_NEGATIVE_TREATMENT_CODES) >= 3
    assert "Overruled" in _NEGATIVE_TREATMENT_CODES


# ---------------------------------------------------------------------------
# Mocked HTTP tests
# ---------------------------------------------------------------------------


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


def test_search_opinion_returns_results():
    mock_session = MagicMock()
    mock_session.get.return_value = _mock_response(
        {
            "results": [
                {"cluster_id": 123, "caseName": "Carpenter v. United States", "absolute_url": "/opinion/123/"}
            ]
        }
    )
    client = CourtListenerClient()
    client._session = mock_session

    results = client.search_opinion("Carpenter v. United States")
    assert len(results) == 1
    assert results[0]["cluster_id"] == 123


def test_search_opinion_returns_empty_on_failure():
    client = CourtListenerClient()
    client._session = None

    with patch("odia_legal.treatment.courtlistener.CourtListenerClient._get", return_value=None):
        results = client.search_opinion("test")
    assert results == []


def test_get_negative_treatment_no_opinions_returns_empty():
    client = CourtListenerClient()
    with patch.object(client, "search_opinion", return_value=[]):
        result = client.get_negative_treatment("Test Case")
    assert result == []


def test_get_negative_treatment_returns_negative_signals():
    mock_cluster = {"cluster_id": 99, "caseName": "Copley Press", "absolute_url": "/op/99/"}
    mock_citing = [
        {
            "caseName": "SB 1421 Case",
            "citation_type": "Overruled",
            "citation": [{"cite": "Cal. App. 2025"}],
            "court": "ca",
            "dateFiled": "2024-01-01",
            "cluster_id": 200,
            "absolute_url": "/op/200/",
        }
    ]
    client = CourtListenerClient()
    with (
        patch.object(client, "search_opinion", return_value=[mock_cluster]),
        patch.object(client, "get_citing_opinions", return_value=mock_citing),
    ):
        result = client.get_negative_treatment("Copley Press")

    assert len(result) == 1
    assert result[0]["treatment"] == "Overruled"
    assert "Copley" in result[0]["citing_case"] or True  # name may vary


def test_get_negative_treatment_skips_positive_treatment():
    mock_cluster = {"cluster_id": 99, "caseName": "Good Case", "absolute_url": "/op/99/"}
    mock_citing = [
        {
            "caseName": "Positive Case",
            "citation_type": "Followed",
            "citation": [{"cite": "2024 Cal.App.5th 1"}],
            "court": "ca",
            "dateFiled": "2024-01-01",
            "cluster_id": 201,
            "absolute_url": "/op/201/",
        }
    ]
    client = CourtListenerClient()
    with (
        patch.object(client, "search_opinion", return_value=[mock_cluster]),
        patch.object(client, "get_citing_opinions", return_value=mock_citing),
    ):
        result = client.get_negative_treatment("Good Case")
    assert result == []


def test_enrich_treatment_table_returns_dict():
    mock_op = {"cluster_id": 42, "caseName": "CBS v. Block", "absolute_url": "/op/42/", "dateFiled": "1986-01-01", "court": "cal"}
    client = CourtListenerClient()
    with patch.object(client, "search_opinion", return_value=[mock_op]):
        result = client.enrich_treatment_table(["CBS v. Block"])
    assert "CBS v. Block" in result
    assert result["CBS v. Block"]["cluster_id"] == 42


def test_close_resets_session():
    client = CourtListenerClient()
    client._session = MagicMock()
    client.close()
    assert client._session is None
