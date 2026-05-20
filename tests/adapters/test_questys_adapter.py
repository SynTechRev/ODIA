"""Unit tests for QuestysAdapter (no live HTTP — uses synthetic fixtures)."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.adapters.questys_adapter import (
    QuestysAdapter,
    QuestysFileMeta,
    _is_login_page,
    _looks_like_real_file,
)

# ---------------------------------------------------------------------------
# Login-page classification — guards the silent-failure mode where the
# webhook flow persisted 26K HTML login pages as if they were real docs.
# ---------------------------------------------------------------------------


def test_is_login_page_catches_small_html_with_login_marker():
    body = (
        b"<!DOCTYPE html><html><head><title>Login - Questys Solutions</title>"
        b"</head><body>Sign in to continue.</body></html>"
    )
    assert _is_login_page("text/html; charset=utf-8", body) is True


def test_is_login_page_rejects_large_html():
    """Above 60KB it's almost certainly a real HTML doc, not a login page."""
    body = b"<!DOCTYPE html><html><body>" + b"A" * 70_000 + b"</body></html>"
    assert _is_login_page("text/html", body) is False


def test_is_login_page_rejects_non_html():
    body = b"%PDF-1.4\n%real PDF bytes"
    assert _is_login_page("application/pdf", body) is False


def test_looks_like_real_file_accepts_pdf():
    assert (
        _looks_like_real_file("application/pdf", b"%PDF-1.4" + b"\x00" * 5000) is True
    )


def test_looks_like_real_file_rejects_tiny_response():
    """14-byte bodies were the Questys throttle signal during BOS bring-up."""
    assert _looks_like_real_file("application/pdf", b"tiny") is False


def test_looks_like_real_file_accepts_real_html_doc():
    """A real HTML document (e.g. Drupal-rendered news release) starts with
    <!doctype html>, so we treat it as real even at the smaller size."""
    body = b"<!DOCTYPE html><html><body>" + b"A" * 5000 + b"</body></html>"
    assert _looks_like_real_file("text/html", body) is True


def test_looks_like_real_file_rejects_html_fragment():
    """A small HTML fragment (no <!doctype>) without the doctype marker
    is the Questys 'no permission' page shape."""
    body = b"<html><body>Unauthorized</body></html>" + b" " * 2000
    assert _looks_like_real_file("text/html", body) is False


# ---------------------------------------------------------------------------
# Search-results parser — the meat of the harvester.
# ---------------------------------------------------------------------------


# fmt: off
# Real Questys results-grid HTML fixture; the JS hrefs are long by design
# (this is what comes back over the wire). Line-length suppressed for the
# fixture only.
# ruff: noqa: E501
_SAMPLE_RESULTS_HTML = """
<html><body>
  <table id="results">
    <tr><th>Name</th><th>Date</th></tr>
    <tr>
      <td><a href='javascript:ShowIframeModal("../File.ashx?id=2824&v=1&isSearch=true", "p", "600px");'>preview</a></td>
      <td><input type="checkbox"></td>
      <td><a href='javascript:ShowIframeModal("../File.ashx?id=2824&v=1&isSearch=true", "p", "600px");'>preview</a></td>
      <td><img src="../Icon.ashx?t=File&x=doc"></td>
      <td>filler</td>
      <td>AGENDA 14 MAR 2006.doc</td>
      <td>3/2/2006</td>
    </tr>
    <tr>
      <td><a href='javascript:ShowIframeModal("../File.ashx?id=2913&v=1&isSearch=true", "p", "600px");'>preview</a></td>
      <td><input type="checkbox"></td>
      <td><a href='javascript:ShowIframeModal("../File.ashx?id=2913&v=1&isSearch=true", "p", "600px");'>preview</a></td>
      <td><img src="../Icon.ashx?t=File&x=pdf"></td>
      <td>filler</td>
      <td>01.05.2021 Minutes.pdf</td>
      <td>1/5/2021</td>
    </tr>
  </table>
</body></html>
"""
# fmt: on


def test_merge_search_results_extracts_id_and_filename():
    pytest.importorskip("bs4")
    catalog: dict[str, QuestysFileMeta] = {}
    QuestysAdapter._merge_search_results(catalog, _SAMPLE_RESULTS_HTML, "agenda")
    assert "2824" in catalog
    assert catalog["2824"].filename == "AGENDA 14 MAR 2006.doc"
    assert catalog["2824"].ext == "doc"
    assert catalog["2824"].found_via == ("agenda",)
    assert "2913" in catalog
    assert catalog["2913"].filename == "01.05.2021 Minutes.pdf"
    assert catalog["2913"].ext == "pdf"


def test_merge_search_results_merges_found_via_terms():
    pytest.importorskip("bs4")
    catalog: dict[str, QuestysFileMeta] = {}
    QuestysAdapter._merge_search_results(catalog, _SAMPLE_RESULTS_HTML, "agenda")
    QuestysAdapter._merge_search_results(catalog, _SAMPLE_RESULTS_HTML, "2006")
    # Same IDs but found via two different terms: found_via must reflect both
    assert "agenda" in catalog["2824"].found_via
    assert "2006" in catalog["2824"].found_via


def test_merge_search_results_handles_empty_html():
    catalog: dict[str, QuestysFileMeta] = {}
    QuestysAdapter._merge_search_results(catalog, "<html></html>", "anything")
    assert catalog == {}


# ---------------------------------------------------------------------------
# Adapter wiring — constructor + URL construction. No network.
# ---------------------------------------------------------------------------


def test_adapter_normalizes_portal_url_trailing_slash():
    a = QuestysAdapter(portal_url="https://example.gov/questys.cmx.webclient")
    assert a.portal_url.endswith("/")
    assert a.search_url.endswith("/Search/Default.aspx")
    assert a.file_url_base.endswith("/File.ashx?id=")


def test_adapter_normalize_is_identity():
    a = QuestysAdapter(portal_url="https://example.gov/questys.cmx.webclient/")
    records = [{"doc_id": "1", "filename": "x.pdf", "ext": "pdf", "found_via": []}]
    assert a.normalize(records) == records
