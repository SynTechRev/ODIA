"""California code ingestion script.

Fetches targeted California statute sections from leginfo.legislature.ca.gov
and writes them to data/legal_corpora/cal_codes/<code_id>.json in the schema
expected by odia_legal.corpus.CaliforniaCodeLoader.

Priority sections cover:
  Gov. Code  — CPRA (§§ 7920–7931), AB 481 surveillance tech (§§ 36000–36010)
  Pen. Code  — Officer personnel records (§ 832.7–832.8)
  Civ. Code  — ALPR operators (§§ 1798.90.51–1798.90.55)
  Veh. Code  — ALPR law enforcement use (§ 2413)

Usage::

    python scripts/ingest_cal_codes.py                  # fetch all
    python scripts/ingest_cal_codes.py --dry-run        # print URLs, skip fetch
    python scripts/ingest_cal_codes.py --code gov       # fetch Gov. Code only
    python scripts/ingest_cal_codes.py --delay 2.0      # 2s between requests
    python scripts/ingest_cal_codes.py --out /tmp/cal   # custom output dir

Output dir defaults to data/legal_corpora/cal_codes/ relative to the repo root.
Each code produces one JSON file:
    gov_code.json, pen_code.json, civ_code.json, veh_code.json, ...
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
log = logging.getLogger("ingest_cal_codes")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUT = _REPO_ROOT / "data" / "legal_corpora" / "cal_codes"

_LEGINFO_BASE = "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml"

_USER_AGENT = (
    "ODIA-Legal-Corpus-Ingestor/1.0 "
    "(https://github.com/SynTechRev/ODIA; civic accountability research)"
)

TODAY = date.today().isoformat()


# ---------------------------------------------------------------------------
# Section manifest — (section_number, title, notes)
# ---------------------------------------------------------------------------


@dataclass
class SectionSpec:
    section: str
    title: str
    notes: str | None = None


@dataclass
class CodeSpec:
    code_id: str
    code_name: str
    law_code: str  # leginfo URL parameter
    output_file: str
    sections: list[SectionSpec] = field(default_factory=list)


_CODES: list[CodeSpec] = [
    # ------------------------------------------------------------------ #
    # California Government Code — CPRA + AB 481                          #
    # ------------------------------------------------------------------ #
    CodeSpec(
        code_id="cal_gov_code",
        code_name="California Government Code",
        law_code="GOV",
        output_file="gov_code.json",
        sections=[
            # CPRA — General Provisions
            SectionSpec("7920.000", "Legislative findings and intent"),
            SectionSpec("7920.005", "Construction of chapter"),
            SectionSpec("7920.100", "Application to state and local agencies"),
            SectionSpec("7920.500", "Definitions — general"),
            SectionSpec("7920.505", "Definition: agency"),
            SectionSpec("7920.510", "Definition: chief executive officer"),
            SectionSpec("7920.515", "Definition: contract"),
            SectionSpec("7920.525", "Definition: local agency"),
            SectionSpec("7920.530", "Definition: person"),
            SectionSpec("7920.535", "Definition: public agency"),
            SectionSpec("7920.540", "Definition: public records"),
            SectionSpec("7920.545", "Definition: state agency"),
            SectionSpec("7920.550", "Definition: writing"),
            # CPRA — Public Access
            SectionSpec("7921.000", "Public records open to inspection"),
            SectionSpec("7921.300", "Request requirements"),
            SectionSpec("7922.000", "Public interest balancing test (catch-all)"),
            SectionSpec("7922.100", "Agency response obligations"),
            SectionSpec("7922.500", "Right of access; 10-day response period"),
            SectionSpec("7922.525", "Right of inspection"),
            SectionSpec("7922.530", "Right to copy; fees"),
            SectionSpec("7922.535", "Ten-calendar-day response period"),
            SectionSpec("7922.540", "Unusual-circumstances extension"),
            SectionSpec("7922.545", "Rolling production of records"),
            SectionSpec("7922.600", "Assistance to requestors"),
            SectionSpec("7922.610", "No disclosure required for prior requests"),
            SectionSpec("7922.615", "Agency regulations governing access"),
            SectionSpec("7922.630", "Electronic records"),
            # CPRA — Exemptions
            SectionSpec("7923.600", "Enumerated exemptions — general"),
            SectionSpec("7923.610", "Preliminary drafts, notes, memoranda"),
            SectionSpec("7923.620", "Pending litigation records"),
            SectionSpec("7923.625", "Personnel, medical files"),
            SectionSpec("7923.630", "Real estate appraisals"),
            SectionSpec("7923.640", "Third-party contract bid data"),
            SectionSpec(
                "7923.650",
                "Law enforcement investigative records",
                notes="Most-litigated CPRA exemption; covers ongoing investigations",
            ),
            SectionSpec("7923.655", "Test questions"),
            SectionSpec("7923.660", "Real estate negotiations"),
            SectionSpec("7923.670", "Juvenile criminal records"),
            SectionSpec("7923.700", "Attorney-client privilege communications"),
            SectionSpec("7923.800", "Public assistance recipient names"),
            SectionSpec("7923.820", "Air quality records — expressly public"),
            SectionSpec("7923.825", "Employment contracts — must be disclosed"),
            SectionSpec("7923.885", "Home address of public officials"),
            # CPRA — Enforcement
            SectionSpec("7923.100", "Injunctive or declaratory relief"),
            SectionSpec("7923.115", "Judicial enforcement action"),
            SectionSpec("7923.120", "Attorney fees to prevailing party"),
            # Employee salary disclosure
            SectionSpec(
                "7927.700",
                "Employee names and salaries — must be disclosed",
                notes="Disclosure-affirmative: name/position/salary public for every employee",
            ),
            SectionSpec("7927.705", "Waiver of exemption by voluntary disclosure"),
            # AB 481 — Surveillance Technology
            SectionSpec(
                "36000",
                "Military equipment — definitions",
                notes="AB 481: defines 'military equipment' for local policy purposes",
            ),
            SectionSpec(
                "36001",
                "Military equipment — ordinance requirement",
                notes="AB 481: agencies must adopt use policy before acquiring equipment",
            ),
            SectionSpec(
                "36002",
                "Military equipment — annual report requirement",
                notes="AB 481: annual community report on use, complaints, violations",
            ),
            SectionSpec("36003", "Military equipment — approval by governing body"),
            SectionSpec("36004", "Military equipment — renewal of authorization"),
            SectionSpec("36005", "Military equipment — policy contents"),
            SectionSpec(
                "36010",
                "Military equipment — compliance and violations",
            ),
        ],
    ),
    # ------------------------------------------------------------------ #
    # California Penal Code — Officer personnel records                   #
    # ------------------------------------------------------------------ #
    CodeSpec(
        code_id="cal_pen_code",
        code_name="California Penal Code",
        law_code="PEN",
        output_file="pen_code.json",
        sections=[
            SectionSpec(
                "832.7",
                "Peace officer personnel records — public disclosure",
                notes="SB 1421: specified records now public (use of force, sexual assault, dishonesty)",
            ),
            SectionSpec(
                "832.8",
                "Peace officer personnel records — confidential",
                notes="Records not listed in 832.7 remain confidential",
            ),
            SectionSpec(
                "832.9",
                "Peace officer records — disclosure process",
            ),
            SectionSpec(
                "13300",
                "Local criminal history — access restrictions",
            ),
            SectionSpec(
                "13301",
                "Criminal history — authorized disclosures",
            ),
        ],
    ),
    # ------------------------------------------------------------------ #
    # California Civil Code — ALPR                                        #
    # ------------------------------------------------------------------ #
    CodeSpec(
        code_id="cal_civ_code",
        code_name="California Civil Code",
        law_code="CIV",
        output_file="civ_code.json",
        sections=[
            SectionSpec(
                "1798.90.51",
                "ALPR — definitions",
                notes="SB 34: defines ALPR system and data",
            ),
            SectionSpec(
                "1798.90.52",
                "ALPR — operator requirements",
                notes="SB 34: operators must have privacy/usage policy",
            ),
            SectionSpec(
                "1798.90.53",
                "ALPR — data retention limits",
                notes="SB 34: 60-day retention limit for ALPR data",
            ),
            SectionSpec(
                "1798.90.54",
                "ALPR — data sharing restrictions",
                notes="SB 34: prohibits sharing with immigration enforcement",
            ),
            SectionSpec(
                "1798.90.55",
                "ALPR — exemptions from CPRA",
                notes="SB 34: ALPR data not subject to CPRA disclosure in some contexts",
            ),
        ],
    ),
    # ------------------------------------------------------------------ #
    # California Vehicle Code — ALPR law enforcement use                 #
    # ------------------------------------------------------------------ #
    CodeSpec(
        code_id="cal_veh_code",
        code_name="California Vehicle Code",
        law_code="VEH",
        output_file="veh_code.json",
        sections=[
            SectionSpec(
                "2413",
                "ALPR — law enforcement use restrictions",
                notes="AB 169: retention, sharing, and auditing requirements for LE ALPR",
            ),
        ],
    ),
    # ------------------------------------------------------------------ #
    # California Welfare & Institutions Code — Juvenile records           #
    # ------------------------------------------------------------------ #
    CodeSpec(
        code_id="cal_welf_inst_code",
        code_name="California Welfare and Institutions Code",
        law_code="WIC",
        output_file="welf_inst_code.json",
        sections=[
            SectionSpec(
                "827",
                "Juvenile records — disclosure restrictions",
                notes="Juvenile case files are confidential; enumerated parties may inspect",
            ),
            SectionSpec(
                "828",
                "Juvenile records — law enforcement access",
            ),
            SectionSpec(
                "829",
                "Juvenile records — CPRA cross-reference",
            ),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------


class LegInfoFetcher:
    """Fetches California statute sections from leginfo.legislature.ca.gov."""

    def __init__(self, delay: float = 1.5, dry_run: bool = False):
        self.delay = delay
        self.dry_run = dry_run
        self._session = requests.Session()
        self._session.headers["User-Agent"] = _USER_AGENT
        self._session.headers["Accept"] = "text/html"

    def fetch_section(
        self,
        law_code: str,
        section: str,
    ) -> str | None:
        """Return the statute text for one section, or None on failure."""
        # leginfo expects the section number with a trailing period
        section_param = section if section.endswith(".") else f"{section}."
        url = f"{_LEGINFO_BASE}?sectionNum={section_param}&lawCode={law_code}"

        if self.dry_run:
            log.info("[DRY RUN] Would fetch: %s", url)
            return f"[DRY RUN — statutory text for {law_code} § {section}]"

        log.info("Fetching %s § %s …", law_code, section)
        try:
            resp = self._session.get(url, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            log.warning("  FAIL: %s", exc)
            return None
        finally:
            time.sleep(self.delay)

        return _extract_section_text(resp.text, law_code, section)

    def close(self) -> None:
        self._session.close()


def _extract_section_text(html: str, law_code: str, section: str) -> str | None:
    """Parse statute text from a leginfo HTML response."""
    soup = BeautifulSoup(html, "html.parser")

    # leginfo renders the content inside a <div class="codeLawContentItemDivClass">
    # or <div id="...manylayouttypes..."> depending on version.
    # We try multiple selectors in preference order.
    for selector in [
        "div#codeLawSectionNoHead",  # primary — CPRA/Pen./Civ./Veh. sections
        "div.content_margins",  # AB 481 §§ 36000+ and some older sections
        "div.codeLawContentItemDivClass",
        "div.lawCodeSection",
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(separator="\n", strip=True)
            if text:
                return text

    # Fallback: look for any div containing the section number as a heading
    for div in soup.find_all("div"):
        text = div.get_text(separator="\n", strip=True)
        if f"§ {section}" in text and len(text) > 100:
            return text

    log.warning("  Could not extract text for %s § %s", law_code, section)
    return None


# ---------------------------------------------------------------------------
# Main ingestion logic
# ---------------------------------------------------------------------------


def ingest_code(
    spec: CodeSpec,
    fetcher: LegInfoFetcher,
    out_dir: Path,
) -> int:
    """Fetch all sections for one code and write the JSON file. Returns count fetched."""
    records = []
    for sec_spec in spec.sections:
        text = fetcher.fetch_section(spec.law_code, sec_spec.section)
        if text is None:
            log.warning(
                "  Skipping %s § %s (fetch failed)", spec.law_code, sec_spec.section
            )
            continue
        record = {
            "section": sec_spec.section,
            "title": sec_spec.title,
            "text": text,
            "url": (
                f"{_LEGINFO_BASE}"
                f"?sectionNum={sec_spec.section}.&lawCode={spec.law_code}"
            ),
        }
        if sec_spec.notes:
            record["notes"] = sec_spec.notes
        records.append(record)

    output = {
        "code_id": spec.code_id,
        "code_name": spec.code_name,
        "source_url": f"https://leginfo.legislature.ca.gov/faces/codesTOCSelected.xhtml?tocCode={spec.law_code}",
        "as_of": TODAY,
        "sections": records,
    }

    out_path = out_dir / spec.output_file
    out_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info("Wrote %s (%d sections) → %s", spec.code_name, len(records), out_path)
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest California statute sections")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print URLs without fetching; write placeholder JSON",
    )
    parser.add_argument(
        "--code",
        choices=[c.law_code.lower() for c in _CODES] + ["all"],
        default="all",
        help="Which code to ingest (default: all)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds between requests (default: 1.5)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        help=f"Output directory (default: {_DEFAULT_OUT})",
    )
    args = parser.parse_args()

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    codes_to_run = (
        _CODES
        if args.code == "all"
        else [c for c in _CODES if c.law_code.lower() == args.code]
    )

    fetcher = LegInfoFetcher(delay=args.delay, dry_run=args.dry_run)
    total = 0
    try:
        for spec in codes_to_run:
            log.info("=== %s ===", spec.code_name)
            count = ingest_code(spec, fetcher, out_dir)
            total += count
    finally:
        fetcher.close()

    log.info("Done. Total sections fetched: %d", total)
    log.info("Output: %s", out_dir)


if __name__ == "__main__":
    main()
