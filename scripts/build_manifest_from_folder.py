"""Generate a contra_manifest.json entry block from a corpus folder.

Scans a directory for PDF files, infers doc_type from filename keywords,
and appends entries to a manifest JSON file ready for contra_batch_ingest.py.

Usage:
    python scripts/build_manifest_from_folder.py --folder "D:/CONTRA Contract Corpus/T-Mobile" --entity "T-Mobile USA"
    python scripts/build_manifest_from_folder.py --folder "D:/CONTRA Contract Corpus/Meta" --entity "Meta Platforms" --recurse
    python scripts/build_manifest_from_folder.py --folder "D:/CONTRA Contract Corpus/T-Mobile" --entity "T-Mobile USA" --out contra_manifest_tmobile.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_DEFAULT_OUT = "contra_manifest.json"

_DOC_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"arbitrat|dispute|aaa|jams|notice.of.dispute", re.I), "arbitration"),
    (re.compile(r"eula|end.user.licen|software.licen", re.I), "eula"),
    (re.compile(r"privacy|ccpa|gdpr|hipaa|data.polic|cookie|cpni", re.I), "privacy_notice"),
    (re.compile(r"terms|tos|tou|subscriber|customer.agreement|service.agreement|conditions", re.I), "tos"),
]

_REJECT_PATTERNS = re.compile(
    r"apache.licen|w3c.process|law.enforcement|lumen|puc.doc|annual.report"
    r"|press.release|investor|earnings|proxy",
    re.I,
)

_CORPORATE_FAMILY_MAP = {
    "T-Mobile USA": "T-Mobile",
    "T-Mobile": "T-Mobile",
    "Meta Platforms": "Meta",
    "Facebook": "Meta",
    "Instagram": "Meta",
    "WhatsApp": "Meta",
    "Cricket Wireless": "AT&T",
    "Verizon Communications": "Verizon",
    "AT&T Inc.": "AT&T",
    "AT&T Mobility": "AT&T",
    "Google LLC": "Alphabet",
    "JPMorgan Chase": "JPMorgan Chase",
    "Chase": "JPMorgan Chase",
    "Comcast / Xfinity": "Comcast",
    "Kaiser Permanente": "Kaiser Permanente",
}


def _infer_doc_type(filename: str) -> str | None:
    if _REJECT_PATTERNS.search(filename):
        return None
    for pattern, doc_type in _DOC_TYPE_PATTERNS:
        if pattern.search(filename):
            return doc_type
    return "tos"  # default


def build(
    folder: Path,
    entity_name: str,
    recurse: bool,
    out_path: Path,
    dry_run: bool,
) -> None:
    pattern = "**/*.pdf" if recurse else "*.pdf"
    pdfs = sorted(folder.glob(pattern))

    if not pdfs:
        print(f"No PDF files found in {folder}")
        return

    corporate_family = _CORPORATE_FAMILY_MAP.get(entity_name, entity_name)

    new_entries: list[dict] = []
    skipped: list[str] = []

    for pdf in pdfs:
        doc_type = _infer_doc_type(pdf.name)
        if doc_type is None:
            skipped.append(pdf.name)
            continue

        entry = {
            "file_path": str(pdf.resolve()),
            "entity_name": entity_name,
            "corporate_family": corporate_family,
            "doc_type": doc_type,
            "doc_type_confidence": 0.75,
            "needs_review": False,
            "version_label": None,
            "effective_date": None,
            "source_url": None,
        }
        new_entries.append(entry)

        status = "DRY RUN" if dry_run else "ADD"
        print(f"  {status}  [{doc_type:<16}] {pdf.name}")

    if skipped:
        print(f"\n  Skipped (reject pattern): {len(skipped)}")
        for s in skipped:
            print(f"    - {s}")

    print(f"\n  New entries: {len(new_entries)}")

    if dry_run:
        print("\n  (dry run — manifest not written)")
        return

    # Load existing manifest if it exists
    existing: list[dict] = []
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        existing_paths = {e["file_path"] for e in existing}
        before = len(new_entries)
        new_entries = [e for e in new_entries if e["file_path"] not in existing_paths]
        if before != len(new_entries):
            print(f"  Skipped {before - len(new_entries)} already in manifest")

    combined = existing + new_entries
    out_path.write_text(
        json.dumps(combined, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Manifest written: {out_path} ({len(combined)} total entries)")
    print(f"\nNext: python scripts/contra_batch_ingest.py --manifest {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build manifest entries from a corpus folder"
    )
    parser.add_argument("--folder", required=True, help="Path to PDF folder")
    parser.add_argument("--entity", required=True, help="Canonical entity name")
    parser.add_argument(
        "--recurse", action="store_true",
        help="Scan subdirectories recursively (use for Meta with Facebook/Instagram/WhatsApp subfolders)"
    )
    parser.add_argument("--out", default=_DEFAULT_OUT, help="Output manifest JSON path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    build(
        folder=Path(args.folder),
        entity_name=args.entity,
        recurse=args.recurse,
        out_path=Path(args.out),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
