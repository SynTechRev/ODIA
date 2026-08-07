"""Smaller CCP § 1281.96 provider retrieval clients.

Covers four providers beyond AAA and JAMS:
    ADRS          -- ADR Services, Inc. (adrs.com)
    JUDICATE_WEST -- Judicate West (judicatewest.com)
    FEDARB        -- Federal Arbitration, Inc. (fedarb.com)
    NAM           -- National Arbitration and Mediation (namadr.com)

Each provider publishes quarterly statistics in a slightly different format,
but all are scrape-able via requests + BeautifulSoup.  The SmallerProviderRetriever
dispatches to per-provider parsers that share the same NormalizedCase output shape.

All parse_*_html() methods accept pre-fetched HTML so tests never hit live sites.
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

_USER_AGENT = (
    "Mozilla/5.0 (compatible; ODIA/3.8.3; research scraper; "
    "+https://github.com/SynTechRev/ODIA)"
)

_PROVIDER_URLS: dict[str, str] = {
    "ADRS": "https://www.adrs.com/arbitration-statistics",
    "JUDICATE_WEST": "https://www.judicatewest.com/arbitration-statistics",
    "FEDARB": "https://www.fedarb.com/arbitration-statistics",
    "NAM": "https://www.namadr.com/arbitration-statistics",
}


@dataclass
class SmallProviderRelease:
    provider: str
    year: int
    quarter: int
    url: str
    fmt: str  # "csv" | "excel" | "html_table"
    label: str = ""


# Shared column map for smaller providers -- they tend to use simpler headers
_COL_MAP: dict[str, str] = {
    "case number": "case_number",
    "case no": "case_number",
    "filing date": "filing_date",
    "date filed": "filing_date",
    "close date": "disposition_date",
    "closing date": "disposition_date",
    "date closed": "disposition_date",
    "business name": "non_consumer_party_name",
    "respondent": "non_consumer_party_name",
    "name of business": "non_consumer_party_name",
    "company": "non_consumer_party_name",
    "dispute type": "dispute_type",
    "type of dispute": "dispute_type",
    "nature": "dispute_type",
    "claim amount": "claim_amount_usd",
    "amount of claim": "claim_amount_usd",
    "claim ($)": "claim_amount_usd",
    "disposition": "disposition_type",
    "type of disposition": "disposition_type",
    "outcome": "disposition_type",
    "result": "disposition_type",
    "prevailing party": "prevailing_party",
    "award to": "prevailing_party",
    "in favor of": "prevailing_party",
    "award amount": "award_amount_usd",
    "amount of award": "award_amount_usd",
    "award ($)": "award_amount_usd",
    "consumer represented": "consumer_represented",
    "represented": "consumer_represented",
    "attorney": "consumer_represented",
    "arbitrator": "arbitrator_names",
    "neutral": "arbitrator_names",
    "arbitrator name": "arbitrator_names",
    "business fees": "arbitrator_fee_business",
    "consumer fees": "arbitrator_fee_consumer",
    "fee waiver": "fee_waiver",
    "waiver": "fee_waiver",
}


def _map_header(raw: str) -> str | None:
    return _COL_MAP.get(raw.strip().lower())


class SmallerProviderRetriever:
    """Retrieve and parse consumer arbitration data from smaller CCP § 1281.96 providers.

    Dispatches to per-provider parsing logic while sharing normalization helpers.
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
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._last_fetch: float = 0.0

    # ------------------------------------------------------------------
    # Public interface (test-friendly)
    # ------------------------------------------------------------------

    def parse_html_table(
        self,
        html: str | bytes,
        provider: str,
        year: int,
        quarter: int,
        source_url: str | None = None,
        entity_registry: EntityRegistry | None = None,
    ) -> list[NormalizedCase]:
        """Parse an HTML page containing a case-data table for any small provider.

        Pass fixture HTML in tests to avoid network access.
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
                raw_rows, provider, year, quarter, source_url, entity_registry
            )
        return []

    def parse_csv_bytes(
        self,
        content: bytes,
        provider: str,
        year: int,
        quarter: int,
        source_url: str | None = None,
        entity_registry: EntityRegistry | None = None,
    ) -> list[NormalizedCase]:
        """Parse CSV bytes from any small provider."""
        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        raw_rows = [dict(row) for row in reader if any(row.values())]
        return self._normalize_rows(
            raw_rows, provider, year, quarter, source_url, entity_registry
        )

    # ------------------------------------------------------------------
    # Live retrieval
    # ------------------------------------------------------------------

    def fetch_all_providers(
        self,
        providers: list[str] | None = None,
        start_year: int = 2019,
        end_year: int = 2024,
        entity_registry: EntityRegistry | None = None,
    ) -> list[NormalizedCase]:
        """Retrieve all quarterly data for the specified providers.

        providers defaults to all four: ADRS, JUDICATE_WEST, FEDARB, NAM.
        Call only after fixture-based tests pass.
        """
        if providers is None:
            providers = list(_PROVIDER_URLS)
        all_cases: list[NormalizedCase] = []
        for provider in providers:
            base_url = _PROVIDER_URLS.get(provider)
            if base_url is None:
                log.warning("Unknown provider %s -- skipping", provider)
                continue
            try:
                releases = self.fetch_quarterly_index(provider, base_url)
                for rel in releases:
                    if not (start_year <= rel.year <= end_year):
                        continue
                    cases = self.download_and_parse(
                        rel, entity_registry=entity_registry
                    )
                    all_cases.extend(cases)
                    log.info(
                        "%s Q%s %s: %d cases",
                        provider,
                        rel.quarter,
                        rel.year,
                        len(cases),
                    )
            except Exception:
                log.exception("Failed to retrieve %s -- continuing", provider)
        return all_cases

    def fetch_quarterly_index(
        self,
        provider: str,
        base_url: str | None = None,
        html_source: str | None = None,
    ) -> list[SmallProviderRelease]:
        """Discover release download links from a provider's stats page."""
        if base_url is None:
            base_url = _PROVIDER_URLS.get(provider, "")
        if html_source is None:
            self._check_robots(base_url, provider)
            html_source = self._get(base_url).text
            self._save_snapshot(html_source, f"{provider.lower()}_index.html")
        return self._parse_index(html_source, provider, base_url)

    def download_and_parse(
        self,
        release: SmallProviderRelease,
        entity_registry: EntityRegistry | None = None,
    ) -> list[NormalizedCase]:
        """Download and parse a single provider quarterly release."""
        if release.fmt == "html_table":
            self._check_robots(release.url, release.provider)
            resp = self._get(release.url)
            fname = f"{release.provider.lower()}_{release.year}_q{release.quarter}.html"
            self._save_snapshot(resp.text, fname)
            return self.parse_html_table(
                resp.text,
                release.provider,
                release.year,
                release.quarter,
                source_url=release.url,
                entity_registry=entity_registry,
            )
        self._check_robots(release.url, release.provider)
        resp = self._get(release.url)
        content = resp.content
        if release.fmt == "excel":
            return self._parse_excel_bytes(
                content,
                release.provider,
                release.year,
                release.quarter,
                release.url,
                entity_registry,
            )
        return self.parse_csv_bytes(
            content,
            release.provider,
            release.year,
            release.quarter,
            release.url,
            entity_registry,
        )

    # ------------------------------------------------------------------
    # Index parsing
    # ------------------------------------------------------------------

    def _parse_index(
        self, html: str, provider: str, base_url: str
    ) -> list[SmallProviderRelease]:
        soup = BeautifulSoup(html, "html.parser")
        releases: list[SmallProviderRelease] = []
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            lower = href.lower()
            if not any(ext in lower for ext in (".csv", ".xlsx", ".xls")):
                continue
            label = a.get_text(strip=True)
            year, quarter = self._infer_year_quarter(label + " " + href)
            if year is None:
                continue
            fmt = "excel" if any(ext in lower for ext in (".xlsx", ".xls")) else "csv"
            abs_url = (
                href
                if href.startswith("http")
                else urllib.parse.urljoin(base_url, href)
            )
            releases.append(
                SmallProviderRelease(
                    provider=provider,
                    year=year,
                    quarter=quarter or 1,
                    url=abs_url,
                    fmt=fmt,
                    label=label,
                )
            )
        return releases

    @staticmethod
    def _infer_year_quarter(text: str) -> tuple[int | None, int | None]:
        import re

        year_m = re.search(r"\b(20\d{2})\b", text)
        quarter_m = re.search(r"[Qq](\d)", text)
        return (
            int(year_m.group(1)) if year_m else None,
            int(quarter_m.group(1)) if quarter_m else None,
        )

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalize_rows(
        self,
        raw_rows: list[dict],
        provider: str,
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
                continue

            raw_sha = make_retrieval_sha256({**raw, "_provider": provider})
            case_id = make_case_id(provider, {**raw, "_provider": provider})

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

            biz_fee = parse_amount(mapped.get("arbitrator_fee_business"))
            con_fee = parse_amount(mapped.get("arbitrator_fee_consumer"))
            fee_total = None
            fee_consumer_pct = None
            if biz_fee is not None or con_fee is not None:
                fee_total = (biz_fee or 0.0) + (con_fee or 0.0)
                if fee_total > 0 and con_fee is not None:
                    fee_consumer_pct = round(con_fee / fee_total, 4)

            quality_flags: list[str] = []
            if not biz_name or biz_name == "UNKNOWN":
                quality_flags.append("MISSING_PARTY_NAME")
            if raw_claim is None:
                quality_flags.append("MISSING_CLAIM_AMOUNT")

            cases.append(
                NormalizedCase(
                    case_id=case_id,
                    provider=provider,
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
                    non_consumer_initiating=None,
                    dispute_type=mapped.get("dispute_type"),
                    dispute_subtype=None,
                    consumer_represented=normalize_consumer_represented(
                        mapped.get("consumer_represented")
                    ),
                    prevailing_party=raw_prev,
                    claim_amount_usd=raw_claim,
                    claim_amount_tier=claim_amount_tier(raw_claim),
                    award_amount_usd=raw_award,
                    claim_to_award_ratio=ratio,
                    disposition_type=raw_disp,
                    arbitrator_names=normalize_arbitrator_names(
                        mapped.get("arbitrator_names")
                    ),
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
        provider: str,
        year: int,
        quarter: int,
        source_url: str | None,
        entity_registry: EntityRegistry | None,
    ) -> list[NormalizedCase]:
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
            raw_rows, provider, year, quarter, source_url, entity_registry
        )

    @staticmethod
    def _make_session() -> requests.Session:
        s = requests.Session()
        s.headers["User-Agent"] = _USER_AGENT
        return s

    def _check_robots(self, url: str, provider: str) -> None:
        if provider not in self._robots:
            parsed = urllib.parse.urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
                self._robots[provider] = rp
            except Exception:
                self._robots[provider] = None
        rp = self._robots.get(provider)
        if rp and not rp.can_fetch(_USER_AGENT, url):
            raise PermissionError(f"robots.txt disallows fetching {url}")

    def _get(self, url: str) -> requests.Response:
        elapsed = time.monotonic() - self._last_fetch
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        log.debug("GET %s", url)
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
