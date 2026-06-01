"""CourtListener API integration — live case treatment signals.

Fetches citation treatment data from the CourtListener REST API
(courtlistener.com/api/rest/v4/) to supplement or override the static
treatment signal table in case_currency.py.

CourtListener provides:
  - Opinion search by case name / citation
  - Citation treatment signals (cites, cited by, negative treatment)
  - Court hierarchy information

The integration is optional — if COURTLISTENER_API_KEY is not set, the
module operates in degraded mode (returns empty results, falls back to
static table).

Usage::

    from odia_legal.treatment.courtlistener import CourtListenerClient

    client = CourtListenerClient()
    opinion = client.search_opinion("Carpenter v. United States")
    if opinion:
        print(opinion["absolute_url"])

    # Get negative treatment for a case
    signals = client.get_negative_treatment("carpet-v-united-states")
    for s in signals:
        print(s["treatment"], s["citing_case"])

Environment variables:
  COURTLISTENER_API_KEY  — API token from courtlistener.com/settings/profile/
  COURTLISTENER_BASE_URL — override API base (default: https://www.courtlistener.com)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_BASE_URL = os.environ.get("COURTLISTENER_BASE_URL", "https://www.courtlistener.com")
_API_ROOT = f"{_BASE_URL}/api/rest/v4"

# Negative treatment keywords from CourtListener citation type codes
_NEGATIVE_TREATMENT_CODES = frozenset(
    {
        "Overruled",
        "Superseded by Statute",
        "Reversed and Remanded",
        "Reversed",
        "Disagreed With",
        "Not Followed",
    }
)


class CourtListenerClient:
    """Client for the CourtListener REST API.

    Requires `requests` (already a project dependency).  API key is
    optional for read-only public endpoints but strongly recommended to
    avoid rate-limiting.
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 15,
        delay: float = 0.5,
    ) -> None:
        self._api_key = api_key or os.environ.get("COURTLISTENER_API_KEY", "")
        self._timeout = timeout
        self._delay = delay
        self._session: Any = None

    def _get_session(self) -> Any:
        """Lazily initialize a requests.Session."""
        if self._session is None:
            try:
                import requests

                self._session = requests.Session()
                self._session.headers["Accept"] = "application/json"
                if self._api_key:
                    self._session.headers["Authorization"] = f"Token {self._api_key}"
            except ImportError:
                logger.warning("CourtListenerClient: requests not installed")
                return None
        return self._session

    def _get(self, path: str, params: dict | None = None) -> dict | None:
        """GET a CourtListener API endpoint. Returns None on failure."""
        session = self._get_session()
        if session is None:
            return None
        url = f"{_API_ROOT}/{path.lstrip('/')}"
        try:
            resp = session.get(url, params=params, timeout=self._timeout)
            resp.raise_for_status()
            time.sleep(self._delay)
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("CourtListenerClient: %s failed: %s", url, exc)
            return None

    def search_opinion(
        self,
        query: str,
        court: str | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Search for opinions matching a case name or citation.

        Args:
            query: Case name fragment or citation (e.g. "Carpenter v. United States")
            court: Optional court abbreviation filter (e.g. "scotus", "ca9")
            limit: Maximum results to return

        Returns:
            List of opinion dicts from CourtListener, or empty list.
        """
        params: dict[str, Any] = {
            "q": query,
            "page_size": limit,
            "order_by": "score desc",
        }
        if court:
            params["court"] = court
        result = self._get("search/", params=params)
        if result is None:
            return []
        return result.get("results", [])

    def get_opinion(self, opinion_id: str | int) -> dict[str, Any] | None:
        """Fetch a single opinion by its CourtListener cluster ID."""
        result = self._get(f"clusters/{opinion_id}/")
        return result

    def get_citing_opinions(
        self,
        cluster_id: str | int,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return opinions that cite the given cluster ID."""
        result = self._get(
            "search/",
            params={
                "q": f"cites:({cluster_id})",
                "page_size": limit,
                "order_by": "score desc",
            },
        )
        if result is None:
            return []
        return result.get("results", [])

    def get_negative_treatment(
        self,
        case_name: str,
        court: str | None = None,
    ) -> list[dict[str, Any]]:
        """Find opinions with negative treatment of the named case.

        Returns a list of dicts with keys: treatment, citing_case, citation,
        court, date_filed, cluster_id.
        """
        # Search for the case to get its cluster_id
        opinions = self.search_opinion(case_name, court=court, limit=1)
        if not opinions:
            return []

        cluster_id = opinions[0].get("cluster_id") or opinions[0].get("id")
        if not cluster_id:
            return []

        # Get citing opinions and filter for negative treatment signals
        citing = self.get_citing_opinions(cluster_id, limit=50)
        negative = []
        for op in citing:
            treatment = op.get("citation_type", "")
            if any(neg in treatment for neg in _NEGATIVE_TREATMENT_CODES):
                negative.append(
                    {
                        "treatment": treatment,
                        "citing_case": op.get("caseName", ""),
                        "citation": op.get("citation", [{}])[0].get("cite", ""),
                        "court": op.get("court", ""),
                        "date_filed": op.get("dateFiled", ""),
                        "cluster_id": op.get("cluster_id", ""),
                        "absolute_url": f"{_BASE_URL}{op.get('absolute_url', '')}",
                    }
                )
        return negative

    def enrich_treatment_table(
        self,
        case_ids: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Batch-enrich treatment signals for a list of case names.

        Returns a dict of {case_name_fragment: enriched_data}.
        Used by the temporal versioning system to update the static table.
        """
        enriched: dict[str, dict[str, Any]] = {}
        for case_name in case_ids:
            opinions = self.search_opinion(case_name, limit=1)
            if opinions:
                op = opinions[0]
                enriched[case_name] = {
                    "cluster_id": op.get("cluster_id", ""),
                    "absolute_url": f"{_BASE_URL}{op.get('absolute_url', '')}",
                    "caseName": op.get("caseName", ""),
                    "dateFiled": op.get("dateFiled", ""),
                    "court": op.get("court", ""),
                    "source_url": f"{_BASE_URL}{op.get('absolute_url', '')}",
                }
        return enriched

    def is_available(self) -> bool:
        """Return True if the API is reachable."""
        result = self._get("search/", params={"q": "test", "page_size": 1})
        return result is not None

    def close(self) -> None:
        """Close the underlying session."""
        if self._session is not None:
            self._session.close()
            self._session = None
