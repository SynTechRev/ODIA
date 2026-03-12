#!/usr/bin/env python3
"""
Oraculus DI Auditor - Triage Script

Minimal dependency CLI tool to create and update document manifests.
Provides audit triage capabilities with flag management and chain-of-custody tracking.

Usage:
    python scripts/triage.py --doc-id DOC123 --path /path/to/file.pdf \\
        --flag "DOJ certification missing" --severity high --author "Your Name" \\
        --note "Document requires legal review"
"""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ManifestManager:
    """Manages document manifest creation and updates."""

    def __init__(self, manifests_dir: str = "manifests"):
        self.manifests_dir = Path(manifests_dir)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        self.schema_path = Path("audit_manifest.schema.json")

    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
            return "FILE_NOT_FOUND"
        except Exception as e:
            print(f"Warning: Error calculating checksum: {e}")
            return "ERROR_CALCULATING_CHECKSUM"

    def load_or_create_manifest(self, doc_id: str) -> dict[str, Any]:
        """Load existing manifest or create a new one."""
        manifest_path = self.manifests_dir / f"{doc_id}.json"

        if manifest_path.exists():
            with open(manifest_path) as f:
                return json.load(f)

        # Create new manifest with required fields
        return {
            "document_id": doc_id,
            "source": "manual_triage",
            "original_path": "",
            "ingest_date": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "uploader": "system",
            "checksum_sha256": "",
            "extraction": {"text_present": False},
            "flags": [],
            "citations": [],
            "notes": [],
            "chain_of_custody": [],
        }

    def add_flag(
        self,
        manifest: dict[str, Any],
        message: str,
        severity: str,
        author: str,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Add an audit flag to the manifest."""
        flag_id = f"FLAG_{len(manifest.get('flags', [])) + 1:04d}"
        flag = {
            "flag_id": flag_id,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "author": author,
        }
        if category:
            flag["category"] = category

        if "flags" not in manifest:
            manifest["flags"] = []
        manifest["flags"].append(flag)

        return manifest

    def add_note(
        self, manifest: dict[str, Any], note: str, author: str
    ) -> dict[str, Any]:
        """Add an audit note to the manifest."""
        note_entry = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "author": author,
            "note": note,
        }
        if "notes" not in manifest:
            manifest["notes"] = []
        manifest["notes"].append(note_entry)

        return manifest

    def add_custody_entry(
        self, manifest: dict[str, Any], actor: str, action: str, details: str = ""
    ) -> dict[str, Any]:
        """Add a chain-of-custody entry."""
        custody_entry = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "actor": actor,
            "action": action,
            "details": details,
        }
        if "chain_of_custody" not in manifest:
            manifest["chain_of_custody"] = []
        manifest["chain_of_custody"].append(custody_entry)

        return manifest

    def update_file_info(
        self, manifest: dict[str, Any], file_path: Path, author: str
    ) -> dict[str, Any]:
        """Update manifest with file information."""
        manifest["original_path"] = str(file_path)
        manifest["checksum_sha256"] = self.calculate_checksum(file_path)

        # Update chain of custody
        if file_path.exists():
            details = f"File size: {file_path.stat().st_size} bytes"
        else:
            details = "File path recorded (file not accessible)"

        self.add_custody_entry(manifest, author, "file_reference_updated", details)

        return manifest

    def save_manifest(self, doc_id: str, manifest: dict[str, Any]) -> Path:
        """Save manifest to disk."""
        manifest_path = self.manifests_dir / f"{doc_id}.json"

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return manifest_path

    def validate_severity(self, severity: str) -> bool:
        """Validate severity level."""
        valid_severities = ["low", "medium", "high", "critical"]
        return severity.lower() in valid_severities


def main():
    parser = argparse.ArgumentParser(
        description="Oraculus DI Auditor - Document Triage Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new manifest with flag
  python scripts/triage.py --doc-id DOC123 --path /storage/file.pdf \\
      --flag "Missing DOJ certification" --severity high --author "Jane Doe"

  # Add note to existing manifest
  python scripts/triage.py --doc-id DOC123 --author "John Smith" \\
      --note "Requires legal team review"

  # Update file path and checksum
  python scripts/triage.py --doc-id DOC123 --path /storage/file.pdf --author "System"
        """,
    )

    parser.add_argument(
        "--doc-id", required=True, help="Document ID (e.g., DOC123, FDA_2024_001)"
    )
    parser.add_argument(
        "--path", type=str, help="Path to the original PDF or document file"
    )
    parser.add_argument("--source", type=str, help="Document source or origin system")
    parser.add_argument("--uploader", type=str, help="Name of person who uploaded")
    parser.add_argument("--flag", type=str, help="Add an audit flag/finding")
    parser.add_argument(
        "--severity",
        type=str,
        choices=["low", "medium", "high", "critical"],
        help="Severity level (required with --flag)",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Flag category (e.g., doj_certification, irb_consent)",
    )
    parser.add_argument("--note", type=str, help="Add an audit note or observation")
    parser.add_argument(
        "--author", required=True, help="Your name or identifier (required)"
    )
    parser.add_argument(
        "--manifests-dir",
        type=str,
        default="manifests",
        help="Directory to store manifests (default: manifests)",
    )

    args = parser.parse_args()

    # Validate flag/severity combination
    if args.flag and not args.severity:
        print("Error: --severity is required when adding a flag", file=sys.stderr)
        sys.exit(1)

    # Initialize manager
    manager = ManifestManager(manifests_dir=args.manifests_dir)

    # Track if this is a new manifest (check before loading)
    manifest_path = manager.manifests_dir / f"{args.doc_id}.json"
    is_new = not manifest_path.exists()

    # Load or create manifest
    print(f"Processing document: {args.doc_id}")
    manifest = manager.load_or_create_manifest(args.doc_id)

    # Update manifest fields
    if args.source:
        manifest["source"] = args.source

    if args.uploader:
        manifest["uploader"] = args.uploader

    if args.path:
        file_path = Path(args.path)
        manifest = manager.update_file_info(manifest, file_path, args.author)
        print(f"  Updated file path: {args.path}")
        print(f"  Checksum: {manifest['checksum_sha256']}")

    # Add flag if provided
    if args.flag:
        manifest = manager.add_flag(
            manifest, args.flag, args.severity, args.author, args.category
        )
        print(f"  Added flag: {args.flag} (severity: {args.severity})")

    # Add note if provided
    if args.note:
        manifest = manager.add_note(manifest, args.note, args.author)
        print(f"  Added note: {args.note[:50]}...")

    # Add custody entry for this operation
    action = "manifest_created" if is_new else "manifest_updated"
    details = "via triage.py"
    manifest = manager.add_custody_entry(manifest, args.author, action, details)

    # Save manifest
    manifest_path = manager.save_manifest(args.doc_id, manifest)
    print(f"  Saved manifest: {manifest_path}")

    # Summary
    print("\nManifest Summary:")
    print(f"  Document ID: {manifest['document_id']}")
    print(f"  Source: {manifest['source']}")
    print(f"  Flags: {len(manifest.get('flags', []))}")
    print(f"  Notes: {len(manifest.get('notes', []))}")
    print(f"  Custody entries: {len(manifest.get('chain_of_custody', []))}")

    if manifest.get("flags"):
        print("\n  Recent flags:")
        for flag in manifest["flags"][-3:]:
            severity = flag["severity"].upper()
            message = flag["message"]
            author = flag["author"]
            print(f"    - [{severity}] {message} (by {author})")

    print("\n[OK] Triage complete")


if __name__ == "__main__":
    main()
