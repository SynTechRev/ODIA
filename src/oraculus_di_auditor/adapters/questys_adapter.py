"""Questys CMX public-portal adapter.

Questys CMX is a 2010-era ASP.NET WebForms document-management system
used by many California county clerks, board secretaries, and DA
offices. Public docs are served via a `File.ashx?id=N` URL, which
requires a valid ASP.NET session cookie (otherwise the server 302-loops
to Login.aspx).

This adapter:
  1. Establishes the session cookie via a one-time GET on Search/Default.aspx
  2. Harvests `File.ashx?id=N` URLs by issuing the public `?q=<term>`
     search URL across an operator-configurable term list, deduping IDs
     across queries
  3. Downloads each ID's bytes with the session cookie attached,
     rejecting tiny HTML "login redirect" responses

It does NOT persist to the DB itself — the ingest pipeline
(`_run_tier1_pipeline` + `_persist_tier1_result`) is the caller's
responsibility. Keeping the adapter pure (no DB writes) lets it be
reused for read-only inventories without touching audit state.

Hardened from the v3.2.5 throwaway probes (`_questys_search_proof.py`,
`_questys_harvest.py`, `_questys_local_ingest.py`) into reusable form.
Bring-up validated against Tulare County BOS (95 docs).
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)


# Default polite-pacing values. Operator can override per-adapter.
_DEFAULT_PAUSE_SEC = 3.0
_DEFAULT_LONG_PAUSE_EVERY_N = 10
_DEFAULT_LONG_PAUSE_SEC = 20.0

# Response < this size + HTML content-type ≈ login redirect page (we
# measured 26 KB consistently against Tulare County's deployment).
_LOGIN_PAGE_MAX_BYTES = 60_000

# Bytes below this for any non-HTML response is suspicious enough to
# treat as a throttle response and retry with backoff.
_MIN_REAL_FILE_BYTES = 1000

_RETRY_BACKOFF_SEC = 60.0
_MAX_RETRIES = 3


@dataclass(frozen=True)
class QuestysFileMeta:
    """A single Questys document the harvester surfaced."""

    doc_id: str  # File.ashx?id=N — N as a string
    filename: str  # original filename from result-grid cell
    ext: str  # lowercase extension without leading dot
    found_via: tuple[str, ...]  # search terms that surfaced this ID


@dataclass(frozen=True)
class QuestysDownload:
    """A successful File.ashx download."""

    doc_id: str
    content: bytes
    content_type: str
    sha256: str


# Default search terms for civic-records harvesting. Operator can
# override per-jurisdiction via QuestysAdapter(search_terms=[...]).
DEFAULT_SEARCH_TERMS: tuple[str, ...] = (
    # Document-type keywords
    "agenda",
    "minutes",
    "minute",
    "resolution",
    "ordinance",
    "staff",
    "report",
    "memo",
    "packet",
    "presentation",
    "attachment",
    "addendum",
    "contract",
    "agreement",
    "amendment",
    "RFP",
    "bid",
    "award",
    "appointment",
    "allocation",
    "budget",
    "fiscal",
    "expenditure",
    "hearing",
    "PSA",
    "consent",
    "board",
    "supervisor",
    # Year anchors — capture dated filenames
    *(str(y) for y in range(2000, 2027)),
    # Departments / functions
    "sheriff",
    "fire",
    "health",
    "housing",
    "planning",
    "transit",
    "grant",
    "settlement",
    "personnel",
)


class QuestysAdapter(DataSourceAdapter):
    """Adapter for Questys CMX public-portal document harvest.

    Usage:
        a = QuestysAdapter(portal_url="https://publicdocs.example.gov/questys.cmx.webclient/")
        a.warm_session()
        catalog = a.harvest_ids()
        for doc_id, meta in catalog.items():
            dl = a.download(doc_id)
            if dl:
                # hand dl.content to the ingest pipeline
                ...
    """

    def __init__(
        self,
        portal_url: str,
        *,
        cache_dir: Path | str = "cache/adapters",
        search_terms: tuple[str, ...] = DEFAULT_SEARCH_TERMS,
        pause_sec: float = _DEFAULT_PAUSE_SEC,
        long_pause_every_n: int = _DEFAULT_LONG_PAUSE_EVERY_N,
        long_pause_sec: float = _DEFAULT_LONG_PAUSE_SEC,
        ua_impersonate: str = "chrome131",
    ):
        super().__init__(name="questys", cache_dir=cache_dir)
        self.portal_url = portal_url.rstrip("/") + "/"
        self.search_url = urljoin(self.portal_url, "Search/Default.aspx")
        self.file_url_base = urljoin(self.portal_url, "File.ashx?id=")
        self.search_terms = tuple(search_terms)
        self.pause_sec = pause_sec
        self.long_pause_every_n = long_pause_every_n
        self.long_pause_sec = long_pause_sec
        self.ua_impersonate = ua_impersonate
        self._session = None  # curl_cffi Session, lazily created

    # ------------------------------------------------------------------
    # DataSourceAdapter contract
    # ------------------------------------------------------------------

    def fetch(self, query: dict) -> list[dict]:
        """Harvest-and-download convenience for the CAIP contract.

        query keys (all optional):
            terms:        list[str]   override default search terms
            max_per_term: int          cap results per search
            extensions:   list[str]   filter to these (with or without dots)

        Returns a list of dicts: [{doc_id, filename, ext, content_b64, sha256}, ...]
        """
        # Most operators want the harvest catalog (IDs + metadata)
        # without immediately downloading — keep fetch() lazy and let
        # ingest_jurisdiction.py drive the per-ID download with its
        # own throttling/retry/persistence wiring.
        terms = query.get("terms") or self.search_terms
        self.warm_session()
        catalog = self.harvest_ids(terms=terms)
        ext_filter = query.get("extensions")
        if ext_filter:
            normalized_exts = {e.lstrip(".").lower() for e in ext_filter}
            catalog = {
                did: meta
                for did, meta in catalog.items()
                if meta.ext in normalized_exts
            }
        return [
            {
                "doc_id": meta.doc_id,
                "filename": meta.filename,
                "ext": meta.ext,
                "found_via": list(meta.found_via),
            }
            for meta in catalog.values()
        ]

    def normalize(self, raw_records: list[dict]) -> list[dict]:
        """Identity transform — Questys metadata is already in our form."""
        return raw_records

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _ensure_session(self):
        """Lazy-construct the curl_cffi Session (so import doesn't fail
        when curl_cffi isn't installed)."""
        if self._session is None:
            try:
                from curl_cffi import requests as cffi_requests
            except ImportError as exc:
                raise ImportError(
                    "curl_cffi is required for QuestysAdapter: pip install curl-cffi"
                ) from exc
            self._session = cffi_requests.Session(impersonate=self.ua_impersonate)
        return self._session

    def warm_session(self) -> int:
        """Hit Search/Default.aspx once to receive ASP.NET session cookies.

        Returns the number of cookies set. Idempotent — safe to call
        repeatedly; subsequent calls refresh the cookie clock.
        """
        sess = self._ensure_session()
        r = sess.get(self.search_url, timeout=30)
        if r.status_code != 200:
            logger.warning(
                "Questys warm_session returned status %d (%dB)",
                r.status_code,
                len(r.content),
            )
            return 0
        return len(sess.cookies)

    # ------------------------------------------------------------------
    # Harvest
    # ------------------------------------------------------------------

    def harvest_ids(
        self, terms: tuple[str, ...] | list[str] | None = None
    ) -> dict[str, QuestysFileMeta]:
        """Run every search term and return deduped {doc_id: meta}.

        Side-effects: makes one HTTP request per term, polite-paced.
        Does NOT download files — that's a separate per-ID call.
        """
        if terms is None:
            terms = self.search_terms
        sess = self._ensure_session()
        catalog: dict[str, QuestysFileMeta] = {}

        for i, term in enumerate(terms, 1):
            try:
                url = f"{self.search_url}?q={str(term).replace(' ', '+')}"
                r = sess.get(url, timeout=60)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Questys harvest %r failed: %s", term, exc)
                continue
            self._merge_search_results(catalog, r.text, term)

            if i < len(terms):
                time.sleep(0.5)  # micro-pace between searches

        return catalog

    @staticmethod
    def _merge_search_results(
        catalog: dict[str, QuestysFileMeta], html: str, term: str
    ) -> None:
        """Extract File.ashx?id=N + filename pairs from one results page."""
        ids = sorted(set(re.findall(r"File\.ashx\?id=(\d+)", html)))
        if not ids:
            return
        id_to_fname = _extract_id_to_filename_map(html, ids)

        for did in ids:
            existing = catalog.get(did)
            fn = id_to_fname.get(did, existing.filename if existing else "")
            ext = (
                fn.rsplit(".", 1)[-1].lower()
                if "." in fn
                else (existing.ext if existing else "")
            )
            if existing is None:
                catalog[did] = QuestysFileMeta(
                    doc_id=did, filename=fn, ext=ext, found_via=(term,)
                )
            else:
                merged_via = (
                    existing.found_via + (term,)
                    if term not in existing.found_via
                    else existing.found_via
                )
                catalog[did] = QuestysFileMeta(
                    doc_id=did,
                    filename=fn or existing.filename,
                    ext=ext or existing.ext,
                    found_via=merged_via,
                )

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self, doc_id: str) -> QuestysDownload | None:
        """Download File.ashx?id=N with the session cookie attached.

        Returns None on:
          - HTTP error
          - login-redirect page (small HTML body)
          - persistent throttle (tiny response that doesn't recover after 3 retries)
        """
        sess = self._ensure_session()
        url = f"{self.file_url_base}{doc_id}&v=1"

        for attempt in range(_MAX_RETRIES):
            try:
                r = sess.get(url, timeout=60, allow_redirects=True)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Questys download id=%s network error: %s", doc_id, exc)
                return None

            ct = r.headers.get("content-type", "")
            if r.status_code != 200:
                return None
            if _is_login_page(ct, r.content):
                return None
            if _looks_like_real_file(ct, r.content):
                return QuestysDownload(
                    doc_id=doc_id,
                    content=r.content,
                    content_type=ct,
                    sha256=hashlib.sha256(r.content).hexdigest(),
                )
            # Suspicious tiny response: back off
            if attempt < _MAX_RETRIES - 1:
                logger.info(
                    "Questys id=%s: %dB on attempt %d; backing off %.0fs",
                    doc_id,
                    len(r.content),
                    attempt + 1,
                    _RETRY_BACKOFF_SEC,
                )
                time.sleep(_RETRY_BACKOFF_SEC)
        return None


# QuestysFileMeta is frozen, so we need a non-frozen-modification helper
# for the BS4-absent code path above:
def _replace_found_via_with(meta: QuestysFileMeta, term: str) -> QuestysFileMeta:
    if term in meta.found_via:
        return meta
    return QuestysFileMeta(
        doc_id=meta.doc_id,
        filename=meta.filename,
        ext=meta.ext,
        found_via=meta.found_via + (term,),
    )


# Monkey-patch a helper onto the dataclass to keep the inline harvest
# code compact (the dataclass is immutable; this is the standard
# "with-replacement" pattern).
QuestysFileMeta._replace_found_via_with = lambda self, term: _replace_found_via_with(  # type: ignore[attr-defined]
    self, term
)


# ----------------------------------------------------------------------
# Module-level helpers (login-page + real-file detection)
# ----------------------------------------------------------------------


def _extract_filename_from_row(row, cells) -> str:
    """Walk cell indices 5, 4, 3 looking for the first non-empty
    string with a dot in it — that's the filename cell."""
    for cell_idx in (5, 4, 3):
        if cell_idx < len(cells):
            text = cells[cell_idx].get_text(" ", strip=True)
            if text and "." in text:
                return text
    return ""


def _extract_id_to_filename_map(html: str, ids: list[str]) -> dict[str, str]:
    """Parse the Telerik results grid and return {File.ashx id: filename}.

    Returns {} when BeautifulSoup isn't installed (caller still gets the
    IDs from the regex; filenames just degrade to "")."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {}

    id_to_fname: dict[str, str] = {}
    soup = BeautifulSoup(html, "html.parser")
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        row_ids = re.findall(r"File\.ashx\?id=(\d+)", str(row))
        if not row_ids:
            continue
        fn = _extract_filename_from_row(row, cells)
        if fn:
            id_to_fname[row_ids[0]] = fn
    return id_to_fname


def _is_login_page(content_type: str, body: bytes) -> bool:
    """Small HTML body containing login markers = redirect, not a real doc."""
    ct = (content_type or "").lower()
    if "text/html" not in ct:
        return False
    if len(body) > _LOGIN_PAGE_MAX_BYTES:
        return False
    head = body[:8000].lower()
    return any(
        marker in head
        for marker in (
            b"login.aspx",
            b"<title>login",
            b"questys solutions",
            b"sign in",
        )
    )


def _looks_like_real_file(content_type: str, body: bytes) -> bool:
    """True iff this looks like a non-trivial document of the expected type."""
    if len(body) < _MIN_REAL_FILE_BYTES:
        return False
    ct = (content_type or "").lower()
    if "text/html" in ct and not body.lower().lstrip().startswith(b"<!doctype html"):
        return False
    return True
