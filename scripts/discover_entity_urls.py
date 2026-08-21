"""CONTRA entity URL discovery — Tranche 1 / Design Element 1.

Probes standard legal-document paths for a given entity's root URL, parses
sitemap.xml, and scans homepage footer anchor links.  Outputs a manifest of
candidate URLs for downstream ingest by ingest_commercial_entity.py.

Usage:
    python scripts/discover_entity_urls.py --entity "Google LLC" --root-url https://policies.google.com
    python scripts/discover_entity_urls.py --entity "Comcast / Xfinity" --root-url https://www.xfinity.com --dry-run
    python scripts/discover_entity_urls.py --batch entities.json   # batch mode from JSON

Output:
    cache/{entity_id_slug}/discovered_urls.json
    cache/{entity_id_slug}/discovery_log.json

entities.json format:
    [{"entity_name": "...", "entity_id_slug": "...", "root_url": "..."}]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("contra.discover")

_USER_AGENT = (
    "ODIA-CONTRA-Discovery/3.9 (SynTechRev research; "
    "commercial-contract-corpus; https://github.com/SynTechRev/ODIA)"
)

# Standard paths to probe per entity root
_PROBE_PATHS = [
    "/terms",
    "/terms-of-service",
    "/terms-and-conditions",
    "/tos",
    "/legal",
    "/legal/terms",
    "/policies",
    "/privacy",
    "/privacy-policy",
    "/privacy/policy",
    "/about/privacy",
    "/help/legal",
    "/legal/privacy",
    "/eula",
    "/license",
    "/dispute",
    "/arbitration",
    "/adr",
    "/legal/arbitration",
    "/sitemap.xml",
    "/sitemap_index.xml",
]

# Keywords that indicate a legal/ToS document link
_LEGAL_KEYWORDS = re.compile(
    r"term|condition|privacy|legal|policy|agreement|license|eula|"
    r"dispute|arbitration|service|subscriber|customer|user",
    re.IGNORECASE,
)

# Keywords in link text or href that indicate non-legal links (skip)
_SKIP_KEYWORDS = re.compile(
    r"login|signin|account|cart|shop|buy|store|support|blog|news|"
    r"press|careers|investor|about-us|contact|sitemap\.html",
    re.IGNORECASE,
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = _USER_AGENT
    s.headers["Accept-Language"] = "en-US,en;q=0.9"
    return s


def _is_pdf_url(url: str) -> bool:
    return url.lower().endswith(".pdf")


def _probe_url(session: requests.Session, url: str, timeout: int = 12) -> dict | None:
    """HEAD-probe a URL; return metadata dict or None on failure."""
    try:
        resp = session.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 405:
            resp = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
        if resp.status_code == 200:
            ct = resp.headers.get("Content-Type", "")
            return {
                "url": resp.url,
                "status": resp.status_code,
                "content_type": ct,
                "is_pdf": "pdf" in ct.lower() or _is_pdf_url(resp.url),
                "source": "probe",
            }
        return None
    except Exception as exc:
        log.debug("probe failed %s: %s", url, exc)
        return None


def _parse_sitemap(session: requests.Session, root_url: str) -> list[str]:
    """Fetch sitemap.xml and return legal-document URLs."""
    urls: list[str] = []
    for sitemap_path in ("/sitemap.xml", "/sitemap_index.xml"):
        sitemap_url = root_url.rstrip("/") + sitemap_path
        try:
            resp = session.get(sitemap_url, timeout=15)
            if resp.status_code != 200:
                continue
            # Extract <loc> tags
            locs = re.findall(r"<loc>(.*?)</loc>", resp.text, re.IGNORECASE)
            for loc in locs:
                loc = loc.strip()
                if _LEGAL_KEYWORDS.search(loc) and not _SKIP_KEYWORDS.search(loc):
                    urls.append(loc)
            if urls:
                log.info("Sitemap yielded %d candidate URLs", len(urls))
                break
        except Exception as exc:
            log.debug("sitemap fetch failed %s: %s", sitemap_url, exc)
    return urls


def _parse_footer_links(session: requests.Session, root_url: str) -> list[str]:
    """Fetch homepage and extract footer anchor links pointing to legal docs."""
    urls: list[str] = []
    try:
        resp = session.get(root_url, timeout=20)
        if resp.status_code != 200:
            return urls
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find footer elements
        footer_candidates = (
            soup.find_all("footer")
            or soup.find_all(attrs={"class": re.compile(r"footer|legal|bottom", re.I)})
            or [soup]
        )

        seen: set[str] = set()
        for container in footer_candidates:
            for a in container.find_all("a", href=True):
                href = a.get("href", "").strip()
                text = a.get_text(strip=True)
                if not href or href.startswith("#") or href.startswith("javascript"):
                    continue
                if _SKIP_KEYWORDS.search(href) and not _LEGAL_KEYWORDS.search(text):
                    continue
                if not (_LEGAL_KEYWORDS.search(href) or _LEGAL_KEYWORDS.search(text)):
                    continue

                full_url = urljoin(root_url, href)
                # Only same or related domain
                parsed_root = urlparse(root_url)
                parsed_link = urlparse(full_url)
                root_domain = ".".join(parsed_root.netloc.split(".")[-2:])
                link_domain = ".".join(parsed_link.netloc.split(".")[-2:])
                if root_domain not in link_domain and link_domain not in root_domain:
                    continue

                if full_url not in seen:
                    seen.add(full_url)
                    urls.append(full_url)

    except Exception as exc:
        log.debug("footer parse failed %s: %s", root_url, exc)
    return urls


def discover(
    entity_name: str,
    entity_id_slug: str,
    root_url: str,
    dry_run: bool = False,
    pause_sec: float = 3.0,
) -> dict:
    """Run full discovery for one entity. Returns summary dict."""
    cache_dir = Path("cache") / entity_id_slug
    out_file = cache_dir / "discovered_urls.json"
    log_file = cache_dir / "discovery_log.json"

    if not dry_run:
        cache_dir.mkdir(parents=True, exist_ok=True)

    log.info("Discovering: %s (%s)", entity_name, root_url)
    session = _session()
    found: dict[str, dict] = {}

    # Step 1 — probe standard paths
    root = root_url.rstrip("/")
    for path in _PROBE_PATHS:
        url = root + path
        if dry_run:
            log.info("  DRY probe %s", url)
            time.sleep(0.1)
            continue
        result = _probe_url(session, url)
        if result:
            canonical = result["url"]
            if canonical not in found:
                found[canonical] = result
                log.info("  FOUND (probe) %s", canonical)
        time.sleep(pause_sec)

    # Step 2 — sitemap
    if not dry_run:
        sitemap_urls = _parse_sitemap(session, root)
        time.sleep(pause_sec)
        for u in sitemap_urls:
            if u not in found:
                result = _probe_url(session, u)
                if result:
                    found[result["url"]] = dict(result, source="sitemap")
                time.sleep(pause_sec)

    # Step 3 — footer links
    if not dry_run:
        footer_urls = _parse_footer_links(session, root)
        time.sleep(pause_sec)
        for u in footer_urls:
            if u not in found:
                result = _probe_url(session, u)
                if result:
                    found[result["url"]] = dict(result, source="footer")
                time.sleep(pause_sec)

    discovered_list = [
        {"url": url, **meta} for url, meta in found.items()
    ]

    summary = {
        "entity_name": entity_name,
        "entity_id_slug": entity_id_slug,
        "root_url": root_url,
        "total_discovered": len(discovered_list),
        "pdf_count": sum(1 for d in discovered_list if d.get("is_pdf")),
        "html_count": sum(1 for d in discovered_list if not d.get("is_pdf")),
        "urls": discovered_list,
    }

    if not dry_run:
        out_file.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        log_file.write_text(
            json.dumps({"entity": entity_name, "discovered": len(discovered_list)}, indent=2),
            encoding="utf-8",
        )
        log.info("Written: %s (%d URLs)", out_file, len(discovered_list))

    return summary


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    parser = argparse.ArgumentParser(description="CONTRA entity URL discovery")
    parser.add_argument("--entity", default=None, help="Entity canonical name")
    parser.add_argument("--entity-slug", default=None, help="entity_id_slug (snake_case)")
    parser.add_argument("--root-url", default=None, help="Entity root URL")
    parser.add_argument(
        "--batch",
        default=None,
        help="JSON file with list of {entity_name, entity_id_slug, root_url}",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pause", type=float, default=3.0, help="Seconds between requests")
    args = parser.parse_args()

    if args.batch:
        batch_path = Path(args.batch)
        if not batch_path.exists():
            print(f"ERROR: batch file not found: {batch_path}", file=sys.stderr)
            sys.exit(1)
        entities = json.loads(batch_path.read_text(encoding="utf-8"))
    elif args.entity and args.root_url:
        slug = args.entity_slug or args.entity.lower().replace(" ", "_").replace("&", "and").replace("/", "_")
        entities = [{"entity_name": args.entity, "entity_id_slug": slug, "root_url": args.root_url}]
    else:
        parser.print_help()
        sys.exit(1)

    total_found = 0
    for ent in entities:
        summary = discover(
            entity_name=ent["entity_name"],
            entity_id_slug=ent["entity_id_slug"],
            root_url=ent["root_url"],
            dry_run=args.dry_run,
            pause_sec=args.pause,
        )
        total_found += summary["total_discovered"]
        print(
            f"  {ent['entity_name']:<35} {summary['total_discovered']:>3} URLs "
            f"({summary['pdf_count']} PDF, {summary['html_count']} HTML)"
        )

    print(f"\nTotal discovered: {total_found} URLs across {len(entities)} entities")
    if not args.dry_run:
        print("Run next: python scripts/ingest_commercial_entity.py --entity-slug <slug>")


if __name__ == "__main__":
    main()
