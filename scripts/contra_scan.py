"""CONTRA corpus scanner — walk D:/CONTRA Contract Corpus/ and emit a manifest.

Run this BEFORE batch ingestion to review every inferred entity name, doc_type,
and version label. Edit the manifest JSON before feeding it to contra_batch_ingest.py.

Usage:
    python scripts/contra_scan.py
    python scripts/contra_scan.py --corpus-root "D:/CONTRA Contract Corpus" --out manifest.json

Output: manifest.json — one entry per PDF, ready for contra_batch_ingest.py.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Entity catalogue — directory name → canonical metadata
# ---------------------------------------------------------------------------
#
# Keys are exact directory names as they appear on disk.
# corporate_family: the controlling parent entity (for cross-entity analysis)
# entity_id_slug:  used to construct entity_id in the DB (snake_case)
#
_ENTITY_CATALOGUE: dict[str, dict] = {
    "AAA":                      {"entity_name": "AAA Northern California",      "corporate_family": "AAA",                       "entity_id_slug": "aaa_ncal"},
    "Adventist Health":         {"entity_name": "Adventist Health",             "corporate_family": "Adventist Health System",   "entity_id_slug": "adventist_health"},
    "Allstate":                 {"entity_name": "Allstate Insurance",           "corporate_family": "Allstate Corporation",      "entity_id_slug": "allstate"},
    "Amazon":                   {"entity_name": "Amazon.com",                   "corporate_family": "Amazon.com Inc.",           "entity_id_slug": "amazon"},
    "American Express":         {"entity_name": "American Express",             "corporate_family": "American Express Company",  "entity_id_slug": "amex"},
    "Anthem":                   {"entity_name": "Anthem Blue Cross",            "corporate_family": "Elevance Health",           "entity_id_slug": "anthem"},
    "Apple":                    {"entity_name": "Apple Inc.",                   "corporate_family": "Apple Inc.",                "entity_id_slug": "apple"},
    "AT&T":                     {"entity_name": "AT&T Mobility",               "corporate_family": "AT&T Inc.",                 "entity_id_slug": "att_mobility"},
    "Bank of America":          {"entity_name": "Bank of America",              "corporate_family": "Bank of America Corp.",     "entity_id_slug": "bofa"},
    "Boost":                    {"entity_name": "Boost Mobile",                 "corporate_family": "DISH Network",              "entity_id_slug": "boost_mobile"},
    "Capital One":              {"entity_name": "Capital One",                  "corporate_family": "Capital One Financial",     "entity_id_slug": "capital_one"},
    "Chase":                    {"entity_name": "JPMorgan Chase",               "corporate_family": "JPMorgan Chase & Co.",      "entity_id_slug": "jpmorgan_chase"},
    "Comcast":                  {"entity_name": "Comcast / Xfinity",            "corporate_family": "Comcast Corporation",       "entity_id_slug": "comcast"},
    "Cricket Wireless":         {"entity_name": "Cricket Wireless",             "corporate_family": "AT&T Inc.",                 "entity_id_slug": "cricket_wireless"},
    "Doordash":                 {"entity_name": "DoorDash",                     "corporate_family": "DoorDash Inc.",             "entity_id_slug": "doordash"},
    "Family Health Care Network":{"entity_name": "Family Healthcare Network",  "corporate_family": "FHCN",                      "entity_id_slug": "fhcn"},
    "Farmers Insurance":        {"entity_name": "Farmers Insurance",            "corporate_family": "Zurich Insurance Group",    "entity_id_slug": "farmers_ins"},
    "Google":                   {"entity_name": "Google LLC",                   "corporate_family": "Google LLC / Alphabet Inc.","entity_id_slug": "google"},
    "Grubhub":                  {"entity_name": "Grubhub",                      "corporate_family": "Just Eat Takeaway.com",     "entity_id_slug": "grubhub"},
    "Instacart":                {"entity_name": "Instacart",                    "corporate_family": "Maplebear Inc.",            "entity_id_slug": "instacart"},
    "Kaiser":                   {"entity_name": "Kaiser Permanente",            "corporate_family": "Kaiser Foundation Health",  "entity_id_slug": "kaiser"},
    "Kaweah Health":            {"entity_name": "Kaweah Health",                "corporate_family": "Kaweah Health",             "entity_id_slug": "kaweah_health"},
    "Lyft":                     {"entity_name": "Lyft Inc.",                    "corporate_family": "Lyft Inc.",                 "entity_id_slug": "lyft"},
    "Meta":                     {"entity_name": "Meta Platforms",               "corporate_family": "Meta Platforms Inc.",       "entity_id_slug": "meta"},
    "MetroPCS":                 {"entity_name": "Metro by T-Mobile",            "corporate_family": "T-Mobile US Inc.",          "entity_id_slug": "metro_tmobile"},
    "Microsoft":                {"entity_name": "Microsoft Corporation",        "corporate_family": "Microsoft Corporation",     "entity_id_slug": "microsoft"},
    "OptumHealth":              {"entity_name": "Optum Health",                 "corporate_family": "UnitedHealth Group",        "entity_id_slug": "optum"},
    "PG&E":                     {"entity_name": "Pacific Gas and Electric",     "corporate_family": "PG&E Corporation",          "entity_id_slug": "pge"},
    "SCE":                      {"entity_name": "Southern California Edison",   "corporate_family": "Edison International",      "entity_id_slug": "sce"},
    "Shipt":                    {"entity_name": "Shipt",                        "corporate_family": "Target Corporation",        "entity_id_slug": "shipt"},
    "State Farm":               {"entity_name": "State Farm Insurance",         "corporate_family": "State Farm Mutual Auto",    "entity_id_slug": "state_farm"},
    "T-Mobile":                 {"entity_name": "T-Mobile USA",                 "corporate_family": "T-Mobile US Inc.",          "entity_id_slug": "tmobile"},
    "Uber":                     {"entity_name": "Uber Technologies",            "corporate_family": "Uber Technologies Inc.",    "entity_id_slug": "uber"},
    "Verizon":                  {"entity_name": "Verizon Communications",       "corporate_family": "Verizon Communications Inc.","entity_id_slug": "verizon"},
    "Wells Fargo":              {"entity_name": "Wells Fargo",                  "corporate_family": "Wells Fargo & Company",     "entity_id_slug": "wells_fargo"},
    "YouTube":                  {"entity_name": "YouTube LLC",                  "corporate_family": "Google LLC / Alphabet Inc.","entity_id_slug": "youtube"},
    # Subsidiaries that appear as sub-directories under a parent entity
    "Zelle":                    {"entity_name": "Zelle",                        "corporate_family": "Early Warning Services LLC","entity_id_slug": "zelle"},
}

# ---------------------------------------------------------------------------
# Doc-type inference — ordered by specificity (most specific wins)
# ---------------------------------------------------------------------------

_DOCTYPE_RULES: list[tuple[str, list[str]]] = [
    # arbitration (most specific — must match before tos/privacy)
    ("arbitration", [
        "arbitration", "notice of dispute", "dispute form", "adr",
        "demand for arbitration", "arbitration initiation",
    ]),
    # eula
    ("eula", [
        "end user license", "eula", "software license agreement",
        "program license agreement", "license agreement", "ios end user",
        "android end user", "ebonding", "open source",
    ]),
    # privacy_notice
    ("privacy_notice", [
        "privacy policy", "privacy notice", "privacy practices",
        "privacy statement", "notice at collection", "ccpa",
        "gdpr", "global privacy", "information practices",
        "nondiscrimination notice", "notice of privacy",
        "privacy control", "cookies and tracking", "e-sign",
        "electronic communications", "paperless", "disclosure",
        "children's privacy", "subpoena",
    ]),
    # tos (broad catch-all for service agreements)
    ("tos", [
        "terms of service", "terms and conditions", "terms of use",
        "subscriber agreement", "customer agreement", "service agreement",
        "user agreement", "acceptable use policy", "fee schedule",
        "mobile agreement", "business agreement", "installment contract",
        "installment agreement", "credit sale contract", "device return",
        "warranty", "plan terms", "plan details", "service terms",
        "wi-fi terms", "wifi terms", "program terms", "web services",
        "turbo for business", "billing disclosures", "broadband",
        "mobile broadband", "purchased content", "smart home",
        "payment terms", "payment conditions", "deposit agreement",
        "digital services", "member agreement", "membership",
        "rider agreement", "driver agreement", "driver terms",
        "shopper agreement", "merchant", "service protection",
        "upgrade program",
    ]),
]

# Months for date extraction from filenames
_MONTH_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def _infer_doc_type(filename: str) -> tuple[str, float]:
    """Return (doc_type, confidence) by matching filename keywords.

    Normalises hyphens and underscores to spaces before matching so that
    'Arbitration-initiation-form' matches keyword 'arbitration initiation'
    and 'Notice-of-Dispute-form' matches 'notice of dispute'.
    """
    # Normalise separators → spaces for keyword matching
    name_lower = filename.lower().replace("-", " ").replace("_", " ")
    for doc_type, keywords in _DOCTYPE_RULES:
        for kw in keywords:
            if kw in name_lower:
                return doc_type, 0.85
    return "tos", 0.30  # low-confidence default


def _extract_version_date(filename: str) -> tuple[str | None, datetime | None]:
    """Parse an effective date from filenames like 'policy_en_us_August_2020.pdf'.

    Returns (version_label, effective_date) or (None, None) if no date found.
    """
    stem = Path(filename).stem.lower()

    # Pattern: ..._Month_Year (e.g. google_privacy_policy_en_May_2018)
    match = re.search(
        r"_(" + "|".join(_MONTH_MAP) + r")_(\d{4})",
        stem,
        re.IGNORECASE,
    )
    if match:
        month_name = match.group(1).lower()
        year = int(match.group(2))
        month = int(_MONTH_MAP[month_name])
        label = f"{match.group(1).capitalize()} {year}"
        try:
            dt = datetime(year, month, 1)
            return label, dt
        except ValueError:
            pass

    # Pattern: ..._Year only (e.g. google_terms_of_service_en_us_2022)
    match = re.search(r"_(\d{4})(?:$|[_\-])", stem)
    if match:
        year = int(match.group(1))
        if 2000 <= year <= 2030:
            label = str(year)
            try:
                dt = datetime(year, 1, 1)
                return label, dt
            except ValueError:
                pass

    # Pattern: year in parentheses or at end of stem (e.g. "ToS 2022")
    match = re.search(r"\b(20\d{2})\b", stem)
    if match:
        year = int(match.group(1))
        return str(year), datetime(year, 1, 1)

    return None, None


def _resolve_entity(parent_dir: str, current_dir: str) -> dict:
    """Resolve entity metadata from directory path components."""
    # If current_dir is itself a known entity (sub-directory case like Zelle)
    if current_dir in _ENTITY_CATALOGUE:
        meta = dict(_ENTITY_CATALOGUE[current_dir])
        if parent_dir and parent_dir != current_dir and parent_dir in _ENTITY_CATALOGUE:
            # Mark the parent relationship
            parent = _ENTITY_CATALOGUE[parent_dir]
            meta["parent_entity"] = parent["entity_name"]
        return meta

    # Fall back to parent_dir entity
    if parent_dir in _ENTITY_CATALOGUE:
        return dict(_ENTITY_CATALOGUE[parent_dir])

    # Unknown directory — flag for manual review
    name = current_dir if current_dir else parent_dir
    return {
        "entity_name": name,
        "corporate_family": None,
        "entity_id_slug": name.lower().replace(" ", "_").replace("&", "and"),
        "_needs_review": True,
    }


def scan_corpus(corpus_root: Path) -> list[dict]:
    """Walk corpus_root and return a list of manifest entries."""
    entries: list[dict] = []
    root_parts = len(corpus_root.parts)

    for pdf in sorted(corpus_root.rglob("*.pdf")):
        parts = pdf.parts[root_parts:]  # relative path components

        if len(parts) == 2:
            # Root-level entity file: <Entity>/<filename.pdf>
            parent_dir = parts[0]
            sub_dir = parts[0]
        elif len(parts) == 3:
            # Sub-entity file: <Entity>/<SubEntity>/<filename.pdf>
            parent_dir = parts[0]
            sub_dir = parts[1]
        else:
            # Deep nesting — treat parent as entity, flag for review
            parent_dir = parts[0]
            sub_dir = parts[0]

        entity_meta = _resolve_entity(parent_dir, sub_dir)
        doc_type, confidence = _infer_doc_type(pdf.name)
        version_label, effective_date = _extract_version_date(pdf.name)

        entry: dict = {
            "file_path": str(pdf),
            "entity_name": entity_meta["entity_name"],
            "entity_id_slug": entity_meta["entity_id_slug"],
            "corporate_family": entity_meta.get("corporate_family"),
            "parent_entity": entity_meta.get("parent_entity"),
            "doc_type": doc_type,
            "doc_type_confidence": confidence,
            "version_label": version_label,
            "effective_date": effective_date.isoformat()[:10] if effective_date else None,
            "source_tier": "T1",
            "needs_review": entity_meta.get("_needs_review", False) or confidence < 0.5,
        }
        entries.append(entry)

    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan CONTRA corpus and emit a manifest JSON.")
    parser.add_argument(
        "--corpus-root",
        default=r"D:\CONTRA Contract Corpus",
        help="Path to the corpus root directory",
    )
    parser.add_argument(
        "--out",
        default="contra_manifest.json",
        help="Output JSON manifest path",
    )
    args = parser.parse_args()

    root = Path(args.corpus_root)
    if not root.exists():
        print(f"ERROR: corpus root not found: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {root}")
    entries = scan_corpus(root)

    # Summary
    by_entity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    needs_review = 0
    for e in entries:
        by_entity[e["entity_name"]] = by_entity.get(e["entity_name"], 0) + 1
        by_type[e["doc_type"]] = by_type.get(e["doc_type"], 0) + 1
        if e["needs_review"]:
            needs_review += 1

    print(f"\nFound {len(entries)} documents across {len(by_entity)} entities")
    print(f"  {needs_review} entries flagged for review (low confidence or unknown entity)")
    print("\nBy entity:")
    for name, count in sorted(by_entity.items(), key=lambda x: -x[1]):
        print(f"  {name:<40} {count:>3}")
    print("\nBy doc_type:")
    for dt, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {dt:<20} {count:>3}")

    out_path = Path(args.out)
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest written to: {out_path.resolve()}")
    print("Review it before running contra_batch_ingest.py")


if __name__ == "__main__":
    main()
