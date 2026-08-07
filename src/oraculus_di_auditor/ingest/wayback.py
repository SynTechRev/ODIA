"""Wayback Machine availability client for C.O.N.T.R.A. commercial ingest.

Provides:
  find_capture(url, target_date)        -- nearest available snapshot to a date
  retrieve_prior_versions(url)          -- list of major annual snapshots

Uses the Wayback Availability API (https://archive.org/wayback/available).
All requests are read-only; no snapshots are submitted.

Rate policy: 1 request / 2 s (archive.org courtesy limit).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlencode

import requests

log = logging.getLogger(__name__)

_AVAILABILITY_BASE = "https://archive.org/wayback/available"
_REQUEST_DELAY_S = 2.0
_TIMEOUT_S = 15
_USER_AGENT = "ODIA/3.8.3 C.O.N.T.R.A. research archival client"


@dataclass(frozen=True)
class WaybackCapture:
    """Single Wayback Machine snapshot reference."""

    original_url: str
    snapshot_url: str
    timestamp: str  # YYYYMMDDhhmmss as returned by Wayback
    status_code: str | None
    available: bool = True

    @property
    def datetime_utc(self) -> datetime:
        """Parse Wayback timestamp string to UTC datetime."""
        return datetime.strptime(self.timestamp, "%Y%m%d%H%M%S").replace(tzinfo=UTC)


def _get_availability(url: str, timestamp: str | None = None) -> dict[str, Any]:
    """Call the Wayback Availability API and return the JSON response."""
    params: dict[str, str] = {"url": url}
    if timestamp:
        params["timestamp"] = timestamp
    query = urlencode(params)
    api_url = f"{_AVAILABILITY_BASE}?{query}"
    log.debug("Wayback API: %s", api_url)

    resp = requests.get(
        api_url,
        headers={"User-Agent": _USER_AGENT},
        timeout=_TIMEOUT_S,
    )
    resp.raise_for_status()
    return resp.json()


def find_capture(
    url: str, target_date: date | datetime | None = None
) -> WaybackCapture | None:
    """Find the nearest Wayback snapshot to target_date for url.

    Arguments:
        url          -- the original URL to look up
        target_date  -- preferred date; None means most recent available

    Returns a WaybackCapture if a snapshot exists, otherwise None.

    Raises requests.RequestException on network errors.
    """
    timestamp: str | None = None
    if target_date is not None:
        if isinstance(target_date, datetime):
            timestamp = target_date.strftime("%Y%m%d%H%M%S")
        else:
            timestamp = target_date.strftime("%Y%m%d") + "120000"

    data = _get_availability(url, timestamp)

    closest = data.get("archived_snapshots", {}).get("closest")
    if not closest or not closest.get("available"):
        return None

    return WaybackCapture(
        original_url=url,
        snapshot_url=closest["url"],
        timestamp=closest["timestamp"],
        status_code=closest.get("status"),
        available=True,
    )


def retrieve_prior_versions(url: str, years: int = 5) -> list[WaybackCapture]:
    """Retrieve one Wayback snapshot per year for the past `years` years.

    Walks backward year by year from the current year, requesting the nearest
    January 1 snapshot. Skips years with no available snapshot.

    Returns a list of WaybackCapture objects sorted newest-first.
    Rate-limits at _REQUEST_DELAY_S between requests.

    Arguments:
        url   -- original URL to retrieve prior versions of
        years -- how many calendar years back to look (default 5)
    """
    current_year = datetime.now(UTC).year
    captures: list[WaybackCapture] = []

    for i in range(years):
        year = current_year - i
        timestamp = f"{year}0101120000"
        try:
            data = _get_availability(url, timestamp)
            closest = data.get("archived_snapshots", {}).get("closest")
            if closest and closest.get("available"):
                captures.append(
                    WaybackCapture(
                        original_url=url,
                        snapshot_url=closest["url"],
                        timestamp=closest["timestamp"],
                        status_code=closest.get("status"),
                        available=True,
                    )
                )
        except requests.RequestException as exc:
            log.warning(
                "Wayback availability check failed for %s year %d: %s", url, year, exc
            )
        if i < years - 1:
            time.sleep(_REQUEST_DELAY_S)

    return captures
