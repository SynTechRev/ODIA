"""PrimeGov public-portal adapter.

PrimeGov (tularecounty.primegov.com, powered by Granicus) is a SaaS
meeting-management platform that replaced Tulare County's legacy Questys
CMX system. Meeting agendas and packets are compiled to PDF and stored in
Azure Blob Storage; a signed SAS URL is issued on demand by the API.

This adapter:
  1. Loads a CSRF token from the public portal HTML (no login required)
  2. Lists all archived and upcoming BOS meetings via the public JSON API
  3. For each meeting's PDF Agenda document, fetches a time-limited signed
     download URL from Azure Blob Storage
  4. Downloads the PDF and returns it for the ingest pipeline

The download URL expires in ~1 hour so it must not be persisted to cache
as a raw URL — only the compiled file ID and metadata are cached.

API endpoints (all public, no auth):
  GET /api/v2/PublicPortal/GetArchivedMeetingYears
  GET /api/v2/PublicPortal/ListArchivedMeetingsByCommitteeId?year=N&committeeId=M
  GET /api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=M
  GET /api/Meeting/getcompiledfiledownloadurl?compiledFileId=N
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .base import DataSourceAdapter

logger = logging.getLogger(__name__)

_DEFAULT_PAUSE_SEC = 1.5
_DEFAULT_LONG_PAUSE_EVERY_N = 20
_DEFAULT_LONG_PAUSE_SEC = 10.0
_MIN_PDF_BYTES = 5_000
_MAX_RETRIES = 3
_RETRY_BACKOFF_SEC = 30.0

# compileOutputType values observed in the API
_OUTPUT_TYPE_PDF = 1
_OUTPUT_TYPE_HTML = 3


@dataclass
class PrimeGovMeetingDoc:
    """One compiled document attached to a BOS meeting."""

    compiled_file_id: int
    meeting_id: int
    meeting_date: str  # ISO 8601 date string
    template_name: str  # e.g. "PDF Agenda", "HTML Agenda Packet"
    output_type: int  # 1=PDF, 3=HTML
    publish_status: int  # 1=published


@dataclass
class PrimeGovDownload:
    """A successfully downloaded compiled agenda PDF."""

    compiled_file_id: int
    meeting_id: int
    meeting_date: str
    content: bytes
    content_type: str
    sha256: str
    signed_url: str = field(repr=False)


class PrimeGovAdapter(DataSourceAdapter):
    """Adapter for PrimeGov public meeting portal document harvest.

    Usage:
        a = PrimeGovAdapter(portal_url="https://tularecounty.primegov.com", committee_id=25)
        catalog = a.list_meeting_docs(years=[2026, 2025])
        for doc in catalog:
            dl = a.download(doc)
            if dl:
                # hand dl.content to the ingest pipeline
                ...
    """

    def __init__(
        self,
        portal_url: str,
        committee_id: int,
        *,
        cache_dir: Path | str = "cache/adapters",
        pause_sec: float = _DEFAULT_PAUSE_SEC,
        long_pause_every_n: int = _DEFAULT_LONG_PAUSE_EVERY_N,
        long_pause_sec: float = _DEFAULT_LONG_PAUSE_SEC,
        ua_impersonate: str = "chrome131",
        include_output_types: tuple[int, ...] = (_OUTPUT_TYPE_PDF,),
    ):
        super().__init__(name="primegov", cache_dir=cache_dir)
        self.portal_url = portal_url.rstrip("/")
        self.committee_id = committee_id
        self.pause_sec = pause_sec
        self.long_pause_every_n = long_pause_every_n
        self.long_pause_sec = long_pause_sec
        self.ua_impersonate = ua_impersonate
        self.include_output_types = include_output_types
        self._session = None
        self._csrf_token: str = ""

    # ------------------------------------------------------------------
    # DataSourceAdapter contract
    # ------------------------------------------------------------------

    def fetch(self, query: dict) -> list[dict]:
        """Harvest-and-catalog convenience for the CAIP contract.

        query keys (all optional):
            years:  list[int]   years to harvest (default: all available)

        Returns a list of dicts: [{compiled_file_id, meeting_id, meeting_date,
                                    template_name, output_type}, ...]
        """
        years = query.get("years")
        docs = self.list_meeting_docs(years=years)
        return [
            {
                "compiled_file_id": d.compiled_file_id,
                "meeting_id": d.meeting_id,
                "meeting_date": d.meeting_date,
                "template_name": d.template_name,
                "output_type": d.output_type,
            }
            for d in docs
        ]

    def normalize(self, raw_records: list[dict]) -> list[dict]:
        return raw_records

    # ------------------------------------------------------------------
    # Session + CSRF
    # ------------------------------------------------------------------

    def _ensure_session(self):
        if self._session is None:
            try:
                from curl_cffi import requests as cffi_requests
            except ImportError as exc:
                raise ImportError(
                    "curl_cffi is required for PrimeGovAdapter: pip install curl-cffi"
                ) from exc
            self._session = cffi_requests.Session(impersonate=self.ua_impersonate)
        return self._session

    def warm_session(self) -> bool:
        """Load the portal page and extract the CSRF token.

        Returns True if the CSRF token was successfully extracted.
        """
        sess = self._ensure_session()
        r = sess.get(f"{self.portal_url}/public/portal", timeout=30)
        if r.status_code != 200:
            logger.warning("PrimeGov warm_session status=%d", r.status_code)
            return False
        m = re.search(r"csrfToken.*?'([^']+)'", r.text)
        if m:
            self._csrf_token = m.group(1)
            logger.debug("PrimeGov CSRF token refreshed (%dB)", len(self._csrf_token))
            return True
        logger.warning("PrimeGov CSRF token not found in portal HTML")
        return False

    def _api_headers(self) -> dict[str, str]:
        return {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*",
            "Referer": f"{self.portal_url}/public/portal",
            "RequestVerificationToken": self._csrf_token,
        }

    # ------------------------------------------------------------------
    # Meeting listing
    # ------------------------------------------------------------------

    def get_available_years(self) -> list[int]:
        """Return the list of years with archived meetings."""
        self.warm_session()
        sess = self._ensure_session()
        r = sess.get(
            f"{self.portal_url}/api/v2/PublicPortal/GetArchivedMeetingYears",
            timeout=20,
            headers=self._api_headers(),
        )
        if r.status_code != 200:
            logger.warning("GetArchivedMeetingYears status=%d", r.status_code)
            return []
        return r.json()

    def _list_meetings_for_year(self, year: int) -> list[dict]:
        sess = self._ensure_session()
        r = sess.get(
            f"{self.portal_url}/api/v2/PublicPortal/ListArchivedMeetingsByCommitteeId"
            f"?year={year}&committeeId={self.committee_id}",
            timeout=30,
            headers=self._api_headers(),
        )
        if r.status_code != 200:
            logger.warning(
                "ListArchivedMeetings year=%d status=%d", year, r.status_code
            )
            return []
        data = r.json()
        return data if isinstance(data, list) else []

    def _list_upcoming_meetings(self) -> list[dict]:
        sess = self._ensure_session()
        r = sess.get(
            f"{self.portal_url}/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId"
            f"?committeeId={self.committee_id}",
            timeout=20,
            headers=self._api_headers(),
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else []

    def list_meeting_docs(
        self, years: list[int] | None = None
    ) -> list[PrimeGovMeetingDoc]:
        """List all compiled documents across meetings.

        Returns docs filtered to self.include_output_types (default: PDF only).
        """
        if not self._csrf_token:
            self.warm_session()

        if years is None:
            years = self.get_available_years()

        meetings: list[dict] = []
        for year in years:
            meetings.extend(self._list_meetings_for_year(year))
            time.sleep(self.pause_sec)

        meetings.extend(self._list_upcoming_meetings())

        docs: list[PrimeGovMeetingDoc] = []
        seen: set[int] = set()
        for m in meetings:
            m_id = m.get("id", 0)
            m_date = m.get("dateTime", "")[:10]
            for d in m.get("documentList", []):
                cid = d.get("id", 0)
                if cid in seen:
                    continue
                if d.get("publishStatus", 0) != 1:
                    continue
                ot = d.get("compileOutputType", 0)
                if ot not in self.include_output_types:
                    continue
                seen.add(cid)
                docs.append(
                    PrimeGovMeetingDoc(
                        compiled_file_id=cid,
                        meeting_id=m_id,
                        meeting_date=m_date,
                        template_name=d.get("templateName", ""),
                        output_type=ot,
                        publish_status=d.get("publishStatus", 0),
                    )
                )

        logger.info(
            "PrimeGov: listed %d documents across %d years (committeeId=%d)",
            len(docs),
            len(years or []),
            self.committee_id,
        )
        return docs

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def _get_signed_url(self, compiled_file_id: int) -> str | None:
        """Fetch a time-limited Azure Blob SAS URL for the given compiled file."""
        sess = self._ensure_session()
        r = sess.get(
            f"{self.portal_url}/api/Meeting/getcompiledfiledownloadurl"
            f"?compiledFileId={compiled_file_id}",
            timeout=20,
            headers=self._api_headers(),
        )
        if r.status_code != 200:
            return None
        url = r.text.strip().strip('"')
        return url if url.startswith("https://") else None

    def download(self, doc: PrimeGovMeetingDoc) -> PrimeGovDownload | None:
        """Download the compiled PDF for doc.

        Returns None on: API error, redirect-loop, tiny/invalid body, or
        persistent network failure after retries.
        """
        if not self._csrf_token:
            self.warm_session()

        for attempt in range(_MAX_RETRIES):
            signed_url = self._get_signed_url(doc.compiled_file_id)
            if not signed_url:
                logger.warning(
                    "PrimeGov: no signed URL for compiledFileId=%d",
                    doc.compiled_file_id,
                )
                return None

            sess = self._ensure_session()
            try:
                r = sess.get(signed_url, timeout=120, allow_redirects=True)
            except Exception as exc:
                logger.warning(
                    "PrimeGov download id=%d attempt=%d error: %s",
                    doc.compiled_file_id,
                    attempt + 1,
                    exc,
                )
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_BACKOFF_SEC)
                continue

            if r.status_code != 200:
                logger.warning(
                    "PrimeGov download id=%d status=%d",
                    doc.compiled_file_id,
                    r.status_code,
                )
                return None

            if len(r.content) < _MIN_PDF_BYTES:
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_BACKOFF_SEC)
                    self.warm_session()
                    continue
                return None

            return PrimeGovDownload(
                compiled_file_id=doc.compiled_file_id,
                meeting_id=doc.meeting_id,
                meeting_date=doc.meeting_date,
                content=r.content,
                content_type=r.headers.get("content-type", "application/pdf"),
                sha256=hashlib.sha256(r.content).hexdigest(),
                signed_url=signed_url,
            )

        return None
