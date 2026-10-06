"""CONTRA needs-review queue processor.

Reads the 32 (or more) entries flagged needs_review=True in a manifest,
presents each one interactively for human classification, then writes a
corrected manifest ready to feed contra_batch_ingest.py.

Usage:
    python scripts/needs_review_processor.py --manifest contra_manifest.json
    python scripts/needs_review_processor.py --manifest contra_manifest.json --auto-reject-low
    python scripts/needs_review_processor.py --show-queue  # list without processing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_VALID_DOC_TYPES = ["tos", "privacy_notice", "eula", "arbitration", "reject"]

_DOC_TYPE_LABELS = {
    "tos": "Terms of Service / Subscriber / Customer Agreement",
    "privacy_notice": "Privacy Notice / Policy / HIPAA NPP / CCPA disclosure",
    "eula": "End-User License Agreement / Software License",
    "arbitration": "Arbitration / Dispute Form",
    "reject": "REJECT (remove from corpus entirely)",
}

_CHECKPOINT_FILE = Path("cache/needs_review_checkpoint.json")


def _load_checkpoint() -> set[str]:
    if _CHECKPOINT_FILE.exists():
        data = json.loads(_CHECKPOINT_FILE.read_text(encoding="utf-8"))
        return set(data.get("processed_paths", []))
    return set()


def _save_checkpoint(processed: set[str]) -> None:
    _CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CHECKPOINT_FILE.write_text(
        json.dumps({"processed_paths": sorted(processed)}, indent=2),
        encoding="utf-8",
    )


def _show_queue(entries: list[dict]) -> None:
    needs_review = [e for e in entries if e.get("needs_review")]
    print(f"\n{len(needs_review)} entries flagged needs_review=True:\n")
    for i, e in enumerate(needs_review, 1):
        conf = e.get("doc_type_confidence", 0)
        print(
            f"  [{i:>3}] {e['entity_name']:<30} "
            f"{e['doc_type']:<16} conf={conf:.2f}  "
            f"{Path(e['file_path']).name[:50]}"
        )


def _prompt_classification(entry: dict, idx: int, total: int) -> str | None:
    """Prompt user to classify one document. Returns new doc_type, 'skip', or 'quit'."""
    path = Path(entry["file_path"])
    inferred = entry["doc_type"]
    conf = entry.get("doc_type_confidence", 0)

    print(f"\n{'='*70}")
    print(f"  [{idx}/{total}] {entry['entity_name']}")
    print(f"  File : {path.name}")
    print(f"  Inferred : {inferred} (confidence={conf:.2f})")
    print()
    for key, label in _DOC_TYPE_LABELS.items():
        marker = " <-- inferred (Enter to confirm)" if key == inferred else ""
        print(f"    {key:<16}  {label}{marker}")
    print()
    print(
        "  Enter=confirm inferred | tos | privacy_notice | eula | arbitration | reject"
    )
    print("  s=skip (keep needs_review=True) | q=quit")
    print()

    while True:
        try:
            raw = input("  Choice > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"

        if raw in ("q", "quit"):
            return "quit"
        if raw in ("s", "skip"):
            return "skip"
        if raw == "":
            # Enter confirms the inferred type
            print(f"  Confirmed: {inferred}")
            return inferred
        if raw in _VALID_DOC_TYPES:
            return raw
        print(
            f"  Invalid choice '{raw}'. Enter one of: tos, privacy_notice, eula, arbitration, reject, s, q"
        )


def process_queue(
    manifest_path: Path,
    auto_reject_low: bool = False,
    show_only: bool = False,
    confirm_all: bool = False,
) -> None:
    manifest: list[dict] = json.loads(manifest_path.read_text(encoding="utf-8"))
    needs_review = [e for e in manifest if e.get("needs_review")]

    if show_only:
        _show_queue(manifest)
        return

    if not needs_review:
        print("No entries flagged needs_review=True. Nothing to process.")
        return

    print(f"\nLoaded {len(manifest)} total entries, {len(needs_review)} need review.")

    checkpoint = _load_checkpoint()
    remaining = [e for e in needs_review if e["file_path"] not in checkpoint]

    if checkpoint:
        done = len(needs_review) - len(remaining)
        print(f"  Resuming: {done} already processed, {len(remaining)} remaining.")

    if not remaining:
        print("All flagged entries have been processed. Writing corrected manifest.")
    else:
        print(f"\nProcessing {len(remaining)} entries. Enter choices as prompted.\n")

    corrections: dict[str, str] = {}
    rejects: set[str] = set()

    for i, entry in enumerate(remaining, 1):
        file_path = entry["file_path"]

        # Auto-reject if confidence < 0.2 and flag set
        if auto_reject_low and entry.get("doc_type_confidence", 1.0) < 0.2:
            print(f"  AUTO-REJECT (conf<0.2): {Path(file_path).name}")
            rejects.add(file_path)
            checkpoint.add(file_path)
            _save_checkpoint(checkpoint)
            continue

        # Auto-confirm inferred type for all entries
        if confirm_all:
            inferred = entry["doc_type"]
            print(
                f"  AUTO-CONFIRM [{i:>2}/{len(remaining)}] {entry['entity_name']} - {Path(file_path).name[:55]} -> {inferred}"
            )
            corrections[file_path] = inferred
            checkpoint.add(file_path)
            _save_checkpoint(checkpoint)
            continue

        choice = _prompt_classification(entry, i, len(remaining))

        if choice == "quit":
            print("\nSaving progress and exiting.")
            _save_checkpoint(checkpoint)
            break

        if choice == "skip":
            continue

        if choice == "reject":
            rejects.add(file_path)
        else:
            corrections[file_path] = choice

        checkpoint.add(file_path)
        _save_checkpoint(checkpoint)

    # Apply corrections to manifest
    rejected_count = 0
    corrected_count = 0
    output_manifest = []
    for entry in manifest:
        fp = entry["file_path"]
        if fp in rejects:
            rejected_count += 1
            continue  # drop from manifest
        if fp in corrections:
            entry = dict(entry)
            entry["doc_type"] = corrections[fp]
            entry["doc_type_confidence"] = 1.0  # human-reviewed
            entry["needs_review"] = False
            corrected_count += 1
        output_manifest.append(entry)

    out_path = manifest_path.with_stem(manifest_path.stem + "_reviewed")
    out_path.write_text(
        json.dumps(output_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n-- Queue Processor Results --")
    print(f"  Corrected : {corrected_count}")
    print(f"  Rejected  : {rejected_count}")
    print(f"  Skipped   : {len(needs_review) - corrected_count - rejected_count}")
    print(f"\nReviewed manifest written to: {out_path}")
    print(
        "Feed this manifest to: python scripts/contra_batch_ingest.py --manifest",
        out_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="CONTRA needs-review queue processor")
    parser.add_argument("--manifest", default="contra_manifest.json")
    parser.add_argument(
        "--show-queue",
        action="store_true",
        help="List flagged entries without processing",
    )
    parser.add_argument(
        "--auto-reject-low",
        action="store_true",
        help="Automatically reject entries with doc_type_confidence < 0.2",
    )
    parser.add_argument(
        "--confirm-all",
        action="store_true",
        help="Auto-confirm every entry's inferred doc_type without prompting (fastest path)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    process_queue(
        manifest_path,
        auto_reject_low=args.auto_reject_low,
        show_only=args.show_queue,
        confirm_all=args.confirm_all,
    )


if __name__ == "__main__":
    main()
