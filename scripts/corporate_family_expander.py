"""CONTRA corporate family expander — resolves subsidiaries via SEC EDGAR + OpenCorporates.

Walks commercial_entities rows and attempts to fill in corporate_family relationships
by querying the SEC EDGAR company search API and the OpenCorporates API. Outputs a
JSON report of discovered relationships and optionally updates the DB.

Priority targets for corpus expansion:
  Verizon Communications — completes telecom triad (AT&T + Comcast already ingested)
  T-Mobile USA           — wireless-only baseline
  Cricket Wireless       — price-sensitive consumer hypothesis test (subsidiary of AT&T)
  Meta Platforms         — largest data-extraction platform not yet in corpus

Usage:
    python scripts/corporate_family_expander.py
    python scripts/corporate_family_expander.py --entity "AT&T Inc."
    python scripts/corporate_family_expander.py --dry-run
    python scripts/corporate_family_expander.py --report-only
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_USER_AGENT = (
    "ODIA-CONTRA-Expander/3.9 (SynTechRev research; contact codicalcalculus@gmail.com)"
)
_EDGAR_COMPANY_SEARCH = "https://efts.sec.gov/LATEST/search-index?q={name}&dateRange=custom&startdt=2020-01-01&forms=10-K"
_EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_PAUSE = 1.5

# Known-good corporate family seeds to pre-populate without needing API
_KNOWN_FAMILIES: dict[str, str] = {
    "AT&T Inc.": "AT&T",
    "AT&T": "AT&T",
    "Cricket Wireless": "AT&T",  # AT&T subsidiary
    "AT&T Mobility": "AT&T",
    "DIRECTV": "AT&T",
    "Comcast Corporation": "Comcast",
    "Comcast": "Comcast",
    "Comcast / Xfinity": "Comcast",
    "Xfinity": "Comcast",
    "NBCUniversal": "Comcast",
    "JPMorgan Chase & Co.": "JPMorgan Chase",
    "JPMorgan Chase": "JPMorgan Chase",
    "Chase Bank": "JPMorgan Chase",
    "Chase": "JPMorgan Chase",
    "Zelle": "JPMorgan Chase",  # operated by Early Warning Services (consortium)
    "Google LLC": "Alphabet",
    "Google": "Alphabet",
    "Alphabet Inc.": "Alphabet",
    "YouTube": "Alphabet",
    "DeepMind": "Alphabet",
    "Kaiser Permanente": "Kaiser Permanente",
    "Kaiser Foundation Health Plan": "Kaiser Permanente",
    "Verizon Communications": "Verizon",
    "Verizon": "Verizon",
    "T-Mobile USA": "T-Mobile",
    "T-Mobile US": "T-Mobile",
    "T-Mobile": "T-Mobile",
    "Sprint": "T-Mobile",  # T-Mobile merger 2020
    "Meta Platforms": "Meta",
    "Meta": "Meta",
    "Facebook": "Meta",
    "Instagram": "Meta",
    "WhatsApp": "Meta",
    # ── Uber ecosystem ─────────────────────────────────────────────────────────
    "Uber Technologies Inc.": "Uber",
    "Uber": "Uber",
    "Portier LLC": "Uber",  # Uber Eats delivery legal entity
    # Identity verification vendors (private companies)
    "Jumio Inc.": "Jumio",
    "Jumio Corporation": "Jumio",
    "Socure Inc.": "Socure",
    "Veriff Inc.": "Veriff",
    "Veriff OÜ": "Veriff",
    # Compliance automation vendors (private)
    "Vanta Inc.": "Vanta",
    "Drata Inc.": "Drata",
    "Sprinto Inc.": "Sprinto",
    "Sprinto HQ Inc.": "Sprinto",
    # Data / payment vendors (private)
    "Plaid Inc.": "Plaid",
    "Dwolla Inc.": "Dwolla",
    "Modulr FS Limited": "Modulr",
    "Upside Commerce Group": "Upside",
    # Tag management / advertising (private or public)
    "Tealium Inc.": "Tealium",
    "TrustArc Inc.": "TrustArc",  # formerly TrustE
    "Microsoft Corporation": "Microsoft",
    "Microsoft": "Microsoft",
    "NextRoll Inc.": "NextRoll",  # formerly AdRoll Group
    "AdRoll Group": "NextRoll",
    "Pinterest Inc.": "Pinterest",
    "Fullstory Inc.": "Fullstory",
    # Telematics
    "Cambridge Mobile Telematics": "Cambridge Mobile Telematics",
}


def _engine(db_path: str):
    from sqlalchemy import create_engine

    return create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )


def _edgar_cik_lookup(name: str) -> str | None:
    """Look up SEC CIK for a company name via EDGAR full-text search."""
    try:
        import requests

        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{name}"', "forms": "10-K"},
            headers={"User-Agent": _USER_AGENT},
            timeout=15,
        )
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if hits:
            return hits[0].get("_source", {}).get("entity_id")
    except Exception as exc:
        print(f"  EDGAR lookup failed for {name}: {exc}", file=sys.stderr)
    return None


def _opencorporates_lookup(name: str) -> dict | None:
    """Query OpenCorporates for top company match. Returns company dict or None."""
    try:
        import requests

        resp = requests.get(
            "https://api.opencorporates.com/v0.4/companies/search",
            params={"q": name, "jurisdiction_code": "us", "per_page": 1},
            headers={"User-Agent": _USER_AGENT},
            timeout=15,
        )
        data = resp.json()
        results = data.get("results", {}).get("companies", [])
        if results:
            return results[0].get("company", {})
    except Exception as exc:
        print(f"  OpenCorporates lookup failed for {name}: {exc}", file=sys.stderr)
    return None


def expand(
    db_path: str,
    entity_filter: str | None,
    dry_run: bool,
    report_only: bool,
) -> None:
    from oraculus_di_auditor.db.models import CommercialEntity
    from sqlalchemy.orm import sessionmaker

    engine = _engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    query = session.query(CommercialEntity)
    if entity_filter:
        query = query.filter(CommercialEntity.canonical_name == entity_filter)
    entities = query.all()

    print(f"Entities to process: {len(entities)}\n")

    report: list[dict] = []
    updated = 0

    for entity in entities:
        name = entity.canonical_name
        current_family = entity.corporate_family

        # Check known-good seeds first (no API call needed)
        resolved_family = _KNOWN_FAMILIES.get(name)

        if resolved_family is None and not report_only:
            # Try EDGAR
            print(f"  EDGAR lookup: {name}")
            cik = _edgar_cik_lookup(name)
            time.sleep(_PAUSE)

            if cik:
                resolved_family = name  # CIK found — it's a top-level entity
                print(f"    CIK found: {cik}")
            else:
                # Try OpenCorporates
                print(f"  OpenCorporates lookup: {name}")
                oc = _opencorporates_lookup(name)
                time.sleep(_PAUSE)
                if oc:
                    resolved_family = oc.get("company_type") and name
                    print(
                        f"    OC match: {oc.get('name', '?')} ({oc.get('jurisdiction_code', '?')})"
                    )

        entry = {
            "entity_id": entity.entity_id,
            "canonical_name": name,
            "current_family": current_family,
            "resolved_family": resolved_family,
            "changed": resolved_family is not None
            and resolved_family != current_family,
        }
        report.append(entry)

        if entry["changed"]:
            print(
                f"  {name}: corporate_family "
                f"{'(unchanged)' if current_family == resolved_family else repr(current_family)} "
                f"-> {repr(resolved_family)}"
            )
            if not dry_run and not report_only:
                entity.corporate_family = resolved_family
                updated += 1

    if not dry_run and not report_only:
        session.commit()

    session.close()

    # Write report
    out = Path("data/corporate_family_report.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "generated_at": __import__("datetime")
                .datetime.now(__import__("datetime").timezone.utc)
                .isoformat(),
                "total_entities": len(report),
                "entities": report,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n-- Corporate Family Expander Results --")
    print(f"  Entities processed : {len(entities)}")
    changed = [e for e in report if e["changed"]]
    print(f"  Families resolved  : {len(changed)}")
    print(
        f"  DB rows updated    : {updated if not dry_run and not report_only else '(dry run)'}"
    )
    print(f"  Report written to  : {out.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Expand CONTRA corporate family relationships via EDGAR + OpenCorporates"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument(
        "--entity", default=None, help="Restrict to one canonical entity name"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without writing"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Use only known-seed data; skip all API calls",
    )
    args = parser.parse_args()

    expand(
        db_path=args.db_path,
        entity_filter=args.entity,
        dry_run=args.dry_run,
        report_only=args.report_only,
    )


if __name__ == "__main__":
    main()
