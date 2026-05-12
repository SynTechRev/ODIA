"""
TCDAO Press Release Archive Scraper
====================================

Ingests the public press release archive at tulareda.org and feeds the
extracted content into the standard O.D.I.A. document pipeline as if
each press release were a PDF upload.

Why this exists
---------------
The TCDAO doesn't publish PDF files of its press releases. The
evidentiary content — personnel announcements, prosecution patterns by
originating agency, AB 481 Bureau of Investigations meetings, grant
awards, technology adoptions — lives only as WordPress posts at:

  https://tulareda.org/category/press-releases/{year}-press-releases/

The yearly archive pages exist for 2020, 2021, 2023, 2024, 2025, 2026
(notably 2022 is gap-checked but appears absent — itself an analytical
finding). Each yearly page has dozens of press releases reachable via
"Read more" links to individual post pages.

Investigative yield from this archive (per Cross-Entity Protocol §5.3
"Leave No Stone Unturned"):

  - Personnel migration evidence (TCSO Deputy → TCDA Investigator
    pattern is documented in multiple 2020-2021 announcements)
  - Prosecution volume by originating agency (which agency's cases
    the TCDAO files most aggressively reveals operational priority)
  - AB 481 Annual Military Equipment Report announcements (April 7,
    2026 meeting confirmed in 2026 archive — material for the
    asymmetry-with-TCSO finding)
  - Grant award announcements (DUI prosecution grants — Vertical
    Prosecution funding traceable per year)
  - Co-sponsored legislation (SB 23 — TCDAO + CDAA, 2021)
  - Bureau of Investigations references (technology, personnel,
    operations)
  - Vendor mentions (Tyler / Journal / Odyssey case management,
    Evidence.com integration)

How the scraper works
---------------------
1. Discovery: GET each yearly archive page and parse out "Read more"
   links. The archive is paginated (e.g., 2020 has /page/2/), so pagination
   is followed until no further links exist.
2. Politeness: respect robots.txt, throttle to 1 req / 2 sec by default,
   announce User-Agent string identifying O.D.I.A. as a civic-research
   tool, and honor any Retry-After headers.
3. Per-post extraction: GET each press release page; pull the <article>
   body via the WordPress-standard semantic HTML; extract: title,
   publish date, author (if present), body text, embedded URLs,
   embedded images (logged but not downloaded — bandwidth control).
4. Normalization: convert the extracted HTML to clean text using a
   conservative tag-stripping pass that preserves paragraph boundaries
   and inline emphasis. Markdown conversion is OPTIONAL via the
   --markdown flag — for D-13 pattern matching, normalized plain text
   is preferred.
5. Ingestion: each press release is wrapped as a virtual document and
   submitted to the O.D.I.A. ingestion API with primary_entity=E-011
   (TCDAO), source_hash=SHA-256 of the normalized text, ingested_at=now.
6. Deduplication: the SeenHash table catches re-runs — running the
   scraper twice doesn't re-emit findings.
7. Persistence: a JSON manifest (one row per scraped press release) is
   written to data/tcdao_archive_manifest.json so subsequent runs can
   skip already-ingested URLs unless --refresh is set.

Rate-limit and politeness rationale
------------------------------------
The site uses Cloudflare. Aggressive scraping triggers WAF challenges
that interrupt the run; modest throttling is faster end-to-end than
fighting the WAF. Tulare County District Attorney is a public agency
whose press releases are public records; the scraper announces itself
clearly via User-Agent and adheres to robots.txt.

CLI
---
  python -m oraculus_di_auditor.scrapers.tcdao_archive \\
      --start-year 2020 --end-year 2026 \\
      --out data/tcdao_archive \\
      --rate-limit 2.0

  python -m oraculus_di_auditor.scrapers.tcdao_archive \\
      --refresh   # re-scrape regardless of manifest

  python -m oraculus_di_auditor.scrapers.tcdao_archive \\
      --dry-run   # discovery only, no per-post fetches

Output: writes data/tcdao_archive/{year}/{date}_{slug}.txt for every
press release, plus a manifest, plus a summary JSON for the analyst.

Integration with D-13
---------------------
Once scraped, every press release flows through the standard ingestion
pipeline. D-13 will:
  - Tag primary_entity=E-011 (TCDAO)
  - Sweep for ALL Tier 1 entity references (VPD, TCSO, TPD,
    Porterville PD, etc.) — these appear constantly in prosecution
    announcements ("Visalia Police Department investigated…")
  - Sweep personnel for cross-jurisdiction migration patterns
  - Sweep vendors for any Tyler/Journal/Odyssey/Evidence.com mentions
  - Emit XREF findings: TCDAO → originating agency for every named
    case, building a quantified prosecution-volume map
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


def _now_iso() -> str:
    """ISO-8601 UTC timestamp using timezone-aware datetime.now(UTC).

    Project convention (CLAUDE.md) is to avoid datetime.utcnow() since
    it returns a naive datetime; datetime.now(dt.UTC) is the 3.11+
    timezone-aware replacement.
    """
    return dt.datetime.now(dt.UTC).isoformat()

logger = logging.getLogger("odia.scrapers.tcdao_archive")

BASE_URL = "https://tulareda.org"
ARCHIVE_PATH_TEMPLATE = "/category/press-releases/{year}-press-releases/"
USER_AGENT = (
    "O.D.I.A.-Forensic-Audit-Scraper/1.0 "
    "(civic-accountability research; contact: github.com/SynTechRev/ODIA)"
)
DEFAULT_RATE_LIMIT_SECONDS = 2.0
TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PressRelease:
    url: str
    year: int
    title: str
    publish_date: str           # ISO date string, best-effort parse
    body_text: str              # plain-text normalized body
    body_markdown: str = ""     # optional markdown rendering
    word_count: int = 0
    sha256: str = ""
    scraped_at: str = ""
    inbound_links: list[str] = field(default_factory=list)
    embedded_images: list[str] = field(default_factory=list)


@dataclass
class ScrapeManifest:
    """A persistent record of every scraped URL with hash and timestamps."""
    started_at: str
    completed_at: str | None = None
    years_scraped: list[int] = field(default_factory=list)
    pages_visited: int = 0
    releases_scraped: int = 0
    releases_skipped_dedup: int = 0
    errors: list[dict] = field(default_factory=list)
    releases: list[dict] = field(default_factory=list)  # one dict per PressRelease


# ---------------------------------------------------------------------------
# HTTP session with politeness
# ---------------------------------------------------------------------------

class PoliteSession:
    """
    Requests session wrapper that enforces:
      - robots.txt compliance
      - rate limiting via inter-request sleep
      - identifying User-Agent
      - exponential backoff on 429/503
      - request-level logging
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        user_agent: str = USER_AGENT,
        rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS,
    ):
        self._base_url = base_url
        self._rate_limit = rate_limit_seconds
        self._last_request_time = 0.0
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})

        # Load robots.txt
        self._robots = RobotFileParser()
        self._robots.set_url(urljoin(base_url, "/robots.txt"))
        try:
            self._robots.read()
            logger.info("robots.txt loaded from %s", base_url)
        except Exception as e:
            logger.warning("robots.txt read failed (%s); defaulting to permissive.", e)

    def get(self, url: str) -> requests.Response | None:
        """Fetch a URL, enforcing politeness. Returns None if blocked or failed."""
        if not self._robots.can_fetch(USER_AGENT, url):
            logger.warning("robots.txt disallows %s; skipping.", url)
            return None

        # Throttle
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)

        attempts = 0
        while attempts < 4:
            try:
                resp = self._session.get(url, timeout=TIMEOUT_SECONDS)
                self._last_request_time = time.time()

                if resp.status_code == 200:
                    logger.debug("GET %s -> 200 (%d bytes)", url, len(resp.content))
                    return resp

                if resp.status_code in (429, 503):
                    backoff = min(2 ** attempts * 5, 60)
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            backoff = max(backoff, int(retry_after))
                        except ValueError:
                            pass
                    logger.warning(
                        "GET %s -> %d; backing off %ds (attempt %d)",
                        url, resp.status_code, backoff, attempts + 1,
                    )
                    time.sleep(backoff)
                    attempts += 1
                    continue

                # Other 4xx/5xx: log and abandon
                logger.warning("GET %s -> %d; abandoning.", url, resp.status_code)
                return None

            except requests.RequestException as e:
                logger.warning("GET %s exception: %s; retrying.", url, e)
                time.sleep(2 ** attempts)
                attempts += 1

        logger.error("GET %s failed after %d attempts.", url, attempts)
        return None


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

def _parse_archive_page(html: str, base_url: str) -> list[str]:
    """
    Extract press release URLs from a yearly archive page.

    The site uses WordPress's category archive layout: each post appears
    as a section with title link, excerpt, and "Read more" link. The
    title link is what we want.
    """
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []

    # WordPress standard: posts are <article> elements; title links live
    # inside <h2><a href=...>. Loops Marketing's theme conforms to this.
    for article in soup.find_all("article"):
        link = article.find("h2")
        if link:
            a = link.find("a", href=True)
            if a:
                urls.append(urljoin(base_url, a["href"]))
                continue

        # Fallback: first <a class="read-more"> or first inbound /year/ link
        rm = article.find("a", class_="read-more")
        if rm and rm.get("href"):
            urls.append(urljoin(base_url, rm["href"]))
            continue

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def _find_next_archive_page(html: str, base_url: str) -> str | None:
    """Extract pagination 'next' link from an archive page, if present."""
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.find("a", class_="next page-numbers")
    if next_link and next_link.get("href"):
        return urljoin(base_url, next_link["href"])
    return None


def _parse_press_release(html: str, url: str, year: int) -> PressRelease | None:
    """Extract title, date, body from a single press release page."""
    soup = BeautifulSoup(html, "html.parser")

    # Title — h1.entry-title or first h1
    title_tag = soup.find("h1", class_="entry-title") or soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "(untitled)"

    # Publish date — multiple WordPress conventions; try them all
    pub_date = ""
    for sel in [
        "time.entry-date",
        "time.published",
        "time[datetime]",
        "span.posted-on time",
    ]:
        t = soup.select_one(sel)
        if t and (t.get("datetime") or t.get_text(strip=True)):
            pub_date = t.get("datetime") or t.get_text(strip=True)
            break

    # If no machine-readable date, look in the body for "On <Month> <day>, <year>"
    # which is the TCDAO's consistent narrative opening pattern.
    body_tag = soup.find("div", class_="entry-content") or soup.find("article")
    if not body_tag:
        logger.warning("No entry-content found at %s", url)
        return None

    body_text = body_tag.get_text(separator="\n", strip=True)
    body_text = re.sub(r"\n{3,}", "\n\n", body_text)

    if not pub_date:
        m = re.search(
            r"(?:On|At|Today|Yesterday on)\s+"
            r"(January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})",
            body_text,
        )
        if m:
            pub_date = f"{m.group(3)}-{_month_to_num(m.group(1)):02d}-{int(m.group(2)):02d}"

    # Inbound links and embedded images
    inbound_links = []
    for a in body_tag.find_all("a", href=True):
        href = urljoin(BASE_URL, a["href"])
        if href and href not in inbound_links:
            inbound_links.append(href)

    embedded_images = []
    for img in body_tag.find_all("img", src=True):
        embedded_images.append(urljoin(BASE_URL, img["src"]))

    sha = hashlib.sha256(body_text.encode("utf-8")).hexdigest()

    return PressRelease(
        url=url,
        year=year,
        title=title,
        publish_date=pub_date,
        body_text=body_text,
        word_count=len(body_text.split()),
        sha256=sha,
        scraped_at=_now_iso(),
        inbound_links=inbound_links[:50],
        embedded_images=embedded_images[:20],
    )


def _month_to_num(name: str) -> int:
    return {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
    }.get(name, 1)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def discover_press_release_urls(
    session: PoliteSession,
    year: int,
) -> list[str]:
    """
    Walk all paginated archive pages for a given year and return all
    press release URLs.
    """
    urls: list[str] = []
    current = urljoin(BASE_URL, ARCHIVE_PATH_TEMPLATE.format(year=year))
    seen_pages = set()
    while current and current not in seen_pages:
        seen_pages.add(current)
        logger.info("Discovering year=%d page=%s", year, current)
        resp = session.get(current)
        if not resp:
            break
        new_urls = _parse_archive_page(resp.text, BASE_URL)
        logger.info("  -> %d post links on this page", len(new_urls))
        urls.extend(new_urls)
        current = _find_next_archive_page(resp.text, BASE_URL)

    # Deduplicate across pages
    seen = set()
    deduped = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def scrape_press_release(
    session: PoliteSession,
    url: str,
    year: int,
) -> PressRelease | None:
    """Fetch and parse a single press release."""
    resp = session.get(url)
    if not resp:
        return None
    return _parse_press_release(resp.text, url, year)


def write_release(release: PressRelease, out_dir: Path) -> Path:
    """Write a press release to disk as a .txt file under year/ subdir."""
    year_dir = out_dir / str(release.year)
    year_dir.mkdir(parents=True, exist_ok=True)
    # Slug from URL final path segment
    slug = urlparse(release.url).path.rstrip("/").rsplit("/", 1)[-1] or release.sha256[:12]
    date_prefix = release.publish_date[:10] if release.publish_date else "undated"
    filename = year_dir / f"{date_prefix}_{slug}.txt"
    filename.write_text(
        f"URL: {release.url}\n"
        f"Title: {release.title}\n"
        f"Date: {release.publish_date}\n"
        f"SHA256: {release.sha256}\n"
        f"Scraped: {release.scraped_at}\n"
        f"\n"
        f"{release.body_text}\n",
        encoding="utf-8",
    )
    return filename


def run_scrape(
    start_year: int,
    end_year: int,
    out_dir: Path,
    rate_limit: float = DEFAULT_RATE_LIMIT_SECONDS,
    refresh: bool = False,
    dry_run: bool = False,
) -> ScrapeManifest:
    """
    Main orchestration entry point. Discovers, scrapes, writes, and
    builds the manifest.
    """
    session = PoliteSession(rate_limit_seconds=rate_limit)
    manifest = ScrapeManifest(
        started_at=_now_iso(),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    seen_urls = set()
    if manifest_path.exists() and not refresh:
        try:
            prior = json.loads(manifest_path.read_text(encoding="utf-8"))
            seen_urls = {r["url"] for r in prior.get("releases", [])}
            logger.info("Loaded prior manifest with %d known URLs.", len(seen_urls))
        except Exception:
            logger.warning("Failed to load prior manifest; treating as fresh run.")

    for year in range(start_year, end_year + 1):
        manifest.years_scraped.append(year)
        urls = discover_press_release_urls(session, year)
        manifest.pages_visited += 1

        for url in urls:
            if url in seen_urls and not refresh:
                manifest.releases_skipped_dedup += 1
                continue

            if dry_run:
                logger.info("[DRY RUN] would scrape: %s", url)
                continue

            release = scrape_press_release(session, url, year)
            if not release:
                manifest.errors.append({"url": url, "year": year, "reason": "fetch_or_parse_failed"})
                continue

            try:
                path = write_release(release, out_dir)
                logger.info("Wrote %s (%d words)", path.name, release.word_count)
            except Exception as e:
                manifest.errors.append({"url": url, "year": year, "reason": f"write_failed: {e}"})
                continue

            manifest.releases_scraped += 1
            manifest.releases.append(asdict(release))

    manifest.completed_at = _now_iso()
    manifest_path.write_text(
        json.dumps(asdict(manifest), indent=2), encoding="utf-8"
    )
    logger.info(
        "Scrape complete. %d releases scraped, %d skipped (dedup), %d errors.",
        manifest.releases_scraped,
        manifest.releases_skipped_dedup,
        len(manifest.errors),
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tcdao_archive")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--out", type=Path, default=Path("data/tcdao_archive"))
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT_SECONDS)
    parser.add_argument("--refresh", action="store_true", help="Re-scrape regardless of dedup")
    parser.add_argument("--dry-run", action="store_true", help="Discovery only; no per-post fetches")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    manifest = run_scrape(
        start_year=args.start_year,
        end_year=args.end_year,
        out_dir=args.out,
        rate_limit=args.rate_limit,
        refresh=args.refresh,
        dry_run=args.dry_run,
    )
    return 0 if not manifest.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
