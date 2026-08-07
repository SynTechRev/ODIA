"""AAA quarterly consumer arbitration data retrieval client.

CCP § 1281.96 requires the American Arbitration Association to publish
quarterly statistics on California consumer arbitrations.  AAA publishes
this data at adr.org as downloadable Excel or CSV files.

Data Pull Protocol (Section II.2):
    - User-Agent: identifies as ODIA research scraper
    - robots.txt: checked before any fetch
    - Rate limit: 1 request per 3 seconds (configurable)
    - Snapshot: full HTML of the index page saved alongside each download

Usage (tests -- never hits network):
    retriever = AAARetriever()
    cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)

Usage (live -- run only after all tests pass):
    retriever = AAARetriever(snapshot_dir=Path("data/snapshots/aaa"))
    releases = retriever.fetch_quarterly_index()
    for rel in releases:
        cases = retriever.download_and_parse(rel, entity_registry=registry)
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import time
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup

from .normalize import (
    NormalizedCase,
    claim_amount_tier,
    make_case_id,
    make_retrieval_sha256,
    normalize_arbitrator_names,
    normalize_bool,
    normalize_consumer_represented,
    normalize_disposition,
    normalize_prevailing,
    parse_amount,
    parse_date,
)

if TYPE_CHECKING:
    from ...entity.registry import EntityRegistry

log = logging.getLogger(__name__)

_PROVIDER = "AAA"
_BASE_URL = "https://www.adr.org"
_STATS_PATH = "/consumer-information/consumer-arbitration-statistics"
_USER_AGENT = (
    "Mozilla/5.0 (compatible; ODIA/3.8.3; research scraper; "
    "+https://github.com/SynTechRev/ODIA)"
)


# ---------------------------------------------------------------------------
# QuarterlyRelease -- a discovered download link
# ---------------------------------------------------------------------------


@dataclass
class QuarterlyRelease:
    """A single quarterly data release discovered on the AAA stats page."""

    year: int
    quarter: int
    url: str  # absolute URL to the file
    fmt: str  # "csv" | "excel" | "html_table"
    label: str = ""  # human-readable label from the page


# ---------------------------------------------------------------------------
# Column map -- normalise AAA header variations across years
# ---------------------------------------------------------------------------

# Maps normalised lower-case header -> NormalizedCase field name
# AAA has changed column names between years; this map handles the variants.
_COL_MAP: dict[str, str] = {
    # Case identifier
    "case number": "case_number",
    "case no": "case_number",
    "case no.": "case_number",
    # Dates
    "date filed": "filing_date",
    "filing date": "filing_date",
    "date filed (mm/dd/yyyy)": "filing_date",
    "date closed": "disposition_date",
    "closing date": "disposition_date",
    "close date": "disposition_date",
    # Parties
    "name of business": "non_consumer_party_name",
    "business name": "non_consumer_party_name",
    "respondent": "non_consumer_party_name",
    "name of respondent": "non_consumer_party_name",
    # Dispute
    "type of dispute": "dispute_type",
    "dispute type": "dispute_type",
    "nature of dispute": "dispute_type",
    # Claim amount
    "amount of claim": "claim_amount_usd",
    "claim amount": "claim_amount_usd",
    "amount of claim ($)": "claim_amount_usd",
    "claim amount ($)": "claim_amount_usd",
    # Disposition
    "type of disposition": "disposition_type",
    "disposition": "disposition_type",
    "disposition type": "disposition_type",
    # Prevailing party
    "prevailing party": "prevailing_party",
    "party in whose favor award rendered": "prevailing_party",
    # Award amount
    "amount of award": "award_amount_usd",
    "award amount": "award_amount_usd",
    "award amount ($)": "award_amount_usd",
    # Representation
    "consumer attorney": "consumer_represented",
    "consumer attorney?": "consumer_represented",
    "consumer represented by attorney": "consumer_represented",
    "represented": "consumer_represented",
    # Arbitrator
    "arbitrator name": "arbitrator_names",
    "arbitrator": "arbitrator_names",
    "name of arbitrator": "arbitrator_names",
    "arbitrator(s)": "arbitrator_names",
    # Fees
    "business filing fee": "arbitrator_fee_business",
    "business fees": "arbitrator_fee_business",
    "consumer filing fee": "arbitrator_fee_consumer",
    "consumer fees": "arbitrator_fee_consumer",
    "fee waiver": "fee_waiver",
    "fee waiver given": "fee_waiver",
    "fee waiver given?": "fee_waiver",
    "fee waiver?": "fee_waiver",
    # Non-consumer initiating
    "initiated by": "initiated_by",
    "filing party": "initiated_by",
}


def _map_header(raw: str) -> str | None:
    return _COL_MAP.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# AAARetriever
# ---------------------------------------------------------------------------


class AAARetriever:
    """Retrieve and parse AAA quarterly consumer arbitration data.

    Two operating modes:
    - Test mode: pass html_source or fixture bytes directly -- no network.
    - Live mode: fetch from adr.org, respecting robots.txt and rate limits.
    """

    def __init__(
        self,
        rate_limit_secs: float = 3.0,
        snapshot_dir: Path | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self._rate_limit = rate_limit_secs
        self._snapshot_dir = snapshot_dir
        self._session = session or self._make_session()
        self._robots: urllib.robotparser.RobotFileParser | None = None
        self._last_fetch: float = 0.0

    # ------------------------------------------------------------------
    # Public interface (test-friendly)
    # ------------------------------------------------------------------

    def parse_html_table(
        self,
        html: str | bytes,
        year: int,
        quarter: int,
        source_url: str | None = None,
        entity_registry: EntityRegistry | None = None,
    ) -> list[NormalizedCase]:
        """Parse an HTML page that contains a case-data table.

        The HTML may be a full AAA statistics page or a minimal fixture.
        All <table> elements are scanned; the first one whose headers map
        to known column names is used.

        This is the primary entry point for tests (pass fixture HTML here).
        """
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                continue
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
            mapped = [_map_header(h) for h in headers]
            if not any(mapped):
                continue
            raw_rows = []
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not any(cells):
                    continue
                raw_rows.append(dict(zip(headers, cells, strict=False)))
            return self._normalize_rows(
                raw_rows, year, quarter, source_url, entity_registry
            )
        return []

    def parse_csv_bytes(
        self,
        content: bytes,
        year: int,
        quarter: int,
        source_url: str | None = None,
        entity_registry: EntityRegistry | None = None,
    ) -> list[NormalizedCase]:
        """Parse AAA CSV bytes into NormalizedCase records."""
        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        raw_rows = [dict(row) for row in reader if any(row.values())]
        return self._normalize_rows(
            raw_rows, year, quarter, source_url, entity_registry
        )

    # ------------------------------------------------------------------
    # Live retrieval (network -- call only after tests pass)
    # ------------------------------------------------------------------

    def fetch_quarterly_index(
        self, html_source: str | None = None
    ) -> list[QuarterlyRelease]:
        """Discover quarterly release download links from the AAA stats page.

        Pass html_source in tests to avoid a network call.
        """
        if html_source is None:
            url = _BASE_URL + _STATS_PATH
            self._check_robots(url)
            html_source = self._get(url).text
            self._save_snapshot(html_source, "aaa_index.html")
        return self._parse_index(html_source)

    def download_and_parse(
        self,
        release: QuarterlyRelease,
        entity_registry: EntityRegistry | None = None,
    ) -> list[NormalizedCase]:
        """Download a quarterly release file and parse it.

        Saves raw HTML snapshot alongside each download (Data Pull Protocol).
        """
        if release.fmt == "html_table":
            self._check_robots(release.url)
            resp = self._get(release.url)
            self._save_snapshot(
                resp.text, f"aaa_{release.year}_q{release.quarter}.html"
            )
            return self.parse_html_table(
                resp.text,
                release.year,
                release.quarter,
                source_url=release.url,
                entity_registry=entity_registry,
            )

        self._check_robots(release.url)
        resp = self._get(release.url)
        self._save_snapshot(
            f"URL: {release.url}\nContent-Type: {resp.headers.get('content-type')}\n",
            f"aaa_{release.year}_q{release.quarter}_meta.txt",
        )
        content = resp.content

        if release.fmt == "excel":
            return self._parse_excel_bytes(
                content,
                release.year,
                release.quarter,
                source_url=release.url,
                entity_registry=entity_registry,
            )
        return self.parse_csv_bytes(
            content,
            release.year,
            release.quarter,
            source_url=release.url,
            entity_registry=entity_registry,
        )

    # ------------------------------------------------------------------
    # Index parsing
    # ------------------------------------------------------------------

    def _parse_index(self, html: str) -> list[QuarterlyRelease]:
        """Extract QuarterlyRelease entries from the AAA statistics index page."""
        soup = BeautifulSoup(html, "html.parser")
        releases: list[QuarterlyRelease] = []

        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            lower = href.lower()
            # Match CSV / Excel download links
            if not any(ext in lower for ext in (".csv", ".xlsx", ".xls")):
                continue
            label = a.get_text(strip=True)
            year, quarter = self._infer_year_quarter(label + " " + href)
            if year is None:
                continue
            fmt = "excel" if any(ext in lower for ext in (".xlsx", ".xls")) else "csv"
            abs_url = href if href.startswith("http") else _BASE_URL + href
            releases.append(
                QuarterlyRelease(
                    year=year, quarter=quarter or 1, url=abs_url, fmt=fmt, label=label
                )
            )

        # Fall back: look for links to stats sub-pages (HTML table mode)
        if not releases:
            for a in soup.find_all("a", href=True):
                label = a.get_text(strip=True)
                year, quarter = self._infer_year_quarter(label)
                if year is None:
                    continue
                abs_url = urllib.parse.urljoin(_BASE_URL + _STATS_PATH, a["href"])
                releases.append(
                    QuarterlyRelease(
                        year=year,
                        quarter=quarter or 1,
                        url=abs_url,
                        fmt="html_table",
                        label=label,
                    )
                )

        return releases

    @staticmethod
    def _infer_year_quarter(text: str) -> tuple[int | None, int | None]:
        """Extract year and quarter from a string like '2024 Q1' or 'Q3_2022'."""
        import re

        year_m = re.search(r"\b(20\d{2})\b", text)
        quarter_m = re.search(r"[Qq](\d)", text)
        year = int(year_m.group(1)) if year_m else None
        quarter = int(quarter_m.group(1)) if quarter_m else None
        return year, quarter

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalize_rows(
        self,
        raw_rows: list[dict],
        year: int,
        quarter: int,
        source_url: str | None,
        entity_registry: EntityRegistry | None,
    ) -> list[NormalizedCase]:
        now = datetime.now()
        cases: list[NormalizedCase] = []
        for raw in raw_rows:
            mapped = {_map_header(k): v for k, v in raw.items() if _map_header(k)}
            if not mapped.get("non_consumer_party_name"):
                continue  # skip header-repeat or empty rows

            raw_sha = make_retrieval_sha256(raw)
            case_id = make_case_id(_PROVIDER, raw)

            filing_dt = parse_date(mapped.get("filing_date"))
            disp_dt = parse_date(mapped.get("disposition_date"))
            days = None
            if filing_dt and disp_dt and disp_dt >= filing_dt:
                days = (disp_dt - filing_dt).days

            raw_claim = parse_amount(mapped.get("claim_amount_usd"))
            raw_award = parse_amount(mapped.get("award_amount_usd"))
            ratio = None
            if raw_claim and raw_claim > 0 and raw_award is not None:
                ratio = round(raw_award / raw_claim, 4)

            raw_disp = normalize_disposition(mapped.get("disposition_type"))
            raw_prev = normalize_prevailing(mapped.get("prevailing_party"), raw_disp)

            biz_name = (mapped.get("non_consumer_party_name") or "UNKNOWN").strip()
            entity_id: str | None = None
            if entity_registry is not None:
                entity = entity_registry.resolve(biz_name)
                if entity:
                    entity_id = entity.entity_id

            rep = normalize_consumer_represented(mapped.get("consumer_represented"))
            arb_names = normalize_arbitrator_names(mapped.get("arbitrator_names"))

            biz_fee = parse_amount(mapped.get("arbitrator_fee_business"))
            con_fee = parse_amount(mapped.get("arbitrator_fee_consumer"))
            fee_total = None
            fee_consumer_pct = None
            if biz_fee is not None or con_fee is not None:
                fee_total = (biz_fee or 0.0) + (con_fee or 0.0)
                if fee_total > 0 and con_fee is not None:
                    fee_consumer_pct = round(con_fee / fee_total, 4)

            non_consumer_init: bool | None = None
            if mapped.get("initiated_by"):
                raw_init = str(mapped["initiated_by"]).strip().upper()
                non_consumer_init = "BUSINESS" in raw_init or "COMPANY" in raw_init

            quality_flags: list[str] = []
            if not biz_name or biz_name == "UNKNOWN":
                quality_flags.append("MISSING_PARTY_NAME")
            if raw_claim is None:
                quality_flags.append("MISSING_CLAIM_AMOUNT")

            cases.append(
                NormalizedCase(
                    case_id=case_id,
                    provider=_PROVIDER,
                    case_url=source_url,
                    retrieval_ts=now,
                    retrieval_sha256=raw_sha,
                    case_year=year,
                    case_quarter=quarter,
                    filing_date=filing_dt,
                    disposition_date=disp_dt,
                    days_to_disposition=days,
                    non_consumer_party_name=biz_name,
                    non_consumer_party_entity_id=entity_id,
                    non_consumer_initiating=non_consumer_init,
                    dispute_type=mapped.get("dispute_type"),
                    dispute_subtype=None,
                    consumer_represented=rep,
                    prevailing_party=raw_prev,
                    claim_amount_usd=raw_claim,
                    claim_amount_tier=claim_amount_tier(raw_claim),
                    award_amount_usd=raw_award,
                    claim_to_award_ratio=ratio,
                    disposition_type=raw_disp,
                    arbitrator_names=arb_names,
                    arbitrator_fee_total_usd=fee_total,
                    arbitrator_fee_alloc_consumer_pct=fee_consumer_pct,
                    fee_waiver=normalize_bool(mapped.get("fee_waiver")),
                    quality_flags=quality_flags,
                )
            )
        return cases

    def _parse_excel_bytes(
        self,
        content: bytes,
        year: int,
        quarter: int,
        source_url: str | None,
        entity_registry: EntityRegistry | None,
    ) -> list[NormalizedCase]:
        """Parse Excel bytes via openpyxl (lazy import -- optional dependency)."""
        try:
            import openpyxl
        except ImportError as exc:
            raise ImportError(
                "openpyxl is required for Excel parsing: pip install openpyxl"
            ) from exc

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        raw_rows = [
            {
                headers[i]: (str(cell) if cell is not None else "")
                for i, cell in enumerate(row)
            }
            for row in rows[1:]
            if any(cell is not None for cell in row)
        ]
        wb.close()
        return self._normalize_rows(
            raw_rows, year, quarter, source_url, entity_registry
        )

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_session() -> requests.Session:
        s = requests.Session()
        s.headers["User-Agent"] = _USER_AGENT
        return s

    def _check_robots(self, url: str) -> None:
        if self._robots is None:
            parsed = urllib.parse.urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self._robots = rp
            except Exception:
                self._robots = None
        if self._robots and not self._robots.can_fetch(_USER_AGENT, url):
            raise PermissionError(f"robots.txt disallows fetching {url}")

    def _get(self, url: str) -> requests.Response:
        elapsed = time.monotonic() - self._last_fetch
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        log.debug("AAA GET %s", url)
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        self._last_fetch = time.monotonic()
        return resp

    def _save_snapshot(self, content: str, filename: str) -> None:
        if self._snapshot_dir is None:
            return
        self._snapshot_dir.mkdir(parents=True, exist_ok=True)
        path = self._snapshot_dir / filename
        path.write_text(content, encoding="utf-8")
        sha = hashlib.sha256(content.encode()).hexdigest()
        log.info("Snapshot saved: %s  sha256=%s", path, sha[:16])
