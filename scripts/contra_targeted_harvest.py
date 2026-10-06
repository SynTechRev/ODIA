"""Targeted direct-URL harvest for specific gig economy legal documents.

Fetches known canonical legal page URLs directly (no Wayback CDX), converts
HTML to clean text, and writes a manifest for contra_batch_ingest.py.

Usage:
    python scripts/contra_targeted_harvest.py [--dry-run] [--entity doordash|instacart]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CORPUS_ROOT = Path(r"D:\CONTRA Contract Corpus")
_MIN_CHARS = 500

# ── Target definitions ────────────────────────────────────────────────────────

_TARGETS = [
    {
        "entity_name": "DoorDash Inc.",
        "entity_id_slug": "doordash_inc",
        "corporate_family": "DoorDash",
        "corpus_folder": "DoorDash",
        "urls": [
            ("https://www.doordash.com/terms/", "terms_of_service"),
            ("https://www.doordash.com/privacy/", "privacy_notice"),
            (
                "https://help.doordash.com/consumers/s/article/doordash-consumer-terms-of-service",
                "terms_of_service",
            ),
            (
                "https://help.doordash.com/consumers/s/article/doordash-privacy-policy",
                "privacy_notice",
            ),
            (
                "https://help.doordash.com/dashers/s/article/dasher-terms-of-service",
                "terms_of_service",
            ),
            (
                "https://help.doordash.com/dashers/s/article/dasher-privacy-policy",
                "privacy_notice",
            ),
            (
                "https://help.doordash.com/merchants/s/article/merchant-terms-of-service",
                "terms_of_service",
            ),
            (
                "https://help.doordash.com/consumers/s/article/doordash-commercial-terms-of-service",
                "terms_of_service",
            ),
        ],
    },
    {
        "entity_name": "Maplebear Inc.",
        "entity_id_slug": "maplebear_inc",
        "corporate_family": "Instacart",
        "corpus_folder": "Instacart",
        "urls": [
            ("https://www.instacart.com/terms", "terms_of_service"),
            ("https://www.instacart.com/privacy_policy", "privacy_notice"),
            ("https://www.instacart.com/shopper-terms", "terms_of_service"),
        ],
    },
]

# ── HTML → text ───────────────────────────────────────────────────────────────


def _html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(
            ["script", "style", "nav", "header", "footer", "meta", "link", "noscript"]
        ):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        return re.sub(r"<[^>]+>", " ", html)


def _slug_from_url(url: str) -> str:
    path = url.rstrip("/").split("?")[0]
    name = path.split("/")[-1] or path.split("/")[-2] or "index"
    name = re.sub(r"[^a-zA-Z0-9_\-]", "-", name)
    return name[:60]


def harvest(entity_filter: str | None = None, dry_run: bool = False) -> list[dict]:
    import requests

    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (compatible; ODIA-Research/1.0; "
        "commercial-contract-corpus-builder)"
    )

    manifest: list[dict] = []
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d")

    for target in _TARGETS:
        slug = target["entity_id_slug"]
        if entity_filter and entity_filter.lower() not in slug.lower():
            continue

        folder = _CORPUS_ROOT / target["corpus_folder"]
        folder.mkdir(parents=True, exist_ok=True)

        print(f"\n  [{target['entity_name']}]")
        fetched = 0

        for url, doc_type in target["urls"]:
            try:
                print(f"    Fetching: {url}")
                if dry_run:
                    print("      [DRY RUN] would fetch")
                    continue

                resp = session.get(url, timeout=20, allow_redirects=True)
                if resp.status_code != 200:
                    print(f"      HTTP {resp.status_code} — skip")
                    time.sleep(1)
                    continue

                ct = resp.headers.get("content-type", "")
                if "html" in ct.lower() or not ct:
                    text = _html_to_text(resp.text)
                else:
                    text = resp.text

                if len(text) < _MIN_CHARS:
                    print(f"      Too short ({len(text)} chars) — skip")
                    time.sleep(1)
                    continue

                doc_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                fname = _slug_from_url(url) + ".txt"
                out_path = folder / fname

                # Check existing files for hash collision (dedup)
                already = False
                for existing in folder.glob("*.txt"):
                    try:
                        h = hashlib.sha256(existing.read_bytes()).hexdigest()
                        if h == doc_hash:
                            print(f"      Duplicate of {existing.name} — skip")
                            already = True
                            break
                    except OSError:
                        pass
                if already:
                    time.sleep(0.5)
                    continue

                out_path.write_text(text, encoding="utf-8")
                print(f"      + {fname} [HTML→txt] ({len(text):,} chars)")
                fetched += 1

                manifest.append(
                    {
                        "entity_name": target["entity_name"],
                        "entity_id_slug": slug,
                        "corporate_family": target["corporate_family"],
                        "source_url": url,
                        "original_url": url,
                        "doc_type": doc_type,
                        "mime_type": "text/plain",
                        "is_pdf": False,
                        "wayback_ts": None,
                        "needs_review": False,
                        "file_path": str(out_path),
                        "document_hash": doc_hash,
                        "status": "new",
                    }
                )
                time.sleep(1.5)

            except Exception as exc:
                print(f"      ERROR: {exc}")
                time.sleep(2)

        print(f"    Fetched {fetched} doc(s)")

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--entity",
        default=None,
        help="Filter by entity slug fragment (doordash|instacart)",
    )
    parser.add_argument("--manifest-out", default=None)
    args = parser.parse_args()

    ts = datetime.now(UTC).strftime("%Y-%m-%d")
    default_manifest = _REPO_ROOT / "data" / "manifests" / f"gig_targeted_{ts}.json"
    out_path = Path(args.manifest_out) if args.manifest_out else default_manifest

    print(f"GIG TARGETED HARVEST — {ts}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    entries = harvest(entity_filter=args.entity, dry_run=args.dry_run)

    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nManifest saved: {out_path}  ({len(entries)} entries)")
        if entries:
            print(
                f"Next step: python scripts/contra_batch_ingest.py --manifest {out_path} --skip-review"
            )
    else:
        print(f"\n[DRY RUN] {len(entries)} entries would be written to {out_path}")


if __name__ == "__main__":
    main()
