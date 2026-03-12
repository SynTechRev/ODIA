#!/usr/bin/env python3
"""
ingest_corpus.py

Exhaustive corpus scanner that:
 - enumerates all files under oraculus/corpus/
 - merges index.json entries if present
 - deduplicates by (sha256 if present) else fallback composite key
 - writes oraculus/corpus/corpus_manifest.json with entries
"""

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

from scripts._utils import normalize_relpath, safe_int, sha256_of_file  # noqa: E402

LOG = logging.getLogger("oraculus.ingest")
logging.basicConfig(level=logging.INFO)

DEFAULT_CORPUS_ROOT = Path("oraculus/corpus")
# 50MB threshold chosen to balance hash computation safety with memory usage
# Files larger than this may strain memory on resource-constrained systems
MAX_HASH_SIZE_BYTES = 50 * 1024 * 1024


def load_index_for_corpus(corpus_dir: Path):
    idx = corpus_dir / "index.json"
    if not idx.exists():
        return None
    try:
        return json.loads(idx.read_text(encoding="utf-8"))
    except Exception as e:
        LOG.warning("Failed to parse index.json in %s: %s", corpus_dir, e)
        return None


def find_all_corpora(root: Path):
    # corpora are directories directly under root with an index.json
    # or plausible metadata.
    corpora = []
    for p in root.iterdir():
        if p.is_dir():
            corpora.append(p)
    return sorted(corpora, key=lambda x: x.name)


def scan_files_under(corpus_dir: Path):
    # yield file entries for any file inside the corpus_dir (recursive)
    for p in corpus_dir.rglob("*"):
        if p.is_file():
            yield p


def build_manifest(root: Path, force_hash=False):  # noqa: C901
    from datetime import datetime

    manifest = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "corpus_root": str(root),
        "files": [],
    }
    seen_keys = set()
    corpora = find_all_corpora(root)
    LOG.info("Found %d corpora folders", len(corpora))

    for corpus_dir in corpora:
        idx = load_index_for_corpus(corpus_dir)
        # First, merge entries from index.json if present
        if idx and isinstance(idx.get("files"), list):
            for fe in idx["files"]:
                # build normalized file entry
                file_name = fe.get("file_name") or fe.get("name") or ""
                relpath = fe.get("relative_path") or file_name
                entry = {
                    "corpus_id": idx.get("corpus_id") or corpus_dir.name,
                    "file_name": file_name,
                    "relative_path": relpath,
                    "file_hash": fe.get("file_hash"),
                    "size": fe.get("size"),
                    "source_index": True,
                }
                # dedupe using composite key
                key = (
                    entry.get("file_hash") or "",
                    entry.get("relative_path") or "",
                    entry.get("size") or 0,
                )
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                manifest["files"].append(entry)

        # Now scan the file tree to find any files not present in index.json
        for f in scan_files_under(corpus_dir):
            rel = normalize_relpath(root, f)
            # try to find if we've already included this path
            already = False
            for e in manifest["files"]:
                if e.get("relative_path") == rel:
                    already = True
                    break
            if already:
                continue

            # compute hash if available (or when forced)
            fh = None
            try:
                # Cache stat result to avoid multiple system calls
                file_stat = f.stat()
                # fast path: if file is small, compute hash
                if force_hash or file_stat.st_size < MAX_HASH_SIZE_BYTES:
                    fh = sha256_of_file(f)
            except Exception as ex:
                LOG.warning("Failed to hash %s: %s", f, ex)

            file_entry = {
                "corpus_id": corpus_dir.name,
                "file_name": f.name,
                "relative_path": rel,
                "file_hash": fh,
                "size": safe_int(file_stat.st_size if "file_stat" in locals() else 0),
                "mtime": file_stat.st_mtime if "file_stat" in locals() else None,
            }
            # dedupe: composite key
            key = (
                file_entry.get("file_hash") or "",
                file_entry.get("relative_path") or "",
                file_entry.get("size") or 0,
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            manifest["files"].append(file_entry)

    # final normalization: ensure unique
    # (seen_keys ensures uniqueness but we normalize fields)
    for e in manifest["files"]:
        if e.get("file_hash") is None:
            e["file_hash"] = ""
    return manifest


def write_manifest(manifest: dict, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    LOG.info("Wrote manifest: %s (%d files)", out_path, len(manifest.get("files", [])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--out", default="transparency_release/corpus_manifest.json")
    parser.add_argument("--force-hash", action="store_true")
    args = parser.parse_args()

    root = Path(args.corpus_root)
    if not root.exists():
        LOG.error("Corpus root not found: %s", root)
        raise SystemExit(1)

    manifest = build_manifest(root, force_hash=args.force_hash)
    write_manifest(manifest, Path(args.out))
    print(f"Manifest generated: {args.out} ({len(manifest['files'])} entries)")


# Compatibility wrappers for old tests
def scan_corpus(base_dir: Path) -> list[dict]:
    """
    Compatibility wrapper for old test interface.
    Returns list of corpus entries compatible with old format.
    """
    corpora = find_all_corpora(base_dir)
    corpus_entries = []

    for corpus_dir in corpora:
        idx = load_index_for_corpus(corpus_dir)
        corpus_entry = {
            "corpus_id": corpus_dir.name,
            "meeting_date": idx.get("meeting_date", "") if idx else "",
            "year": (
                int(idx.get("meeting_date", "2000")[:4])
                if idx and idx.get("meeting_date")
                else 0
            ),
            "files": [],
            "ingest_status": "verified",
        }

        if idx and isinstance(idx.get("files"), list):
            for fe in idx["files"]:
                corpus_entry["files"].append(
                    {
                        "name": fe.get("file_name", ""),
                        "category": fe.get("file_type", "attachment"),
                        "file_hash": fe.get("file_hash", ""),
                        "text_hash": fe.get("text_hash", ""),
                        "extraction_complete": fe.get("extraction_complete", False),
                    }
                )

        corpus_entry["file_count"] = len(corpus_entry["files"])
        corpus_entries.append(corpus_entry)

    return corpus_entries


def generate_manifest(entries: list[dict]) -> dict:
    """
    Compatibility wrapper for old test interface.
    Generates manifest from corpus entries in old format.
    """
    from datetime import UTC

    manifest = {
        "manifest_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "description": (
            "Complete file inventory for 2014-2025 California legislative corpus"
        ),
        "corpus_range": {"start_year": 2014, "end_year": 2025},
        "total_corpora": len(entries),
        "corpora": entries,
    }

    # Calculate statistics
    manifest["total_files"] = sum(c["file_count"] for c in entries)
    manifest["years_covered"] = sorted(set(c["year"] for c in entries if c["year"] > 0))

    # Add top-level files array for compatibility
    all_files = []
    for entry in entries:
        for file_info in entry.get("files", []):
            if file_info.get("name"):
                all_files.append(
                    {
                        "corpus_id": entry["corpus_id"],
                        "name": file_info["name"],
                        "file_hash": file_info.get("file_hash", ""),
                    }
                )
    manifest["files"] = all_files

    return manifest


if __name__ == "__main__":
    main()
