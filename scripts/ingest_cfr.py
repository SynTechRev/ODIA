"""CFR (Code of Federal Regulations) ingestion script.

Fetches targeted CFR sections from the eCFR Renderer API
(www.ecfr.gov) and writes data/legal_corpora/cfr/<title>_part<part>.json
in the schema expected by odia_legal.corpus.CFRLoader.

Priority sections cover:
  2 CFR Part 200  — Uniform Administrative Requirements (grants, subrecipients,
                    procurement, internal controls, equipment)
  28 CFR Part 23  — Criminal Intelligence Systems (ALPR / surveillance data rules)

Usage::

    python scripts/ingest_cfr.py                     # fetch all
    python scripts/ingest_cfr.py --dry-run           # print URLs, skip fetch
    python scripts/ingest_cfr.py --title 2 --part 200
    python scripts/ingest_cfr.py --delay 1.5

Output: data/legal_corpora/cfr/title2_part200.json, title28_part23.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print(
        "ERROR: Missing dependencies. Run: pip install requests beautifulsoup4",
        file=sys.stderr,
    )
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ingest_cfr")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUT = _REPO_ROOT / "data" / "legal_corpora" / "cfr"

# eCFR renderer API — returns enhanced HTML with section content
_ECFR_API = (
    "https://www.ecfr.gov/api/renderer/v1/content/enhanced"
    "/{date}/title-{title}?part={part}&section={section}"
)
_ECFR_DATE = "2024-01-01"  # stable snapshot date

_USER_AGENT = (
    "ODIA-Legal-Corpus-Ingestor/1.0 "
    "(https://github.com/SynTechRev/ODIA; civic accountability research)"
)

TODAY = date.today().isoformat()


# ---------------------------------------------------------------------------
# Section manifest
# ---------------------------------------------------------------------------


@dataclass
class CFRSectionSpec:
    section: str  # e.g. "200.303"
    title: str  # human-readable title
    notes: str | None = None


@dataclass
class CFRPartSpec:
    cfr_title: int  # e.g. 2
    cfr_part: int  # e.g. 200
    corpus_id: str  # e.g. "cfr_2_200"
    part_name: str  # e.g. "Uniform Administrative Requirements"
    output_file: str  # e.g. "title2_part200.json"
    sections: list[CFRSectionSpec] = field(default_factory=list)


_PARTS: list[CFRPartSpec] = [
    # ------------------------------------------------------------------ #
    # 2 CFR Part 200 — Uniform Administrative Requirements for Grants     #
    # ------------------------------------------------------------------ #
    CFRPartSpec(
        cfr_title=2,
        cfr_part=200,
        corpus_id="cfr_2_200",
        part_name="Uniform Administrative Requirements, Cost Principles, and Audit Requirements for Federal Awards",
        output_file="title2_part200.json",
        sections=[
            CFRSectionSpec(
                "200.1",
                "Definitions",
                notes="All key terms for federal grant compliance",
            ),
            CFRSectionSpec("200.2", "Applicability"),
            CFRSectionSpec("200.100", "Purpose of this part"),
            CFRSectionSpec("200.101", "Applicability of this part"),
            CFRSectionSpec("200.203", "Notices of funding opportunities"),
            CFRSectionSpec(
                "200.303",
                "Internal controls",
                notes="Requires internal controls over federal awards consistent with COSO framework",
            ),
            CFRSectionSpec("200.305", "Payment"),
            CFRSectionSpec("200.313", "Equipment"),
            CFRSectionSpec("200.315", "Intangible property"),
            CFRSectionSpec(
                "200.318",
                "General procurement standards",
                notes="All procurement transactions must be conducted in a manner providing full and open competition",
            ),
            CFRSectionSpec("200.319", "Competition"),
            CFRSectionSpec("200.320", "Methods of procurement to be followed"),
            CFRSectionSpec("200.326", "Contract provisions"),
            CFRSectionSpec(
                "200.330",
                "Requirements for pass-through entities",
                notes="Subrecipient monitoring and management requirements",
            ),
            CFRSectionSpec("200.331", "Subrecipient and contractor determinations"),
            CFRSectionSpec(
                "200.332",
                "Requirements for subrecipients",
                notes="Financial and programmatic reporting for subrecipients",
            ),
            CFRSectionSpec("200.403", "Factors affecting allowability of costs"),
            CFRSectionSpec("200.431", "Compensation — fringe benefits"),
            CFRSectionSpec(
                "200.447", "Defense and prosecution of criminal and civil proceedings"
            ),
            CFRSectionSpec(
                "200.501",
                "Audit requirements",
                notes="Single audit requirements for non-federal entities expending $750K+ per year",
            ),
            CFRSectionSpec("200.502", "Basis for determining audit requirements"),
        ],
    ),
    # ------------------------------------------------------------------ #
    # 28 CFR Part 23 — Criminal Intelligence Systems                      #
    # ------------------------------------------------------------------ #
    CFRPartSpec(
        cfr_title=28,
        cfr_part=23,
        corpus_id="cfr_28_23",
        part_name="Criminal Intelligence Systems Operating Policies",
        output_file="title28_part23.json",
        sections=[
            CFRSectionSpec(
                "23.3",
                "Definitions",
                notes="Defines 'criminal intelligence information', 'intelligence system', 'participating agency'",
            ),
            CFRSectionSpec(
                "23.20",
                "Operating principles",
                notes="No criminal intelligence file may be maintained without reasonable suspicion of criminal activity",
            ),
            CFRSectionSpec(
                "23.30",
                "Inquiry, dissemination and security of criminal intelligence information",
                notes="Access controls and security requirements for intelligence data",
            ),
            CFRSectionSpec("23.40", "Funding guidelines and required certifications"),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------


class ECFRFetcher:
    def __init__(self, delay: float = 1.5, dry_run: bool = False):
        self.delay = delay
        self.dry_run = dry_run
        self._session = requests.Session()
        self._session.headers["User-Agent"] = _USER_AGENT
        self._session.headers["Accept"] = "text/html"

    def fetch_section(self, cfr_title: int, cfr_part: int, section: str) -> str | None:
        url = _ECFR_API.format(
            date=_ECFR_DATE,
            title=cfr_title,
            part=cfr_part,
            section=section,
        )
        if self.dry_run:
            log.info("[DRY RUN] %s", url)
            return f"[DRY RUN — {cfr_title} C.F.R. § {section}]"

        log.info("Fetching %d C.F.R. § %s …", cfr_title, section)
        try:
            resp = self._session.get(url, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            log.warning("  FAIL: %s", exc)
            return None
        finally:
            time.sleep(self.delay)

        return _extract_cfr_text(resp.text, section)

    def close(self) -> None:
        self._session.close()


def _extract_cfr_text(html: str, section: str) -> str | None:
    """Extract statute text from eCFR renderer HTML response."""
    soup = BeautifulSoup(html, "html.parser")

    # eCFR renderer: <div class="section" id="200.1"> — dots in id are invalid CSS
    # so use soup.find() instead of css select.
    el = soup.find("div", class_="section", id=section)
    if el is None:
        el = soup.find("div", class_="section")
    if el is None:
        for div in soup.find_all("div"):
            text = div.get_text(separator="\n", strip=True)
            if len(text) > 100:
                return text
        return None

    return el.get_text(separator="\n", strip=True) or None


# ---------------------------------------------------------------------------
# Main ingestion logic
# ---------------------------------------------------------------------------


def ingest_part(spec: CFRPartSpec, fetcher: ECFRFetcher, out_dir: Path) -> int:
    """Fetch all sections for one CFR part. Returns count fetched."""
    records = []
    for sec in spec.sections:
        text = fetcher.fetch_section(spec.cfr_title, spec.cfr_part, sec.section)
        if text is None:
            log.warning(
                "  Skipping %d CFR § %s (fetch failed)", spec.cfr_title, sec.section
            )
            continue
        record = {
            "section": sec.section,
            "title": sec.title,
            "text": text,
            "url": (
                f"https://www.ecfr.gov/current/title-{spec.cfr_title}"
                f"/subtitle-A/chapter-II/part-{spec.cfr_part}/section-{sec.section}"
            ),
        }
        if sec.notes:
            record["notes"] = sec.notes
        records.append(record)

    output = {
        "code_id": spec.corpus_id,
        "code_name": f"{spec.cfr_title} C.F.R. Part {spec.cfr_part} — {spec.part_name}",
        "cfr_title": spec.cfr_title,
        "cfr_part": spec.cfr_part,
        "source_url": f"https://www.ecfr.gov/current/title-{spec.cfr_title}/part-{spec.cfr_part}",
        "as_of": TODAY,
        "sections": records,
    }

    out_path = out_dir / spec.output_file
    out_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info(
        "Wrote %d C.F.R. Part %d (%d sections) → %s",
        spec.cfr_title,
        spec.cfr_part,
        len(records),
        out_path,
    )
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CFR sections from eCFR")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--title", type=int, default=None, help="CFR title (default: all)"
    )
    parser.add_argument(
        "--part", type=int, default=None, help="CFR part (default: all)"
    )
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    parts_to_run = [
        p
        for p in _PARTS
        if (args.title is None or p.cfr_title == args.title)
        and (args.part is None or p.cfr_part == args.part)
    ]

    fetcher = ECFRFetcher(delay=args.delay, dry_run=args.dry_run)
    total = 0
    try:
        for spec in parts_to_run:
            log.info("=== %d C.F.R. Part %d ===", spec.cfr_title, spec.cfr_part)
            total += ingest_part(spec, fetcher, out_dir)
    finally:
        fetcher.close()

    log.info("Done. Total sections fetched: %d", total)


if __name__ == "__main__":
    main()
