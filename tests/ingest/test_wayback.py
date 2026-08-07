"""Tests for ingest.wayback — Wayback Machine availability client."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest

from oraculus_di_auditor.ingest.wayback import (
    WaybackCapture,
    find_capture,
    retrieve_prior_versions,
)

# ---------------------------------------------------------------------------
# WaybackCapture
# ---------------------------------------------------------------------------


class TestWaybackCapture:
    def test_datetime_utc_parsing(self):
        cap = WaybackCapture(
            original_url="https://example.com/tos",
            snapshot_url="https://web.archive.org/web/20240101120000/https://example.com/tos",
            timestamp="20240101120000",
            status_code="200",
        )
        dt = cap.datetime_utc
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 12
        assert dt.tzinfo is UTC

    def test_available_defaults_to_true(self):
        cap = WaybackCapture(
            original_url="https://example.com",
            snapshot_url="https://web.archive.org/web/20230101/https://example.com",
            timestamp="20230101120000",
            status_code="200",
        )
        assert cap.available is True

    def test_frozen_dataclass(self):
        cap = WaybackCapture(
            original_url="https://example.com",
            snapshot_url="https://web.archive.org/web/20230101/https://example.com",
            timestamp="20230101120000",
            status_code="200",
        )
        with pytest.raises((AttributeError, TypeError)):
            cap.original_url = "something else"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# find_capture
# ---------------------------------------------------------------------------


_WAYBACK_RESPONSE_FOUND = {
    "url": "https://example.com/tos",
    "archived_snapshots": {
        "closest": {
            "url": "https://web.archive.org/web/20240101120000/https://example.com/tos",
            "timestamp": "20240101120000",
            "available": True,
            "status": "200",
        }
    },
}

_WAYBACK_RESPONSE_EMPTY = {
    "url": "https://example.com/tos",
    "archived_snapshots": {},
}


class TestFindCapture:
    def _mock_get(self, response_data: dict):
        mock_resp = MagicMock()
        mock_resp.json.return_value = response_data
        mock_resp.raise_for_status = MagicMock()
        return patch(
            "oraculus_di_auditor.ingest.wayback.requests.get",
            return_value=mock_resp,
        )

    def test_returns_capture_when_found(self):
        with self._mock_get(_WAYBACK_RESPONSE_FOUND):
            result = find_capture("https://example.com/tos")
        assert result is not None
        assert result.snapshot_url.startswith("https://web.archive.org/")
        assert result.timestamp == "20240101120000"
        assert result.status_code == "200"

    def test_returns_none_when_not_found(self):
        with self._mock_get(_WAYBACK_RESPONSE_EMPTY):
            result = find_capture("https://example.com/tos")
        assert result is None

    def test_passes_timestamp_from_date(self):
        captured_params = {}

        def fake_get(url, **kwargs):
            captured_params["url"] = url
            mock_resp = MagicMock()
            mock_resp.json.return_value = _WAYBACK_RESPONSE_FOUND
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch(
            "oraculus_di_auditor.ingest.wayback.requests.get", side_effect=fake_get
        ):
            find_capture("https://example.com/tos", target_date=date(2023, 6, 1))

        assert "timestamp=20230601120000" in captured_params["url"]

    def test_passes_timestamp_from_datetime(self):
        captured_params = {}

        def fake_get(url, **kwargs):
            captured_params["url"] = url
            mock_resp = MagicMock()
            mock_resp.json.return_value = _WAYBACK_RESPONSE_FOUND
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch(
            "oraculus_di_auditor.ingest.wayback.requests.get", side_effect=fake_get
        ):
            find_capture(
                "https://example.com/tos",
                target_date=datetime(2023, 6, 1, 14, 30, tzinfo=UTC),
            )

        assert "timestamp=20230601143000" in captured_params["url"]

    def test_no_timestamp_when_target_date_is_none(self):
        captured_params = {}

        def fake_get(url, **kwargs):
            captured_params["url"] = url
            mock_resp = MagicMock()
            mock_resp.json.return_value = _WAYBACK_RESPONSE_FOUND
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch(
            "oraculus_di_auditor.ingest.wayback.requests.get", side_effect=fake_get
        ):
            find_capture("https://example.com/tos", target_date=None)

        assert "timestamp" not in captured_params["url"]

    def test_propagates_request_exception(self):
        import requests

        with patch(
            "oraculus_di_auditor.ingest.wayback.requests.get",
            side_effect=requests.ConnectionError("network down"),
        ):
            with pytest.raises(requests.ConnectionError):
                find_capture("https://example.com/tos")


# ---------------------------------------------------------------------------
# retrieve_prior_versions
# ---------------------------------------------------------------------------


class TestRetrievePriorVersions:
    def _mock_get_always_found(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _WAYBACK_RESPONSE_FOUND
        mock_resp.raise_for_status = MagicMock()
        return patch(
            "oraculus_di_auditor.ingest.wayback.requests.get",
            return_value=mock_resp,
        )

    def _mock_get_never_found(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = _WAYBACK_RESPONSE_EMPTY
        mock_resp.raise_for_status = MagicMock()
        return patch(
            "oraculus_di_auditor.ingest.wayback.requests.get",
            return_value=mock_resp,
        )

    def test_returns_list(self):
        with (
            patch("oraculus_di_auditor.ingest.wayback.time.sleep"),
            self._mock_get_always_found(),
        ):
            results = retrieve_prior_versions("https://example.com/tos", years=3)
        assert isinstance(results, list)

    def test_returns_up_to_n_captures(self):
        with (
            patch("oraculus_di_auditor.ingest.wayback.time.sleep"),
            self._mock_get_always_found(),
        ):
            results = retrieve_prior_versions("https://example.com/tos", years=3)
        assert len(results) <= 3

    def test_empty_when_none_found(self):
        with (
            patch("oraculus_di_auditor.ingest.wayback.time.sleep"),
            self._mock_get_never_found(),
        ):
            results = retrieve_prior_versions("https://example.com/tos", years=3)
        assert results == []

    def test_skips_on_network_error(self):
        import requests as req

        call_count = 0

        def flaky_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise req.ConnectionError("timeout")
            mock_resp = MagicMock()
            mock_resp.json.return_value = _WAYBACK_RESPONSE_FOUND
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with (
            patch(
                "oraculus_di_auditor.ingest.wayback.requests.get", side_effect=flaky_get
            ),
            patch("oraculus_di_auditor.ingest.wayback.time.sleep"),
        ):
            results = retrieve_prior_versions("https://example.com/tos", years=3)
        assert len(results) == 2
