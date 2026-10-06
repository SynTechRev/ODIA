"""CourtListener REST API client.

CourtListener (courtlistener.com) provides free access to U.S. court opinions,
dockets, and citation graphs via a JSON REST API.

API reference: https://www.courtlistener.com/help/api/rest/
Rate limits: 5,000 req/day unauthenticated; 50,000/day with free API key.
Auth: Set env var COURTLISTENER_API_KEY to a free token from courtlistener.com.

This client is intentionally thin — it handles auth, rate-limit backoff,
and deserialization into plain dicts. The caller (CourtListenerCorpusLoader)
converts dicts to CaseLawRecord and CaseLawBuilder writes them to disk.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.courtlistener.com/api/rest/v4"
_DEFAULT_PAGE_SIZE = 20
_RATE_LIMIT_BACKOFF_SEC = 60.0
_MAX_RETRIES = 3


class CourtListenerClient:
    """Thin wrapper around the CourtListener v4 REST API.

    Authentication:
        Set COURTLISTENER_API_KEY in the environment for the 50 k/day tier.
        Anonymous requests work at 5 k/day but may hit limits during bulk harvest.

    Usage:
        cl = CourtListenerClient()
        results = cl.search_opinions(query="CPRA public records", courts=["cal"])
        for r in results:
            cluster = cl.get_cluster(r["cluster_id"])
    """

    def __init__(
        self,
        api_key: str | None = None,
        pause_sec: float = 0.5,
        max_retries: int = _MAX_RETRIES,
    ):
        raw_key = api_key or os.environ.get("COURTLISTENER_API_KEY", "").strip()
        self._api_key: str | None = raw_key or None
        self.pause_sec = pause_sec
        self.max_retries = max_retries
        self._session = None

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def _ensure_session(self):
        if self._session is None:
            try:
                import requests as _requests

                s = _requests.Session()
                s.headers.update({"Accept": "application/json"})
                if self._api_key:
                    s.headers["Authorization"] = f"Token {self._api_key}"
                self._session = s
            except ImportError:
                try:
                    from curl_cffi import requests as cffi_requests

                    s = cffi_requests.Session(impersonate="chrome131")
                    if self._api_key:
                        s.headers["Authorization"] = f"Token {self._api_key}"
                    self._session = s
                except ImportError as exc:
                    raise ImportError(
                        "Either requests or curl-cffi is required for CourtListenerClient"
                    ) from exc
        return self._session

    # ------------------------------------------------------------------
    # Core HTTP helper
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any] | None:
        sess = self._ensure_session()
        url = f"{_BASE_URL}{path}"
        for attempt in range(self.max_retries):
            try:
                r = sess.get(url, params=params or {}, timeout=30)
            except Exception as exc:
                logger.warning(
                    "CourtListener GET %s attempt=%d error: %s", path, attempt + 1, exc
                )
                if attempt < self.max_retries - 1:
                    time.sleep(_RATE_LIMIT_BACKOFF_SEC)
                continue

            if r.status_code == 200:
                try:
                    return r.json()
                except Exception:
                    return None
            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", _RATE_LIMIT_BACKOFF_SEC))
                logger.warning("CourtListener rate-limited; sleeping %ds", retry_after)
                time.sleep(retry_after)
                continue
            if r.status_code == 404:
                return None
            logger.warning("CourtListener %s status=%d", path, r.status_code)
            return None

        return None

    def _paginate(
        self, path: str, params: dict, max_results: int = 100
    ) -> list[dict[str, Any]]:
        """Yield all results across pages up to max_results."""
        results: list[dict[str, Any]] = []
        p = dict(params)
        p["page_size"] = min(_DEFAULT_PAGE_SIZE, max_results)

        while True:
            data = self._get(path, p)
            if not data:
                break
            batch = data.get("results", [])
            results.extend(batch)
            if len(results) >= max_results:
                break
            next_url = data.get("next")
            if not next_url:
                break
            # Extract cursor from next URL
            from urllib.parse import parse_qs, urlparse

            qs = parse_qs(urlparse(next_url).query)
            if "cursor" in qs:
                p["cursor"] = qs["cursor"][0]
            elif "page" in qs:
                p["page"] = qs["page"][0]
            else:
                break
            time.sleep(self.pause_sec)

        return results[:max_results]

    # ------------------------------------------------------------------
    # Opinion search
    # ------------------------------------------------------------------

    def search_opinions(
        self,
        query: str,
        courts: list[str] | None = None,
        date_after: str | None = None,
        date_before: str | None = None,
        order_by: str = "score desc",
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """Search court opinions by keyword.

        Args:
            query: Free-text query (e.g. "CPRA exemption public records")
            courts: List of court slugs (e.g. ["cal", "ca9", "scotus"])
            date_after: ISO date string "YYYY-MM-DD"
            date_before: ISO date string "YYYY-MM-DD"
            order_by: "score desc" | "dateFiled desc" | "dateFiled asc"
            max_results: Max opinions to return

        Returns list of opinion metadata dicts from the search endpoint.
        """
        params: dict[str, Any] = {
            "q": query,
            "type": "o",
            "order_by": order_by,
        }
        if courts:
            params["court"] = " ".join(courts)
        if date_after:
            params["filed_after"] = date_after
        if date_before:
            params["filed_before"] = date_before

        return self._paginate("/search/", params, max_results=max_results)

    # ------------------------------------------------------------------
    # Opinion cluster (a case + all its opinions)
    # ------------------------------------------------------------------

    def get_cluster(self, cluster_id: int | str) -> dict[str, Any] | None:
        """Fetch the opinion cluster (case metadata + opinion list)."""
        return self._get(f"/clusters/{cluster_id}/")

    def get_opinion(self, opinion_id: int | str) -> dict[str, Any] | None:
        """Fetch a single opinion (includes plain_text when available)."""
        return self._get(f"/opinions/{opinion_id}/")

    # ------------------------------------------------------------------
    # Citation graph
    # ------------------------------------------------------------------

    def get_citing_opinions(
        self, cluster_id: int | str, max_results: int = 20
    ) -> list[dict[str, Any]]:
        """Return opinions that cite the given cluster."""
        return self._paginate(
            "/search/",
            {"type": "o", "q": f"cites:({cluster_id})", "order_by": "dateFiled desc"},
            max_results=max_results,
        )

    # ------------------------------------------------------------------
    # Docket lookup
    # ------------------------------------------------------------------

    def get_docket(self, docket_id: int | str) -> dict[str, Any] | None:
        """Fetch docket metadata."""
        return self._get(f"/dockets/{docket_id}/")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Return True if the API is reachable and the key (if any) is valid."""
        data = self._get("/")
        return data is not None
