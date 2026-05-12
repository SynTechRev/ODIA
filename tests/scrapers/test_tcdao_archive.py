"""Tests for the v1 TCDAO press-release archive scraper.

These tests exercise pure parsing functions against inline HTML
fixtures captured from the WordPress theme tulareda.org runs. No
network calls happen here -- the C2 track adds full HTTP-mocking
tests later; this commit only covers the parser correctness gate.

bs4 (beautifulsoup4) is required. When it's not installed the
fixture-driven tests skip rather than fail so the rest of the
analysis test suite still runs cleanly on minimal dev installs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

bs4 = pytest.importorskip(
    "bs4"
)  # noqa: F841  -- used transitively by the module under test

from oraculus_di_auditor.scrapers.tcdao_archive import (  # noqa: E402
    BASE_URL,
    PressRelease,
    ScrapeManifest,
    _find_next_archive_page,
    _now_iso,
    _parse_archive_page,
    _parse_press_release,
    write_release,
)

# ---------------------------------------------------------------------------
# Fixtures -- inline HTML snippets matching the WordPress theme.
# ---------------------------------------------------------------------------

ARCHIVE_PAGE_HTML = """<!DOCTYPE html>
<html><body>
  <article id="post-101">
    <h2><a href="/2026/04/ab-481-april-public-meeting/">AB 481 April Meeting</a></h2>
    <p>The Tulare County District Attorney announces...</p>
    <a class="read-more" href="/2026/04/ab-481-april-public-meeting/">Read more</a>
  </article>
  <article id="post-102">
    <h2><a href="/2026/03/grant-award-2026/">DUI Vertical Prosecution Grant</a></h2>
    <p>A $250,000 award...</p>
  </article>
  <article id="post-103">
    <h2>
      <a href="/2026/02/bureau-investigations-update/"
        >Bureau of Investigations Update</a>
    </h2>
  </article>
  <nav class="pagination">
    <a class="next page-numbers"
       href="/category/press-releases/2026-press-releases/page/2/">Next</a>
  </nav>
</body></html>
"""

PRESS_RELEASE_HTML = """<!DOCTYPE html>
<html><body>
  <article>
    <h1 class="entry-title">AB 481 Annual Military Equipment Report Public Meeting</h1>
    <time class="entry-date" datetime="2026-03-15T10:00:00-07:00">March 15, 2026</time>
    <div class="entry-content">
      <p>On March 15, 2026, the Tulare County District Attorney's Office
      announces a public meeting on April 7, 2026 to discuss the AB 481
      Annual Military Equipment Report.</p>
      <p>Per Ordinance 3611, the Bureau of Investigations is required to
      provide annual reporting on military equipment use.</p>
      <a href="/related/ab481-ordinance-3611/">Read Ordinance 3611</a>
      <img src="/images/ab481-meeting-banner.jpg" alt="banner"/>
    </div>
  </article>
</body></html>
"""

# A press release where neither <time> nor entry-date selectors are present,
# forcing the fallback narrative-date regex to fire.
PRESS_RELEASE_HTML_NO_DATE_TAG = """<!DOCTYPE html>
<html><body>
  <article>
    <h1 class="entry-title">Vendor Update</h1>
    <div class="entry-content">
      <p>On January 5, 2024, the Office issued the following update
      regarding evidence management.</p>
    </div>
  </article>
</body></html>
"""


# ---------------------------------------------------------------------------
# Archive-page parser
# ---------------------------------------------------------------------------


def test_parse_archive_page_extracts_three_urls() -> None:
    urls = _parse_archive_page(ARCHIVE_PAGE_HTML, BASE_URL)
    assert len(urls) == 3
    assert all(u.startswith(BASE_URL + "/2026/") for u in urls)
    assert urls[0].endswith("ab-481-april-public-meeting/")


def test_parse_archive_page_handles_empty_html() -> None:
    assert _parse_archive_page("<html></html>", BASE_URL) == []


def test_parse_archive_page_deduplicates() -> None:
    duplicated = ARCHIVE_PAGE_HTML.replace(
        '<article id="post-103">',
        '<article id="post-101-dup">'
        '<h2><a href="/2026/04/ab-481-april-public-meeting/">AB 481 Dup</a></h2>'
        '</article><article id="post-103">',
    )
    urls = _parse_archive_page(duplicated, BASE_URL)
    # Even with the extra duplicate, only the unique 3 should come back.
    assert len(urls) == 3


def test_find_next_archive_page_returns_pagination_link() -> None:
    nxt = _find_next_archive_page(ARCHIVE_PAGE_HTML, BASE_URL)
    assert nxt is not None
    assert nxt.endswith("/page/2/")


def test_find_next_archive_page_none_when_no_pagination() -> None:
    html = "<html><body><article></article></body></html>"
    assert _find_next_archive_page(html, BASE_URL) is None


# ---------------------------------------------------------------------------
# Press-release parser
# ---------------------------------------------------------------------------


def test_parse_press_release_extracts_title_date_body() -> None:
    url = f"{BASE_URL}/2026/03/ab-481-april-2026-public-meeting/"
    release = _parse_press_release(PRESS_RELEASE_HTML, url, 2026)
    assert release is not None
    assert release.title.startswith("AB 481")
    # Machine-readable datetime attribute on <time>
    assert release.publish_date.startswith("2026-03-15")
    assert "AB 481" in release.body_text
    assert "Ordinance 3611" in release.body_text
    assert "Bureau of Investigations" in release.body_text
    assert release.url == url
    assert release.year == 2026
    assert release.word_count > 30
    # SHA256 is hex, length 64
    assert len(release.sha256) == 64
    assert all(c in "0123456789abcdef" for c in release.sha256)
    # Inbound link captured
    assert any("ordinance-3611" in link.lower() for link in release.inbound_links)
    # Embedded image captured
    assert any("banner" in img for img in release.embedded_images)


def test_parse_press_release_falls_back_to_narrative_date() -> None:
    release = _parse_press_release(
        PRESS_RELEASE_HTML_NO_DATE_TAG, f"{BASE_URL}/2024/01/vendor-update/", 2024
    )
    assert release is not None
    # The fallback regex should parse "On January 5, 2024," to 2024-01-05.
    assert release.publish_date == "2024-01-05"


def test_parse_press_release_returns_none_when_no_article_body() -> None:
    html = "<html><body><h1>Bare page, no article</h1></body></html>"
    release = _parse_press_release(html, f"{BASE_URL}/orphan/", 2026)
    assert release is None


# ---------------------------------------------------------------------------
# write_release
# ---------------------------------------------------------------------------


def test_write_release_creates_year_subdir_and_file(tmp_path: Path) -> None:
    release = PressRelease(
        url=f"{BASE_URL}/2026/03/test-slug/",
        year=2026,
        title="Test",
        publish_date="2026-03-15",
        body_text="Some content here.",
        word_count=3,
        sha256="a" * 64,
        scraped_at=_now_iso(),
    )
    out = write_release(release, tmp_path)
    assert out.exists()
    assert out.parent.name == "2026"
    assert "test-slug" in out.name
    assert "2026-03-15" in out.name
    contents = out.read_text(encoding="utf-8")
    assert "Title: Test" in contents
    assert "Some content here." in contents


# ---------------------------------------------------------------------------
# Timestamp helper -- verifies the CLAUDE.md "no datetime.utcnow()" rule.
# ---------------------------------------------------------------------------


def test_now_iso_returns_timezone_aware_string() -> None:
    iso = _now_iso()
    # datetime.now(UTC).isoformat() produces e.g. "2026-05-12T17:00:00+00:00",
    # not the naive "2026-05-12T17:00:00" that utcnow() would produce.
    assert "+00:00" in iso or iso.endswith("Z")


# ---------------------------------------------------------------------------
# Manifest dataclass shape (sanity check for downstream JSON round-trips).
# ---------------------------------------------------------------------------


def test_scrape_manifest_serialises_round_trip() -> None:
    manifest = ScrapeManifest(started_at=_now_iso())
    manifest.releases_scraped = 5
    manifest.releases_skipped_dedup = 2
    manifest.years_scraped = [2025, 2026]
    from dataclasses import asdict

    serialised = json.dumps(asdict(manifest))
    back = json.loads(serialised)
    assert back["releases_scraped"] == 5
    assert back["releases_skipped_dedup"] == 2
    assert back["years_scraped"] == [2025, 2026]
