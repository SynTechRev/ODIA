"""Gig economy URL discovery and PDF harvest for CONTRA corpus expansion.

Targets the four zero-doc gig economy entities:
  - Lyft Inc.              (lyft.com)
  - DoorDash Inc.          (doordash.com)
  - Maplebear Inc.         (instacart.com, instacartads.com, carrotads.com)
  - Grubhub Holdings       (grubhub.com, seamless.com)

Uses Wayback Machine CDX API to enumerate archived legal document URLs,
then downloads PDFs (and HTML-to-PDF conversion candidates) into the
CONTRA corpus folder structure. Writes a manifest compatible with
contra_batch_ingest.py for pipeline ingestion.

Usage:
    python scripts/contra_gig_harvest.py --dry-run      # count only, no download
    python scripts/contra_gig_harvest.py                # full harvest all 4 entities
    python scripts/contra_gig_harvest.py --entity lyft  # single entity
    python scripts/contra_gig_harvest.py --manifest-out data/manifests/gig_harvest_YYYY-MM-DD.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parents[1]

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_CORPUS_ROOT = Path(r"D:\CONTRA Contract Corpus")
_CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
_WB_PREFIX = "https://web.archive.org/web/"

# ── Target entity definitions ────────────────────────────────────────────────


class GigTarget(NamedTuple):
    entity_name: str
    entity_slug: str
    corporate_family: str
    corpus_folder: str  # relative to _CORPUS_ROOT
    domains: list[str]
    url_path_hints: list[str]
    priority: str
    direct_urls: list[
        str
    ] = []  # fallback: canonical known legal page URLs (no CDX needed)


_GIG_TARGETS: list[GigTarget] = [
    GigTarget(
        entity_name="Lyft Inc.",
        entity_slug="lyft_inc",
        corporate_family="Lyft",
        corpus_folder="Lyft",
        domains=["lyft.com"],
        url_path_hints=[
            "/terms",
            "/privacy",
            "/legal",
            "/arbitration",
            "/terms-of-service",
            "/privacy-policy",
            "/driver-terms",
            "/lyft-driver-services-agreement",
            "/community-guidelines",
            "/accessibility",
            "/terms/us",
        ],
        priority="HIGH",
    ),
    GigTarget(
        entity_name="DoorDash Inc.",
        entity_slug="doordash_inc",
        corporate_family="DoorDash",
        corpus_folder="DoorDash",
        domains=["doordash.com", "help.doordash.com"],
        url_path_hints=[
            "/terms",
            "/privacy",
            "/legal",
            "/about/legal",
            "/consumers/s/article/consumer-terms-of-service",
            "/dashers/s/article/dasher-terms-of-service",
        ],
        priority="HIGH",
        direct_urls=[
            "https://help.doordash.com/consumers/s/article/consumer-terms-of-service",
            "https://help.doordash.com/consumers/s/article/doordash-privacy-policy",
            "https://help.doordash.com/consumers/s/article/doordash-commercial-terms-of-service",
            "https://help.doordash.com/dashers/s/article/dasher-terms-of-service",
            "https://help.doordash.com/dashers/s/article/dasher-privacy-policy",
            "https://help.doordash.com/merchants/s/article/merchant-terms-of-service",
            "https://www.doordash.com/terms/",
            "https://www.doordash.com/privacy/",
        ],
    ),
    GigTarget(
        entity_name="Maplebear Inc.",
        entity_slug="maplebear_inc",
        corporate_family="Instacart",
        corpus_folder="Instacart",
        domains=["instacart.com", "instacartads.com", "carrotads.com"],
        url_path_hints=[
            "/terms",
            "/privacy",
            "/legal",
            "/terms-of-service",
            "/privacy-policy",
            "/shopper-agreement",
            "/terms/shopper",
            "/legal/terms",
            "/legal/privacy",
        ],
        priority="HIGH",
        direct_urls=[
            "https://www.instacart.com/terms",
            "https://www.instacart.com/privacy_policy",
            "https://www.instacart.com/shopper-terms",
            "https://www.instacart.com/legal",
            "https://www.instacart.com/privacy",
            "https://instacartads.com/advertising-terms",
            "https://www.instacart.com/help/section/360009947932",
        ],
    ),
    GigTarget(
        entity_name="Grubhub Holdings LLC",
        entity_slug="grubhub_holdings",
        corporate_family="Grubhub",
        corpus_folder="Grubhub",
        domains=["grubhub.com", "seamless.com"],
        url_path_hints=[
            "/legal",
            "/privacy",
            "/terms",
            "/about/legal",
            "/about/privacy",
            "/about/terms",
            "/legal/privacy-policy",
            "/legal/terms-of-use",
            "/legal/driver-terms",
            "/legal/restaurant-terms",
        ],
        priority="HIGH",
        direct_urls=[
            "https://www.grubhub.com/legal/terms-of-use",
            "https://www.grubhub.com/legal/privacy-policy",
            "https://www.grubhub.com/legal/driver-terms",
            "https://www.grubhub.com/legal/restaurant-terms",
            "https://www.seamless.com/legal/terms-of-use",
            "https://www.seamless.com/legal/privacy-policy",
        ],
    ),
]

# ── Reject patterns (mirrors contra_new_pdf_finder.py) ───────────────────────

_REJECT_RE = re.compile(
    r"apache\.licen|w3c\.process|annual\.report|press\.release|investor"
    r"|earnings|proxy|soc2\.report|audit\.report|white\.paper|case\.study"
    r"|accessibility|icon|logo|wcag|section\.508|en\.301|w-9|w9\.form"
    r"|tax\.form|pricing\.guide|price\.guide|code\.of\.conduct"
    r"|meet\.and\.confer|fraud\.article|blog|newsroom|careers|jobs|hiring",
    re.IGNORECASE,
)

_LEGAL_RE = re.compile(
    r"terms?[\-_./]?(?:of[\-_.]?service|of[\-_.]?use|and[\-_.]?conditions|agreement)?"
    r"|privacy[\-_./]?(?:policy|notice|statement)?"
    r"|arbitration|data[\-_./]?(?:processing|sharing|use)"
    r"|user[\-_./]?agreement|service[\-_./]?agreement|driver[\-_.]?agreement"
    r"|shopper[\-_.]?agreement|dasher[\-_.]?agreement"
    r"|community[\-_.]?guidelines|legal[\-_./]?notice",
    re.IGNORECASE,
)


# Doc type inference
def _infer_doc_type(url: str, title: str = "") -> str:
    s = (url + " " + title).lower()
    if re.search(r"arbitrat", s):
        return "arbitration_agreement"
    if re.search(r"privacy|gdpr|ccpa", s):
        return "privacy_notice"
    if re.search(r"terms|tos|service|use|agreement|condition", s):
        return "tos"
    if re.search(r"community|guideline|policy", s):
        return "policy"
    return "tos"


def _cdx_search(domain: str, path_hint: str, session) -> list[dict]:
    """Single CDX query for one domain+path combo. Returns list of snapshot dicts."""
    url_pattern = f"https://{domain}{path_hint}*"
    params = {
        "url": url_pattern,
        "output": "json",
        "fl": "original,timestamp,statuscode,mimetype",
        "collapse": "urlkey",
        "filter": "statuscode:200",
        "limit": "50",
        "from": "20200101",
    }
    try:
        resp = session.get(_CDX_ENDPOINT, params=params, timeout=20)
        if resp.status_code == 429:
            time.sleep(15)
            resp = session.get(_CDX_ENDPOINT, params=params, timeout=20)
        resp.raise_for_status()
        rows = resp.json()
        if not rows or len(rows) < 2:
            return []
        header, *data = rows
        return [dict(zip(header, row, strict=False)) for row in data]
    except Exception:
        return []


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _existing_hashes(db_path: str) -> set[str]:
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
        )
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT document_hash FROM commercial_documents")
            ).fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()


def harvest_entity(
    target: GigTarget, db_path: str, dry_run: bool, session
) -> list[dict]:
    """Discover and download legal documents for one gig entity."""

    print(f"\n  [{target.entity_name}]")
    corpus_dir = _CORPUS_ROOT / target.corpus_folder
    if not dry_run:
        corpus_dir.mkdir(parents=True, exist_ok=True)

    existing = _existing_hashes(db_path)
    discovered: list[dict] = []
    seen_urls: set[str] = set()

    for domain in target.domains:
        for hint in target.url_path_hints:
            snapshots = _cdx_search(domain, hint, session)
            time.sleep(0.4)

            for snap in snapshots:
                url = snap.get("original", "")
                mime = snap.get("mimetype", "")
                ts = snap.get("timestamp", "")

                if url in seen_urls:
                    continue
                if _REJECT_RE.search(url):
                    continue

                # Accept PDFs or HTML legal pages
                is_pdf = "pdf" in mime.lower() or url.lower().endswith(".pdf")
                is_html = "html" in mime.lower() or (
                    not is_pdf and _LEGAL_RE.search(url)
                )

                if not (is_pdf or is_html):
                    continue

                seen_urls.add(url)

                wb_url = f"{_WB_PREFIX}{ts}/{url}" if ts else url
                doc_type = _infer_doc_type(url)

                discovered.append(
                    {
                        "entity_name": target.entity_name,
                        "entity_id_slug": target.entity_slug,
                        "corporate_family": target.corporate_family,
                        "source_url": wb_url,
                        "original_url": url,
                        "doc_type": doc_type,
                        "mime_type": mime,
                        "is_pdf": is_pdf,
                        "wayback_ts": ts,
                        "needs_review": False,
                    }
                )

    # Direct URL fallback — use known canonical URLs when CDX returns nothing
    if not discovered and target.direct_urls:
        print(f"    CDX empty — falling back to {len(target.direct_urls)} direct URLs")
        for url in target.direct_urls:
            if url in seen_urls:
                continue
            if _REJECT_RE.search(url):
                continue
            seen_urls.add(url)
            doc_type = _infer_doc_type(url)
            is_pdf = url.lower().endswith(".pdf")
            discovered.append(
                {
                    "entity_name": target.entity_name,
                    "entity_id_slug": target.entity_slug,
                    "corporate_family": target.corporate_family,
                    "source_url": url,
                    "original_url": url,
                    "doc_type": doc_type,
                    "mime_type": "application/pdf" if is_pdf else "text/html",
                    "is_pdf": is_pdf,
                    "wayback_ts": "",
                    "needs_review": False,
                }
            )

    print(f"    Discovered: {len(discovered)} candidates")

    if dry_run:
        return discovered

    # Download PDFs as binary; HTML pages as extracted plain text (.txt)
    # .txt is natively supported by the ODIA document_loader and contra_batch_ingest
    manifest_entries = []
    for item in discovered:
        path_part = urlparse(item["original_url"]).path.strip("/")
        slug = re.sub(r"[^\w\-]", "_", path_part)[:60] or "document"

        if item["is_pdf"]:
            fname = slug + ".pdf"
        else:
            fname = slug + ".txt"

        dest = corpus_dir / fname

        if dest.exists():
            fhash = _sha256_file(dest)
            if fhash in existing:
                item["status"] = "dup_existing"
                continue

        try:
            r = session.get(item["source_url"], timeout=30, stream=True)
            r.raise_for_status()

            if item["is_pdf"]:
                with dest.open("wb") as f:
                    for chunk in r.iter_content(65536):
                        f.write(chunk)
            else:
                # HTML → extract clean text via BeautifulSoup
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(r.content, "html.parser")
                    # Remove nav, footer, script, style
                    for tag in soup(
                        ["nav", "footer", "script", "style", "header", "aside"]
                    ):
                        tag.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                    # Require meaningful legal text (min 500 chars)
                    if len(text) < 500:
                        item["status"] = "skip_too_short"
                        continue
                except ImportError:
                    # Fallback: strip HTML tags with regex
                    html_content = r.content.decode("utf-8", errors="replace")
                    text = re.sub(r"<[^>]+>", " ", html_content)
                    text = re.sub(r"\s+", " ", text).strip()
                    if len(text) < 500:
                        item["status"] = "skip_too_short"
                        continue

                dest.write_text(text, encoding="utf-8")

            fhash = _sha256_file(dest)
            if fhash in existing:
                dest.unlink()
                item["status"] = "dup_hash"
                continue

            existing.add(fhash)
            item["file_path"] = str(dest)
            item["document_hash"] = fhash
            item["status"] = "new"
            item["needs_review"] = not item["is_pdf"]  # HTML extracts need QC
            manifest_entries.append(item)
            print(f"    + {fname[:60]}" + (" [HTML→txt]" if not item["is_pdf"] else ""))
            time.sleep(0.5)

        except Exception as exc:
            item["status"] = f"error:{exc}"

    return manifest_entries


def main() -> None:
    import requests

    parser = argparse.ArgumentParser(
        description="Gig economy PDF harvest for CONTRA corpus"
    )
    parser.add_argument(
        "--entity",
        choices=["lyft", "doordash", "instacart", "grubhub"],
        default=None,
        help="Harvest single entity only",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--manifest-out", default=None)
    args = parser.parse_args()

    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    entity_suffix = f"_{args.entity}" if args.entity else ""
    manifest_path = (
        Path(args.manifest_out)
        if args.manifest_out
        else (
            _REPO_ROOT
            / "data"
            / "manifests"
            / f"gig_harvest_{date_str}{entity_suffix}.json"
        )
    )

    _ENTITY_MAP = {"lyft": 0, "doordash": 1, "instacart": 2, "grubhub": 3}
    targets = [_GIG_TARGETS[_ENTITY_MAP[args.entity]]] if args.entity else _GIG_TARGETS

    session = requests.Session()
    session.headers["User-Agent"] = "CONTRA-corpus-harvester/1.0 research@odia.internal"

    print(f"GIG ECONOMY HARVEST — {date_str}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Targets: {', '.join(t.entity_name for t in targets)}")
    print("=" * 60)

    all_entries: list[dict] = []
    for target in targets:
        entries = harvest_entity(target, args.db_path, args.dry_run, session)
        all_entries.extend(entries)

    print(f"\n{'─'*60}")
    print(f"Total candidates discovered: {len(all_entries)}")
    new_count = sum(1 for e in all_entries if e.get("status") == "new")
    dup_count = sum(1 for e in all_entries if "dup" in e.get("status", ""))
    html_count = sum(1 for e in all_entries if not e.get("is_pdf"))
    print(f"  New PDFs downloaded : {new_count}")
    print(f"  Duplicates skipped  : {dup_count}")
    print(f"  HTML (review needed): {html_count}")

    if all_entries:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(all_entries, indent=2, default=str), encoding="utf-8"
        )
        print(f"\nManifest saved: {manifest_path}")
        print(
            f"Next step: python scripts/contra_batch_ingest.py --manifest {manifest_path}"
        )


if __name__ == "__main__":
    main()
