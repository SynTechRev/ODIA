"""CONTRA new-PDF finder — hash-based dedup against contra_corpus.db.

Walks a corpus folder tree, computes SHA-256 for each PDF, and cross-references
against commercial_documents.document_hash in the DB.  Outputs ONLY files not yet
ingested — eliminating the DUP-heavy batch problem from naïve folder scans.

Also optionally writes:
  - A manifest JSON ready for contra_batch_ingest.py (with entity_name inferred
    from subfolder structure)
  - A DUP report of files already in DB (for audit purposes)

Usage:
    # Show what's new (dry run):
    python scripts/contra_new_pdf_finder.py --folder "D:/CONTRA Contract Corpus/Uber Technologies Inc"

    # Write manifest of new files:
    python scripts/contra_new_pdf_finder.py --folder "D:/CONTRA Contract Corpus/Uber Technologies Inc" \
        --entity "Uber Technologies Inc." --manifest out.json

    # Walk full corpus root, infer entity from first-level subfolder name:
    python scripts/contra_new_pdf_finder.py --folder "D:/CONTRA Contract Corpus" --auto-entity

    # Include DUP report:
    python scripts/contra_new_pdf_finder.py --folder "D:/CONTRA Contract Corpus" --auto-entity \
        --dup-report dup_report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"

# Infer doc_type from filename
_DOCTYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"arbitrat|dispute|aaa|jams|notice.of.dispute|paa|platform.access", re.I
        ),
        "tos",
    ),
    (re.compile(r"eula|end.user.licen|software.licen", re.I), "eula"),
    (
        re.compile(r"privacy|ccpa|gdpr|hipaa|data.polic|cookie|biometric|health", re.I),
        "privacy_notice",
    ),
    (
        re.compile(
            r"data.processing|dpa|processor.agreement|standard.contractual", re.I
        ),
        "data_processing_agreement",
    ),
    (
        re.compile(
            r"terms|tos|tou|subscriber|customer.agreement|service.agreement|condition",
            re.I,
        ),
        "tos",
    ),
]

# Reject patterns — not consumer-facing legal instruments
_REJECT_PATTERNS = re.compile(
    r"apache.licen|w3c.process|annual.report|press.release|investor|earnings|proxy"
    r"|soc2.report|audit.report|white.paper|case.study|accessibility|icon|logo"
    r"|wcag|section.508|en.301|w-9|w9.form|tax.form|pricing.guide|price.guide"
    r"|code.of.conduct|meet.and.confer|fraud.article",
    re.I,
)

# Top-level corpus entity folders → canonical entity name
_CORPUS_TOP_LEVEL_MAP: dict[str, str] = {
    "AAA": "AAA",
    "Adventist Health": "Adventist Health",
    "Allstate": "Allstate Corporation",
    "Amazon": "Amazon.com",
    "American Express": "American Express Company",
    "Anthem": "Anthem Inc.",
    "Apple": "Apple Inc.",
    "AT&T": "AT&T Mobility",
    "Bank of America": "Bank of America Corporation",
    "Boost": "Boost Mobile",
    "Capital One": "Capital One Financial",
    "Chase": "JPMorgan Chase",
    "Comcast": "Comcast Corporation",
    "Cricket Wireless": "Cricket Wireless",
    "Doordash": "DoorDash Inc.",
    "Family Health Care Network": "Family Health Care Network",
    "Farmers Insurance": "Farmers Insurance Exchange",
    "Google": "Google LLC",
    "Grubhub": "Grubhub Inc.",
    "Instacart": "Maplebear Inc.",
    "Kaiser": "Kaiser Foundation Health Plan",
    "Kaweah Health": "Kaweah Delta Health Care District",
    "Lyft": "Lyft Inc.",
    "Meta": "Meta Platforms",
    "MetroPCS": "MetroPCS Communications",
    "Microsoft": "Microsoft Corporation",
    "OptumHealth": "Optum Inc.",
    "PG&E": "Pacific Gas and Electric Company",
    "Qualtrics": "Qualtrics International",
    "SCE": "Southern California Edison",
    "Shipt": "Shipt Inc.",
    "State Farm": "State Farm Mutual",
    "T-Mobile": "T-Mobile US Inc.",
    "Uber Technologies Inc": "Uber Technologies Inc.",
    "Verizon": "Verizon Communications",
    "Wells Fargo": "Wells Fargo & Company",
    "YouTube": "Google LLC",
}

# Subfolder → entity name inference for the Uber Technologies Inc structure
_UBER_SUBFOLDER_ENTITY_MAP: dict[str, str] = {
    "Drata": "Drata Inc.",
    "Dwolla": "Dwolla Inc.",
    "Facebook": "Meta Platforms",
    "Fullstory": "Fullstory Inc.",
    "Jumio": "Jumio Inc.",
    "Meta": "Meta Platforms",
    "MicrosoftBing": "Microsoft Corporation",
    "Modulr": "Modulr FS Limited",
    "NextRoll": "NextRoll Inc.",
    "Pintrest": "Pinterest Inc.",
    "Plaid": "Plaid Inc.",
    "Socure": "Socure Inc.",
    "Sprinto": "Sprinto Inc.",
    "Tealium": "Tealium Inc.",
    "TrustArc": "TrustArc Inc.",
    "Upside": "Upside Commerce Group",
    "Vanta": "Vanta Inc.",
    "Veriff": "Veriff Inc.",
    # Uber subsidiaries
    "Schleuder": "Schleuder LLC",
    "Rasier": "Rasier LLC",
    # Empty subfolders — will be flagged as needing URL discovery
    "Amazon": "Amazon.com",
    "Criteo": "Criteo SA",
    "Demandbase": "Demandbase Inc.",
    "Drift": "Drift.com Inc.",
    "Google Ads": "Google LLC",
    "Hotjar": "Hotjar Ltd.",
    "Instagram": "Meta Platforms",
    "Joveo": "Joveo Inc.",
    "Lime": "Neutron Holdings Inc.",
    "LinkedIn": "LinkedIn Corporation",
    "LiveRamp": "LiveRamp Holdings",
    "Marketo": "Adobe Inc.",
    "MNTN": "MNTN Inc.",
    "Mutiny": "Mutiny Inc.",
    "PayPal": "PayPal Holdings",
    "Qualtrics": "Qualtrics International",
    "Reddit": "Reddit Inc.",
    "Rokt": "Rokt Pte. Ltd.",
    "Snap": "Snap Inc.",
    "Tembici": "Tembici S.A.",
    "The Trade Desk": "The Trade Desk Inc.",
    "TikTok": "TikTok Inc.",
    "TripleLift": "TripleLift Inc.",
    "TwitterX": "X Corp.",
    "Yahoo": "Yahoo Inc.",
    "Zeta": "Zeta Global Holdings",
}


def _sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _infer_doc_type(filename: str) -> str:
    if _REJECT_PATTERNS.search(filename):
        return "__REJECT__"
    for pattern, doc_type in _DOCTYPE_PATTERNS:
        if pattern.search(filename):
            return doc_type
    return "tos"  # fallback default


def _infer_entity_from_path(
    pdf_path: Path, root: Path, default_entity: str | None
) -> str:
    """Infer entity name from subfolder structure relative to root.

    Lookup order:
      1. Top-level corpus folder → _CORPUS_TOP_LEVEL_MAP
      2. Uber-ecosystem nested subfolder → _UBER_SUBFOLDER_ENTITY_MAP
      3. Two levels deep (e.g. Meta/TrustArc) → _UBER_SUBFOLDER_ENTITY_MAP for level-2
      4. Folder name as-is (last resort)
    """
    try:
        rel = pdf_path.relative_to(root)
        parts = rel.parts
        if len(parts) >= 2:
            top_folder = parts[0]
            # Top-level corpus entity folder (highest priority)
            if top_folder in _CORPUS_TOP_LEVEL_MAP:
                # If nested under a known Uber sub-processor, prefer that entity
                if len(parts) >= 3:
                    nested = parts[1]
                    if nested in _UBER_SUBFOLDER_ENTITY_MAP:
                        return _UBER_SUBFOLDER_ENTITY_MAP[nested]
                return _CORPUS_TOP_LEVEL_MAP[top_folder]
            # Uber-ecosystem nested subfolder
            if top_folder in _UBER_SUBFOLDER_ENTITY_MAP:
                return _UBER_SUBFOLDER_ENTITY_MAP[top_folder]
            # Two-level nesting (e.g. any/TrustArc/file.pdf)
            if len(parts) >= 3:
                nested = parts[1]
                if nested in _UBER_SUBFOLDER_ENTITY_MAP:
                    return _UBER_SUBFOLDER_ENTITY_MAP[nested]
            return top_folder  # use folder name as entity name (last resort)
        elif len(parts) == 1:
            # File directly in root folder
            return default_entity or "Unknown"
    except ValueError:
        pass
    return default_entity or "Unknown"


def find_new_pdfs(
    folder: Path,
    db_path: str,
    entity_name: str | None = None,
    auto_entity: bool = False,
    reject_known: bool = True,
) -> tuple[list[dict], list[dict]]:
    """
    Returns (new_entries, dup_entries).

    new_entries: PDFs not in DB — manifest-ready dicts
    dup_entries: PDFs already in DB
    """
    from sqlalchemy import create_engine, text

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    # Load all known hashes from DB
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT d.document_hash, e.canonical_name FROM commercial_documents d "
                "JOIN commercial_entities e ON e.entity_id = d.entity_id"
            )
        ).fetchall()

    known_hashes: dict[str, str] = {
        row[0]: row[1] for row in rows
    }  # hash → entity_name

    pdfs = sorted(folder.rglob("*.pdf"))
    new_entries: list[dict] = []
    dup_entries: list[dict] = []
    rejected: list[str] = []

    for pdf in pdfs:
        doc_type = _infer_doc_type(pdf.name)
        if doc_type == "__REJECT__":
            rejected.append(str(pdf))
            continue

        file_hash = _sha256(pdf)

        if file_hash in known_hashes:
            dup_entries.append(
                {
                    "file_path": str(pdf),
                    "document_hash": file_hash,
                    "existing_entity": known_hashes[file_hash],
                    "status": "duplicate",
                }
            )
            continue

        # New file — build manifest entry
        if auto_entity:
            inferred_entity = _infer_entity_from_path(pdf, folder, entity_name)
        else:
            inferred_entity = entity_name or "Unknown"

        new_entries.append(
            {
                "entity_name": inferred_entity,
                "file_path": str(pdf),
                "document_hash": file_hash,
                "doc_type": doc_type,
                "version_label": None,
                "effective_date": None,
                "source_tier": "T1",
                "needs_review": False,
            }
        )

    if rejected:
        print(f"  Rejected (non-legal patterns): {len(rejected)} files")

    return new_entries, dup_entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find PDFs not yet ingested into contra_corpus.db"
    )
    parser.add_argument(
        "--folder", required=True, help="Root folder to scan (recursive)"
    )
    parser.add_argument(
        "--entity", default=None, help="Entity name (override auto-inference)"
    )
    parser.add_argument(
        "--auto-entity",
        action="store_true",
        help="Infer entity from subfolder name using built-in map (for Uber Technologies Inc structure)",
    )
    parser.add_argument(
        "--db-path", default=_DEFAULT_DB, help="Path to contra_corpus.db"
    )
    parser.add_argument(
        "--manifest", default=None, help="Write new-file manifest to this path"
    )
    parser.add_argument(
        "--dup-report", default=None, help="Write duplicate report to this path"
    )
    parser.add_argument(
        "--no-ingest-check", action="store_true", help="Skip DB check (manifest only)"
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"ERROR: folder not found: {folder}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning: {folder}")
    print(f"DB: {args.db_path}")
    print()

    new_entries, dup_entries = find_new_pdfs(
        folder=folder,
        db_path=args.db_path,
        entity_name=args.entity,
        auto_entity=args.auto_entity,
    )

    total = len(new_entries) + len(dup_entries)
    print(f"Results: {total} PDFs scanned")
    print(f"  New (not in DB): {len(new_entries)}")
    print(f"  Duplicate:       {len(dup_entries)}")

    if new_entries:
        print("\nNew files to ingest:")
        for e in new_entries:
            p = Path(e["file_path"])
            print(f"  [{e['doc_type']:<24}] {e['entity_name'][:30]:<30} {p.name[:55]}")

    if args.manifest and new_entries:
        out = Path(args.manifest)
        out.write_text(json.dumps(new_entries, indent=2), encoding="utf-8")
        print(f"\nManifest written: {out} ({len(new_entries)} entries)")
        print(f"Next: python scripts/contra_batch_ingest.py --manifest {out}")

    if args.dup_report and dup_entries:
        dup_path = Path(args.dup_report)
        dup_path.write_text(json.dumps(dup_entries, indent=2), encoding="utf-8")
        print(f"DUP report written: {dup_path}")

    if not args.manifest and new_entries:
        print("\nTo ingest: re-run with --manifest <output.json>")


if __name__ == "__main__":
    main()
