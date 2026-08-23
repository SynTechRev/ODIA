"""Build CONTRA manifests for the full Uber sub-processor ecosystem.

Routes root-level files to correct entities (Uber core, Portier LLC, Google LLC,
Cambridge Mobile Telematics) and generates per-entity manifests for each vendor
subfolder (Fullstory, Plaid, TrustArc, Meta, Microsoft, etc.).

Produces:
  contra_manifest_uber_core.json        -- Uber Technologies Inc. core instruments
  contra_manifest_portier.json          -- Portier LLC (Uber Eats delivery entity)
  contra_manifest_cmt.json              -- Cambridge Mobile Telematics
  contra_manifest_uber_google.json      -- Google LLC docs (merges with existing corpus)
  contra_manifest_uber_vendors.json     -- All subfolder vendor entities combined

Usage:
    python scripts/build_manifest_uber_ecosystem.py --dry-run
    python scripts/build_manifest_uber_ecosystem.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_UBER_ROOT = Path(r"D:\CONTRA Contract Corpus\Uber Technologies Inc")

# Root-level file routing — explicit assignment for every file
_ROOT_ROUTING: dict[str, dict] = {
    "Uber U.S. Terms of Use.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    "THE NEW UBER PRO TERMS AND CONDITIONS.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    "Uber Pro Terms And Conditions 2026.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
        "version_label": "2026",
    },
    "Uber Cookie Notice (Global).pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Driver and Delivery Person Privacy Notice.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Driver and Delivery Person Privacy Notice (1).pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Driver Privacy Notice.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Guidelines for Third Party Data Requests and Service of Legal Documents_.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    "Uber use of Cambridge Mobile Telematics.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    # Portier LLC — separate entity (Uber Eats delivery operations)
    "Portier LLC Terms and Conditions.pdf": {
        "entity_name": "Portier LLC",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    # Cambridge Mobile Telematics — driver behavioral scoring vendor
    "Cambridge Mobile Telematics PRIVACY POLICY.pdf": {
        "entity_name": "Cambridge Mobile Telematics",
        "corporate_family": "Cambridge Mobile Telematics",
        "doc_type": "privacy_notice",
    },
    # Google LLC docs — route to existing corpus entity
    "Google Analytics Privacy Notice Safeguarding your data.pdf": {
        "entity_name": "Google LLC",
        "corporate_family": "Alphabet",
        "doc_type": "privacy_notice",
    },
    "How Google uses information from sites or apps that use our services.pdf": {
        "entity_name": "Google LLC",
        "corporate_family": "Alphabet",
        "doc_type": "privacy_notice",
    },
    # REJECTS — not commercial legal instruments
    "European Commission Standard Contractual Clauses (SCC).pdf": None,
    "Office of Privacy and Open Government Privacy Laws, Policies and Guidance.pdf": None,
    "Salesloft Cookie Notice.pdf": None,
    "ITA PRIVACY PROGRAM.pdf": None,
}

# Subfolder → entity mapping
_SUBFOLDER_ENTITIES: dict[str, dict] = {
    "Fullstory": {
        "entity_name": "Fullstory Inc.",
        "corporate_family": "Fullstory",
        "notes": "Session replay and behavioral analytics — receives full behavioral stream of all Uber users",
    },
    "Plaid": {
        "entity_name": "Plaid Inc.",
        "corporate_family": "Plaid",
        "notes": "Financial data aggregator — bank account access for Uber payment processing",
    },
    "TrustArc": {
        "entity_name": "TrustArc Inc.",
        "corporate_family": "TrustArc",
        "notes": "Consent management platform — manages privacy consent on behalf of Uber",
    },
    "Meta": {
        "entity_name": "Meta Platforms",
        "corporate_family": "Meta",
        "notes": "Ad targeting — merges with existing Meta corpus records",
    },
    "MicrosoftBing": {
        "entity_name": "Microsoft Corporation",
        "corporate_family": "Microsoft",
        "notes": "Bing Ads and analytics",
    },
    "NextRoll": {
        "entity_name": "NextRoll Inc.",
        "corporate_family": "NextRoll",
        "notes": "Programmatic ad retargeting",
    },
    "Tealium": {
        "entity_name": "Tealium Inc.",
        "corporate_family": "Tealium",
        "notes": "Tag management and data layer orchestration",
    },
    "Upside": {
        "entity_name": "Upside Commerce Group",
        "corporate_family": "Upside",
        "notes": "Cashback rewards and loyalty data",
    },
    "Dwolla": {
        "entity_name": "Dwolla Inc.",
        "corporate_family": "Dwolla",
        "notes": "ACH payment processing",
    },
    "Modulr": {
        "entity_name": "Modulr FS Limited",
        "corporate_family": "Modulr",
        "notes": "Payment infrastructure (UK operations)",
    },
    "Pintrest": {
        "entity_name": "Pinterest Inc.",
        "corporate_family": "Pinterest",
        "notes": "Ad platform",
    },
    "Qualtrics": {
        "entity_name": "Qualtrics LLC",
        "corporate_family": "Qualtrics",
        "notes": "Survey and experience data",
    },
}

_DOC_TYPE_KEYWORDS = {
    "arbitrat": "arbitration", "dispute": "arbitration",
    "eula": "eula", "end user licen": "eula",
    "privacy": "privacy_notice", "cookie": "privacy_notice", "ccpa": "privacy_notice",
    "gdpr": "privacy_notice", "data polic": "privacy_notice", "data processing": "privacy_notice",
    "sub-processor": "privacy_notice", "sub processor": "privacy_notice",
    "terms": "tos", "conditions": "tos", "acceptable use": "tos",
    "service level": "tos", "addendum": "tos", "partner program": "tos",
}


def _infer_doc_type(filename: str) -> str:
    fn = filename.lower()
    for kw, dt in _DOC_TYPE_KEYWORDS.items():
        if kw in fn:
            return dt
    return "tos"


def _make_entry(file_path: Path, entity_name: str, corporate_family: str,
                doc_type: str, version_label: str | None = None) -> dict:
    return {
        "file_path": str(file_path.resolve()),
        "entity_name": entity_name,
        "corporate_family": corporate_family,
        "doc_type": doc_type,
        "doc_type_confidence": 0.85,
        "needs_review": False,
        "version_label": version_label,
        "effective_date": None,
        "source_url": None,
    }


def build(dry_run: bool) -> None:
    if not _UBER_ROOT.exists():
        print(f"ERROR: Uber corpus folder not found: {_UBER_ROOT}")
        return

    # --- Root-level files ---
    uber_core: list[dict] = []
    portier: list[dict] = []
    cmt: list[dict] = []
    google_supplement: list[dict] = []
    rejected: list[str] = []
    unrouted: list[str] = []

    for pdf in sorted(_UBER_ROOT.glob("*.pdf")):
        routing = _ROOT_ROUTING.get(pdf.name)
        if routing is None:
            if pdf.name in _ROOT_ROUTING:
                rejected.append(pdf.name)
                continue
            else:
                unrouted.append(pdf.name)
                continue

        entry = _make_entry(
            pdf,
            entity_name=routing["entity_name"],
            corporate_family=routing["corporate_family"],
            doc_type=routing["doc_type"],
            version_label=routing.get("version_label"),
        )

        if routing["entity_name"] == "Uber Technologies Inc.":
            uber_core.append(entry)
        elif routing["entity_name"] == "Portier LLC":
            portier.append(entry)
        elif routing["entity_name"] == "Cambridge Mobile Telematics":
            cmt.append(entry)
        elif routing["entity_name"] == "Google LLC":
            google_supplement.append(entry)

    # --- Subfolder vendor entities ---
    vendor_entries: list[dict] = []
    vendor_summary: dict[str, int] = {}

    for subfolder_name, entity_info in _SUBFOLDER_ENTITIES.items():
        subfolder = _UBER_ROOT / subfolder_name
        if not subfolder.exists():
            continue
        pdfs = sorted(subfolder.glob("*.pdf"))
        if not pdfs:
            continue

        vendor_summary[entity_info["entity_name"]] = len(pdfs)
        for pdf in pdfs:
            entry = _make_entry(
                pdf,
                entity_name=entity_info["entity_name"],
                corporate_family=entity_info["corporate_family"],
                doc_type=_infer_doc_type(pdf.name),
            )
            vendor_entries.append(entry)

    # --- Print plan ---
    print("\n== UBER ECOSYSTEM MANIFEST BUILD ==\n")
    print(f"  Uber Technologies Inc. (core)  : {len(uber_core)} instruments")
    print(f"  Portier LLC                    : {len(portier)} instrument")
    print(f"  Cambridge Mobile Telematics    : {len(cmt)} instrument")
    print(f"  Google LLC (supplement)        : {len(google_supplement)} instruments")
    print(f"  Sub-processor vendors          : {sum(vendor_summary.values())} instruments across {len(vendor_summary)} entities")
    for name, count in sorted(vendor_summary.items(), key=lambda x: -x[1]):
        print(f"    {name:<35} {count}")
    if rejected:
        print(f"\n  REJECTED (not legal instruments): {len(rejected)}")
        for r in rejected:
            print(f"    - {r}")
    if unrouted:
        print(f"\n  UNROUTED (check routing map): {len(unrouted)}")
        for u in unrouted:
            print(f"    ? {u}")

    total = len(uber_core) + len(portier) + len(cmt) + len(google_supplement) + len(vendor_entries)
    print(f"\n  TOTAL entries to ingest: {total}")

    if dry_run:
        print("\n  (dry run — manifests not written)")
        return

    def _write(path: str, entries: list[dict]) -> None:
        if not entries:
            return
        out = Path(path)
        out.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Written: {out} ({len(entries)} entries)")

    print("\nWriting manifests...")
    _write("contra_manifest_uber_core.json", uber_core)
    _write("contra_manifest_portier.json", portier)
    _write("contra_manifest_cmt.json", cmt)
    _write("contra_manifest_uber_google.json", google_supplement)
    _write("contra_manifest_uber_vendors.json", vendor_entries)

    print("\nNext — ingest in order:")
    print("  python scripts/contra_batch_ingest.py --manifest contra_manifest_uber_core.json --skip-review")
    print("  python scripts/contra_batch_ingest.py --manifest contra_manifest_portier.json --skip-review")
    print("  python scripts/contra_batch_ingest.py --manifest contra_manifest_cmt.json --skip-review")
    print("  python scripts/contra_batch_ingest.py --manifest contra_manifest_uber_google.json --skip-review")
    print("  python scripts/contra_batch_ingest.py --manifest contra_manifest_uber_vendors.json --skip-review")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build CONTRA manifests for the full Uber sub-processor ecosystem"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    build(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
