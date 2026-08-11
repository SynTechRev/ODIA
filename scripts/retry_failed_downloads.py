"""retry_failed_downloads.py — Retry failed attachment downloads from a retrieval manifest.

Reads the `failed_files` list written by LegistarAdapter.retrieve_corpus() and
attempts to re-download each one. On success the entry moves from `failed_files`
to `files` in the manifest. The manifest is updated in-place at the end.

Usage:
    python scripts/retry_failed_downloads.py
    python scripts/retry_failed_downloads.py --manifest data/retrieved/retrieval_manifest.json
    python scripts/retry_failed_downloads.py --dry-run
    python scripts/retry_failed_downloads.py --output-dir data/retrieved
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("retry_failed_downloads")

_DEFAULT_MANIFEST = _REPO_ROOT / "data" / "retrieved" / "retrieval_manifest.json"
_TIMEOUT = 30
_RETRY_BACKOFF = [2, 5, 10]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dest: Path) -> Path:
    try:
        import requests
    except ImportError as exc:
        raise ImportError("requests is required: pip install requests") from exc

    filename = Path(urlparse(url).path).name or "attachment"
    if dest.is_dir():
        dest = dest / filename

    dest.parent.mkdir(parents=True, exist_ok=True)

    for attempt, backoff in enumerate(_RETRY_BACKOFF):
        try:
            resp = requests.get(url, timeout=_TIMEOUT, stream=True)
            if resp.status_code == 429:
                logger.warning("Rate limited — sleeping %ds", backoff)
                time.sleep(backoff)
                continue
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return dest
        except Exception as exc:
            if attempt == len(_RETRY_BACKOFF) - 1:
                raise
            logger.warning(
                "Attempt %d/%d failed: %s", attempt + 1, len(_RETRY_BACKOFF), exc
            )
            time.sleep(backoff)

    raise RuntimeError(f"All retries exhausted for {url}")


def retry_manifest(
    manifest_path: Path,
    output_dir: Path,
    dry_run: bool,
) -> None:
    if not manifest_path.exists():
        sys.exit(f"ERROR: manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failed = manifest.get("failed_files", [])

    if not failed:
        logger.info("No failed files in manifest — nothing to retry.")
        return

    logger.info(
        "Manifest: %s | failed_files to retry: %d",
        manifest_path.name,
        len(failed),
    )

    if dry_run:
        logger.info("DRY-RUN — would retry:")
        for i, entry in enumerate(failed, 1):
            logger.info(
                "  [%d/%d] %s\n         url: %s\n         error was: %s",
                i,
                len(failed),
                entry.get("attachment_name", "?"),
                entry.get("source_url", "?"),
                entry.get("error", "?"),
            )
        return

    recovered: list[dict] = []
    still_failed: list[dict] = []

    for i, entry in enumerate(failed, 1):
        url = entry.get("source_url", "")
        name = entry.get("attachment_name", "attachment")
        matter_id = entry.get("matter_id")
        matter_title = entry.get("matter_title", "")

        logger.info("[%d/%d] %s", i, len(failed), name[:80])

        if not url:
            logger.warning("  Skipping — no source_url in entry")
            still_failed.append(entry)
            continue

        dest = output_dir / (Path(urlparse(url).path).name or "attachment")

        try:
            saved_path = _download(url, dest)
            sha = _sha256_file(saved_path)
            recovered.append(
                {
                    "matter_id": matter_id,
                    "matter_title": matter_title,
                    "attachment_name": name,
                    "local_path": str(saved_path),
                    "sha256": sha,
                    "source_url": url,
                }
            )
            logger.info("  OK → %s", saved_path.name)
        except Exception as exc:
            logger.warning("  FAILED: %s", exc)
            entry["error"] = str(exc)
            still_failed.append(entry)

    # Update manifest
    manifest["files"].extend(recovered)
    manifest["downloaded_count"] = len(manifest["files"])
    manifest["failed_files"] = still_failed
    manifest["failed_count"] = len(still_failed)

    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )

    logger.info("")
    logger.info("=" * 60)
    logger.info(
        "Recovered: %d  |  Still failed: %d  |  Manifest updated.",
        len(recovered),
        len(still_failed),
    )
    if recovered:
        logger.info("")
        logger.info("Next — ingest recovered files:")
        logger.info(
            "  python scripts/bulk_ingest.py --corpus data --folder retrieved --jurisdiction <slug>"
        )


def main() -> None:
    p = argparse.ArgumentParser(
        prog="retry_failed_downloads",
        description="Retry failed attachment downloads from a Legistar retrieval manifest.",
    )
    p.add_argument(
        "--manifest",
        default=str(_DEFAULT_MANIFEST),
        metavar="PATH",
        help=f"Path to retrieval_manifest.json (default: {_DEFAULT_MANIFEST})",
    )
    p.add_argument(
        "--output-dir",
        default=str(_DEFAULT_MANIFEST.parent),
        metavar="DIR",
        help="Directory to save re-downloaded files (default: same as manifest)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be retried without downloading",
    )
    args = p.parse_args()

    retry_manifest(
        manifest_path=Path(args.manifest),
        output_dir=Path(args.output_dir),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
