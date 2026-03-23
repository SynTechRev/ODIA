"""Legistar API adapter for automated legislative document retrieval.

Legistar is a widely-used legislative management system. Cities expose a public
REST API at https://webapi.legistar.com/v1/{client}/ where {client} is the
city's Legistar subdomain (e.g., "visalia" for visalia.legistar.com).

This adapter wraps the public Legistar REST API to:
  - List legislative matters (bills, contracts, resolutions, ordinances)
  - Get document attachments for each matter
  - Download attachments to a local directory
  - Retrieve full meeting agendas and event items
  - Build a local document corpus ready for ODIA analysis

All HTTP calls use requests with a 30-second timeout and exponential-backoff
retry on transient errors. No authentication is required for public Legistar
endpoints.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

_BASE_URL = "https://webapi.legistar.com/v1/{client}/"
_TIMEOUT = 30  # seconds
_MAX_RETRIES = 3
_RETRY_BACKOFF = [1, 2, 4]  # seconds


def _get(url: str, params: dict | None = None) -> Any:
    """Perform a GET request with retry on transient HTTP errors."""
    try:
        import requests  # type: ignore[import]
    except ImportError as exc:
        raise ImportError("requests is required: pip install requests") from exc

    for attempt, backoff in enumerate(_RETRY_BACKOFF):
        try:
            resp = requests.get(url, params=params, timeout=_TIMEOUT)
            if resp.status_code == 429:
                logger.warning("Rate limited — sleeping %ss", backoff)
                time.sleep(backoff)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            if attempt == _MAX_RETRIES - 1:
                raise
            logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, _MAX_RETRIES, exc)
            time.sleep(backoff)
    raise RuntimeError(f"All retries exhausted for {url}")


def _download_file(url: str, dest: Path) -> Path:
    """Download a file to *dest*, returning the final path."""
    try:
        import requests  # type: ignore[import]
    except ImportError as exc:
        raise ImportError("requests is required: pip install requests") from exc

    resp = requests.get(url, timeout=_TIMEOUT, stream=True)
    resp.raise_for_status()

    # Derive filename from URL or Content-Disposition
    filename = dest.name if dest.suffix else Path(urlparse(url).path).name or "attachment"
    if dest.is_dir():
        dest = dest / filename

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return dest


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _date_str(d: date | str | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, str):
        return d
    return d.strftime("%Y-%m-%d")


class LegistarAdapter:
    """Client for the Legistar public REST API.

    Parameters
    ----------
    client_id:
        The Legistar subdomain for the target city (e.g. ``"visalia"``).
    """

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id.lower().strip()
        self._base = _BASE_URL.format(client=self.client_id)

    def _url(self, path: str) -> str:
        return urljoin(self._base, path.lstrip("/"))

    # ------------------------------------------------------------------
    # Matters (legislative items)
    # ------------------------------------------------------------------

    def list_matters(
        self,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        matter_type: str | None = None,
        top: int = 1000,
    ) -> list[dict[str, Any]]:
        """List legislative matters optionally filtered by date range and type.

        Parameters
        ----------
        start_date, end_date:
            ISO date strings or ``date`` objects limiting ``MatterIntroDate``.
        matter_type:
            Filter by ``MatterTypeName`` (e.g. ``"Contract"``).
        top:
            Maximum number of records (Legistar default is 1000).

        Returns
        -------
        list[dict]
            Raw Legistar matter objects.
        """
        params: dict[str, Any] = {"$top": top}
        filters: list[str] = []
        if start_date:
            filters.append(f"MatterIntroDate ge datetime'{_date_str(start_date)}'")
        if end_date:
            filters.append(f"MatterIntroDate le datetime'{_date_str(end_date)}'")
        if matter_type:
            filters.append(f"MatterTypeName eq '{matter_type}'")
        if filters:
            params["$filter"] = " and ".join(filters)

        return _get(self._url("matters"), params=params)

    def get_matter(self, matter_id: int | str) -> dict[str, Any]:
        """Get a single matter by ID."""
        return _get(self._url(f"matters/{matter_id}"))

    def get_matter_attachments(self, matter_id: int | str) -> list[dict[str, Any]]:
        """Get all document attachments for a matter.

        Returns
        -------
        list[dict]
            Each dict has at least ``MatterAttachmentId``, ``MatterAttachmentName``,
            ``MatterAttachmentHyperlink``.
        """
        return _get(self._url(f"matters/{matter_id}/attachments"))

    # ------------------------------------------------------------------
    # Events (meetings/agendas)
    # ------------------------------------------------------------------

    def list_events(
        self,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        top: int = 200,
    ) -> list[dict[str, Any]]:
        """List meetings/events optionally filtered by date range."""
        params: dict[str, Any] = {"$top": top}
        filters: list[str] = []
        if start_date:
            filters.append(f"EventDate ge datetime'{_date_str(start_date)}'")
        if end_date:
            filters.append(f"EventDate le datetime'{_date_str(end_date)}'")
        if filters:
            params["$filter"] = " and ".join(filters)
        return _get(self._url("events"), params=params)

    def get_event_items(self, event_id: int | str) -> list[dict[str, Any]]:
        """Get agenda items for a specific meeting."""
        return _get(self._url(f"events/{event_id}/eventitems"))

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    def download_attachment(
        self, attachment_url: str, output_dir: str | Path
    ) -> Path:
        """Download a single attachment to *output_dir*.

        Parameters
        ----------
        attachment_url:
            Direct URL to the attachment (from ``MatterAttachmentHyperlink``).
        output_dir:
            Directory to save the file into.

        Returns
        -------
        Path
            Path to the downloaded file.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(urlparse(attachment_url).path).name or "attachment"
        dest = output_dir / filename
        return _download_file(attachment_url, dest)

    # ------------------------------------------------------------------
    # Full corpus retrieval
    # ------------------------------------------------------------------

    def retrieve_corpus(
        self,
        start_date: date | str,
        end_date: date | str,
        output_dir: str | Path,
        matter_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve all documents matching the criteria and save locally.

        Workflow:
        1. List all matters in date range (optionally filtered by type).
        2. For each matter, get attachments.
        3. Download each attachment to *output_dir*.
        4. Return a manifest dict.

        Parameters
        ----------
        start_date, end_date:
            Date range for matter introduction date.
        output_dir:
            Local directory to save downloaded files.
        matter_types:
            Optional list of matter type names to include (e.g.
            ``["Contract", "Resolution"]``). Pass ``None`` to retrieve all types.

        Returns
        -------
        dict
            Manifest with keys: ``client_id``, ``start_date``, ``end_date``,
            ``matter_count``, ``attachment_count``, ``downloaded_count``,
            ``failed_count``, ``files``.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest: dict[str, Any] = {
            "client_id": self.client_id,
            "start_date": _date_str(start_date),
            "end_date": _date_str(end_date),
            "matter_count": 0,
            "attachment_count": 0,
            "downloaded_count": 0,
            "failed_count": 0,
            "files": [],
        }

        types_to_fetch = matter_types or [None]
        matters: list[dict] = []
        for mtype in types_to_fetch:
            try:
                batch = self.list_matters(
                    start_date=start_date,
                    end_date=end_date,
                    matter_type=mtype,
                )
                matters.extend(batch)
            except Exception as exc:
                logger.warning("Failed to list matters (type=%s): %s", mtype, exc)

        manifest["matter_count"] = len(matters)
        logger.info("Found %d matters for %s", len(matters), self.client_id)

        for matter in matters:
            matter_id = matter.get("MatterId") or matter.get("Id")
            if matter_id is None:
                continue
            try:
                attachments = self.get_matter_attachments(matter_id)
            except Exception as exc:
                logger.warning("Failed to get attachments for matter %s: %s", matter_id, exc)
                continue

            manifest["attachment_count"] += len(attachments)

            for att in attachments:
                url = att.get("MatterAttachmentHyperlink") or att.get("Hyperlink") or ""
                name = att.get("MatterAttachmentName") or att.get("Name") or "attachment"
                if not url:
                    continue
                try:
                    dest = self.download_attachment(url, output_dir)
                    manifest["files"].append({
                        "matter_id": matter_id,
                        "matter_title": matter.get("MatterTitle", ""),
                        "attachment_name": name,
                        "local_path": str(dest),
                        "sha256": _sha256_file(dest),
                        "source_url": url,
                    })
                    manifest["downloaded_count"] += 1
                    logger.info("Downloaded: %s", dest.name)
                except Exception as exc:
                    logger.warning("Failed to download %s: %s", url, exc)
                    manifest["failed_count"] += 1

        # Write manifest JSON
        manifest_path = output_dir / "retrieval_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(
            "Retrieval complete: %d downloaded, %d failed",
            manifest["downloaded_count"],
            manifest["failed_count"],
        )
        return manifest

    # ------------------------------------------------------------------
    # City list
    # ------------------------------------------------------------------

    def list_available_clients(self) -> list[dict[str, str]]:
        """Return the curated list of known Legistar cities.

        Reads from ``config/legistar_cities.json`` relative to the package root,
        or returns an empty list if the file is not found.
        """
        candidates = [
            Path(__file__).resolve().parent.parent.parent.parent / "config" / "legistar_cities.json",
            Path(__file__).resolve().parent / "legistar_cities.json",
        ]
        for path in candidates:
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return []


def load_cities() -> list[dict[str, str]]:
    """Load the curated list of known Legistar cities from config/legistar_cities.json."""
    config_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "legistar_cities.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return []
