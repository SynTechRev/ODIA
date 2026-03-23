"""Tests for LegistarAdapter using mocked HTTP responses."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oraculus_di_auditor.adapters.legistar_adapter import (
    LegistarAdapter,
    _date_str,
    _sha256_file,
    load_cities,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter():
    return LegistarAdapter("testcity")


SAMPLE_MATTERS = [
    {
        "MatterId": 1,
        "MatterTitle": "Test Contract",
        "MatterTypeName": "Contract",
        "MatterIntroDate": "2024-03-01T00:00:00",
    },
    {
        "MatterId": 2,
        "MatterTitle": "Test Resolution",
        "MatterTypeName": "Resolution",
        "MatterIntroDate": "2024-04-01T00:00:00",
    },
]

SAMPLE_ATTACHMENTS = [
    {
        "MatterAttachmentId": 101,
        "MatterAttachmentName": "Contract.pdf",
        "MatterAttachmentHyperlink": "https://example.com/files/contract.pdf",
    }
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestDateStr:
    def test_none_returns_none(self):
        assert _date_str(None) is None

    def test_string_passthrough(self):
        assert _date_str("2024-01-15") == "2024-01-15"

    def test_date_object(self):
        from datetime import date

        assert _date_str(date(2024, 1, 15)) == "2024-01-15"


class TestSha256File:
    def test_sha256_is_64_chars(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"hello world")
        result = _sha256_file(f)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_sha256_deterministic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"test content")
        assert _sha256_file(f) == _sha256_file(f)


# ---------------------------------------------------------------------------
# LegistarAdapter construction
# ---------------------------------------------------------------------------


class TestLegistarAdapterInit:
    def test_client_id_stored(self, adapter):
        assert adapter.client_id == "testcity"

    def test_client_id_lowercased(self):
        a = LegistarAdapter("TestCity")
        assert a.client_id == "testcity"

    def test_base_url_contains_client_id(self, adapter):
        assert "testcity" in adapter._base


# ---------------------------------------------------------------------------
# list_matters
# ---------------------------------------------------------------------------


class TestListMatters:
    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_MATTERS,
    )
    def test_returns_list(self, mock_get, adapter):
        result = adapter.list_matters()
        assert isinstance(result, list)
        assert len(result) == 2

    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_MATTERS,
    )
    def test_calls_matters_endpoint(self, mock_get, adapter):
        adapter.list_matters()
        url = mock_get.call_args[0][0]
        assert "matters" in url
        assert "testcity" in url

    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_MATTERS,
    )
    def test_date_filter_in_params(self, mock_get, adapter):
        adapter.list_matters(start_date="2024-01-01", end_date="2024-12-31")
        params = mock_get.call_args[1].get("params", {})
        assert "$filter" in params
        assert "2024-01-01" in params["$filter"]
        assert "2024-12-31" in params["$filter"]

    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_MATTERS,
    )
    def test_matter_type_filter(self, mock_get, adapter):
        adapter.list_matters(matter_type="Contract")
        params = mock_get.call_args[1].get("params", {})
        assert "Contract" in params.get("$filter", "")


# ---------------------------------------------------------------------------
# get_matter
# ---------------------------------------------------------------------------


class TestGetMatter:
    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_MATTERS[0],
    )
    def test_returns_dict(self, mock_get, adapter):
        result = adapter.get_matter(1)
        assert isinstance(result, dict)

    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_MATTERS[0],
    )
    def test_endpoint_contains_matter_id(self, mock_get, adapter):
        adapter.get_matter(42)
        url = mock_get.call_args[0][0]
        assert "42" in url


# ---------------------------------------------------------------------------
# get_matter_attachments
# ---------------------------------------------------------------------------


class TestGetMatterAttachments:
    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_ATTACHMENTS,
    )
    def test_returns_list(self, mock_get, adapter):
        result = adapter.get_matter_attachments(1)
        assert isinstance(result, list)

    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=SAMPLE_ATTACHMENTS,
    )
    def test_endpoint_contains_attachments(self, mock_get, adapter):
        adapter.get_matter_attachments(1)
        url = mock_get.call_args[0][0]
        assert "attachments" in url


# ---------------------------------------------------------------------------
# list_events
# ---------------------------------------------------------------------------


class TestListEvents:
    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=[{"EventId": 1, "EventDate": "2024-03-15"}],
    )
    def test_returns_list(self, mock_get, adapter):
        result = adapter.list_events()
        assert isinstance(result, list)

    @patch(
        "oraculus_di_auditor.adapters.legistar_adapter._get",
        return_value=[],
    )
    def test_events_endpoint(self, mock_get, adapter):
        adapter.list_events(start_date="2024-01-01")
        url = mock_get.call_args[0][0]
        assert "events" in url


# ---------------------------------------------------------------------------
# get_event_items
# ---------------------------------------------------------------------------


class TestGetEventItems:
    @patch("oraculus_di_auditor.adapters.legistar_adapter._get", return_value=[])
    def test_returns_list(self, mock_get, adapter):
        result = adapter.get_event_items(1)
        assert isinstance(result, list)

    @patch("oraculus_di_auditor.adapters.legistar_adapter._get", return_value=[])
    def test_endpoint_contains_eventitems(self, mock_get, adapter):
        adapter.get_event_items(99)
        url = mock_get.call_args[0][0]
        assert "eventitems" in url


# ---------------------------------------------------------------------------
# download_attachment
# ---------------------------------------------------------------------------


class TestDownloadAttachment:
    def test_creates_file(self, tmp_path, adapter):
        url = "https://example.com/files/doc.pdf"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_content = lambda chunk_size: [b"PDF content"]
        mock_resp.raise_for_status = lambda: None

        with patch("requests.get", return_value=mock_resp):
            dest = adapter.download_attachment(url, tmp_path)
        assert dest.exists()
        assert dest.read_bytes() == b"PDF content"

    def test_returns_path(self, tmp_path, adapter):
        mock_resp = MagicMock()
        mock_resp.iter_content = lambda chunk_size: [b"data"]
        mock_resp.raise_for_status = lambda: None

        with patch("requests.get", return_value=mock_resp):
            result = adapter.download_attachment(
                "https://example.com/file.txt", tmp_path
            )
        assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# retrieve_corpus
# ---------------------------------------------------------------------------


class TestRetrieveCorpus:
    def test_returns_manifest_dict(self, tmp_path, adapter):
        with (
            patch.object(adapter, "list_matters", return_value=SAMPLE_MATTERS),
            patch.object(
                adapter, "get_matter_attachments", return_value=SAMPLE_ATTACHMENTS
            ),
            patch.object(adapter, "download_attachment") as mock_dl,
        ):
            dest_file = tmp_path / "contract.pdf"
            dest_file.write_bytes(b"PDF")
            mock_dl.return_value = dest_file

            manifest = adapter.retrieve_corpus("2024-01-01", "2024-12-31", tmp_path)

        assert isinstance(manifest, dict)
        assert "matter_count" in manifest
        assert "downloaded_count" in manifest
        assert "files" in manifest

    def test_matter_count_correct(self, tmp_path, adapter):
        with (
            patch.object(adapter, "list_matters", return_value=SAMPLE_MATTERS),
            patch.object(adapter, "get_matter_attachments", return_value=[]),
        ):
            manifest = adapter.retrieve_corpus("2024-01-01", "2024-12-31", tmp_path)

        assert manifest["matter_count"] == 2

    def test_manifest_json_written(self, tmp_path, adapter):
        with (patch.object(adapter, "list_matters", return_value=[]),):
            adapter.retrieve_corpus("2024-01-01", "2024-12-31", tmp_path)

        assert (tmp_path / "retrieval_manifest.json").exists()

    def test_failed_attachment_increments_counter(self, tmp_path, adapter):
        with (
            patch.object(adapter, "list_matters", return_value=SAMPLE_MATTERS[:1]),
            patch.object(
                adapter, "get_matter_attachments", return_value=SAMPLE_ATTACHMENTS
            ),
            patch.object(
                adapter, "download_attachment", side_effect=Exception("network error")
            ),
        ):
            manifest = adapter.retrieve_corpus("2024-01-01", "2024-12-31", tmp_path)

        assert manifest["failed_count"] == 1

    def test_no_matters_zero_downloads(self, tmp_path, adapter):
        with patch.object(adapter, "list_matters", return_value=[]):
            manifest = adapter.retrieve_corpus("2024-01-01", "2024-12-31", tmp_path)
        assert manifest["downloaded_count"] == 0


# ---------------------------------------------------------------------------
# list_available_clients
# ---------------------------------------------------------------------------


class TestListAvailableClients:
    def test_returns_list(self, adapter):
        result = adapter.list_available_clients()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# load_cities
# ---------------------------------------------------------------------------


class TestLoadCities:
    def test_returns_list(self):
        result = load_cities()
        assert isinstance(result, list)

    def test_cities_have_required_fields(self):
        cities = load_cities()
        if cities:
            for city in cities[:5]:
                assert "city" in city
                assert "state" in city
                assert "client_id" in city
