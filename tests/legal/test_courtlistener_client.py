"""Tests for CourtListenerClient — all offline (no real HTTP calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from oraculus_di_auditor.legal.courtlistener_client import CourtListenerClient


class _FakeResponse:
    def __init__(self, status_code: int = 200, data: dict | None = None):
        self.status_code = status_code
        self._data = data or {}
        self.headers = {}

    def json(self):
        return self._data


class TestCourtListenerClientInit:
    def test_no_api_key(self, monkeypatch):
        monkeypatch.delenv("COURTLISTENER_API_KEY", raising=False)
        cl = CourtListenerClient()
        assert cl._api_key is None

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("COURTLISTENER_API_KEY", "testkey123")
        cl = CourtListenerClient()
        assert cl._api_key == "testkey123"

    def test_explicit_api_key(self, monkeypatch):
        monkeypatch.delenv("COURTLISTENER_API_KEY", raising=False)
        cl = CourtListenerClient(api_key="mykey")
        assert cl._api_key == "mykey"

    def test_empty_env_var_treated_as_none(self, monkeypatch):
        monkeypatch.setenv("COURTLISTENER_API_KEY", "")
        cl = CourtListenerClient()
        assert cl._api_key is None


class TestCourtListenerClientGet:
    def _make_session(self, status_code=200, data=None):
        mock_sess = MagicMock()
        mock_resp = _FakeResponse(status_code=status_code, data=data or {})
        mock_sess.get.return_value = mock_resp
        return mock_sess

    def test_get_success(self):
        cl = CourtListenerClient()
        cl._session = self._make_session(200, {"results": [], "count": 0})
        result = cl._get("/search/", {"q": "test"})
        assert result is not None
        assert "results" in result

    def test_get_404_returns_none(self):
        cl = CourtListenerClient()
        cl._session = self._make_session(404)
        result = cl._get("/opinions/99999/")
        assert result is None

    def test_get_rate_limited_retries(self):
        cl = CourtListenerClient(max_retries=2)
        mock_sess = MagicMock()
        rate_limit_resp = _FakeResponse(429)
        rate_limit_resp.headers = {"Retry-After": "0"}
        ok_resp = _FakeResponse(200, {"id": 1})
        mock_sess.get.side_effect = [rate_limit_resp, ok_resp]
        cl._session = mock_sess
        with patch("oraculus_di_auditor.legal.courtlistener_client.time") as mock_time:
            mock_time.sleep = MagicMock()
            result = cl._get("/opinions/1/")
        assert result == {"id": 1}

    def test_get_network_error_retries(self):
        cl = CourtListenerClient(max_retries=2)
        mock_sess = MagicMock()
        mock_sess.get.side_effect = [
            OSError("network"),
            _FakeResponse(200, {"ok": True}),
        ]
        cl._session = mock_sess
        with patch("oraculus_di_auditor.legal.courtlistener_client.time") as mock_time:
            mock_time.sleep = MagicMock()
            result = cl._get("/clusters/1/")
        assert result == {"ok": True}


class TestSearchOpinions:
    def test_search_returns_results(self):
        cl = CourtListenerClient()
        cl._session = MagicMock()
        cl._session.get.return_value = _FakeResponse(
            200,
            {
                "results": [
                    {"id": 1, "cluster_id": 100, "case_name": "Test v. State"},
                    {"id": 2, "cluster_id": 101, "case_name": "Other v. County"},
                ],
                "count": 2,
                "next": None,
            },
        )
        results = cl.search_opinions("CPRA exemption", max_results=10)
        assert len(results) == 2
        assert results[0]["case_name"] == "Test v. State"

    def test_search_with_courts_filter(self):
        cl = CourtListenerClient()
        mock_sess = MagicMock()
        mock_sess.get.return_value = _FakeResponse(
            200, {"results": [], "count": 0, "next": None}
        )
        cl._session = mock_sess
        cl.search_opinions("test", courts=["cal", "ca9"])
        call_kwargs = mock_sess.get.call_args
        assert call_kwargs is not None
        params = call_kwargs[1].get("params") or call_kwargs[0][1]
        assert "court" in params
        assert "cal" in params["court"]

    def test_search_empty_results(self):
        cl = CourtListenerClient()
        cl._session = MagicMock()
        cl._session.get.return_value = _FakeResponse(
            200, {"results": [], "count": 0, "next": None}
        )
        results = cl.search_opinions("no results query", max_results=5)
        assert results == []


class TestGetCluster:
    def test_get_cluster_success(self):
        cl = CourtListenerClient()
        cl._session = MagicMock()
        cl._session.get.return_value = _FakeResponse(
            200,
            {
                "id": 42,
                "case_name": "People v. Test",
                "date_filed": "2020-03-15",
                "citations": [{"cite": "123 Cal.App.5th 456"}],
                "court_id": "cal",
            },
        )
        cluster = cl.get_cluster(42)
        assert cluster is not None
        assert cluster["case_name"] == "People v. Test"

    def test_get_cluster_missing(self):
        cl = CourtListenerClient()
        cl._session = MagicMock()
        cl._session.get.return_value = _FakeResponse(404)
        cluster = cl.get_cluster(99999)
        assert cluster is None


class TestPing:
    def test_ping_success(self):
        cl = CourtListenerClient()
        cl._session = MagicMock()
        cl._session.get.return_value = _FakeResponse(200, {})
        assert cl.ping() is True

    def test_ping_failure(self):
        cl = CourtListenerClient()
        cl._session = MagicMock()
        cl._session.get.return_value = _FakeResponse(503)
        assert cl.ping() is False
