#!/usr/bin/env python3
"""Cross-platform normalization for corpus files.

This script ensures cross-platform compatibility by:
- Normalizing line endings (CRLF → LF)
- Checking file permissions
- Detecting path case sensitivity issues

Usage:
    python scripts/cross_platform_normalize.py [--corpus-root CORPUS_ROOT]

Author: GitHub Copilot Agent
Date: 2025-11-25
"""

import argparse
import os
import stat
import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

from scripts.corpus_manager import (
    HIST_FILES,
    REQUIRED_SUBDIRS,
    check_cross_platform_compatibility,
    normalize_line_endings,
)

# Standard Unix permissions
# Directory: rwxr-xr-x (755) - owner can read/write/execute, others can read/execute
DIRECTORY_PERMISSIONS = (
    stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
)
# File: rw-r--r-- (644) - owner can read/write, others can read
FILE_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH


def check_file_permissions(corpus_root: Path) -> dict:
    """Check file and directory permissions for cross-platform issues.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with permission check results
    """
    results = {
        "directories": [],
        "files": [],
        "issues": [],
    }

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        # Check directory permissions
        for subdir in REQUIRED_SUBDIRS:
            subdir_path = corpus_path / subdir
            if subdir_path.exists():
                mode = subdir_path.stat().st_mode
                results["directories"].append(
                    {
                        "path": str(subdir_path),
                        "mode": oct(mode),
                        "readable": os.access(subdir_path, os.R_OK),
                        "writable": os.access(subdir_path, os.W_OK),
                        "executable": os.access(subdir_path, os.X_OK),
                    }
                )

                if not os.access(subdir_path, os.R_OK | os.W_OK):
                    results["issues"].append(
                        {
                            "path": str(subdir_path),
                            "type": "directory",
                            "issue": "Insufficient permissions (need read+write)",
                        }
                    )

        # Check metadata files
        metadata_path = corpus_path / "metadata"
        if metadata_path.exists():
            for json_file in metadata_path.glob("*.json"):
                mode = json_file.stat().st_mode
                results["files"].append(
                    {
                        "path": str(json_file),
                        "mode": oct(mode),
                        "readable": os.access(json_file, os.R_OK),
                        "writable": os.access(json_file, os.W_OK),
                    }
                )

                if not os.access(json_file, os.R_OK):
                    results["issues"].append(
                        {
                            "path": str(json_file),
                            "type": "file",
                            "issue": "Not readable",
                        }
                    )

    return results


def fix_file_permissions(corpus_root: Path, fix: bool = False) -> dict:
    """Fix file permissions for cross-platform compatibility.

    Args:
        corpus_root: Root path for corpus directories
        fix: If True, actually fix the permissions

    Returns:
        Dictionary with fix results
    """
    results = {
        "checked": 0,
        "fixed": 0,
        "errors": [],
    }

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        # Process both directory and file permissions in a single loop
        for subdir in REQUIRED_SUBDIRS:
            subdir_path = corpus_path / subdir
            if not subdir_path.exists():
                continue

            # Fix directory permissions
            results["checked"] += 1
            try:
                current_mode = subdir_path.stat().st_mode & 0o777
                target_mode = DIRECTORY_PERMISSIONS & 0o777
                if fix and current_mode != target_mode:
                    os.chmod(subdir_path, DIRECTORY_PERMISSIONS)
                    results["fixed"] += 1
            except OSError as e:
                results["errors"].append(
                    {
                        "path": str(subdir_path),
                        "error": str(e),
                    }
                )

            # Fix file permissions within this directory
            for file_path in subdir_path.iterdir():
                if file_path.is_file():
                    results["checked"] += 1
                    try:
                        current_mode = file_path.stat().st_mode & 0o777
                        target_mode = FILE_PERMISSIONS & 0o777
                        if fix and current_mode != target_mode:
                            os.chmod(file_path, FILE_PERMISSIONS)
                            results["fixed"] += 1
                    except OSError as e:
                        results["errors"].append(
                            {
                                "path": str(file_path),
                                "error": str(e),
                            }
                        )

    return results


def detect_path_case_issues(corpus_root: Path) -> dict:
    """Detect potential path case sensitivity issues.

    On case-insensitive filesystems (Windows, macOS default), files
    with different cases are the same. This detects such issues.

    Args:
        corpus_root: Root path for corpus directories

    Returns:
        Dictionary with case issue detection results
    """
    results = {
        "potential_conflicts": [],
        "checked_paths": 0,
    }

    seen_paths = {}

    for hist_id in HIST_FILES:
        corpus_path = corpus_root / hist_id
        if not corpus_path.exists():
            continue

        for subdir in REQUIRED_SUBDIRS:
            subdir_path = corpus_path / subdir
            if not subdir_path.exists():
                continue

            for file_path in subdir_path.iterdir():
                results["checked_paths"] += 1
                normalized = str(file_path).lower()

                if normalized in seen_paths:
                    results["potential_conflicts"].append(
                        {
                            "path1": seen_paths[normalized],
                            "path2": str(file_path),
                            "issue": "Case sensitivity conflict",
                        }
                    )
                else:
                    seen_paths[normalized] = str(file_path)

    return results


def main():
    """Run cross-platform normalization."""
    parser = argparse.ArgumentParser(
        description="Cross-platform normalization for corpus files"
    )
    parser.add_argument(
        "--corpus-root",
        type=str,
        default="oraculus/corpus",
        help="Root directory for corpus files",
    )
    parser.add_argument(
        "--fix-line-endings",
        action="store_true",
        help="Normalize line endings (CRLF → LF)",
    )
    parser.add_argument(
        "--fix-permissions",
        action="store_true",
        help="Fix file permissions for cross-platform compatibility",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()

    print("=" * 70)
    print("CROSS-PLATFORM NORMALIZATION")
    print("=" * 70)

    if not corpus_root.exists():
        print(f"\n✗ Corpus root not found: {corpus_root}")
        return 1

    exit_code = 0

    # Step 1: Check compatibility
    print("\n[1/4] Checking cross-platform compatibility...")
    compat = check_cross_platform_compatibility(corpus_root)

    if compat["permission_issues"]:
        print(f"  ⚠ Permission issues found: {len(compat['permission_issues'])}")
        if args.verbose:
            for issue in compat["permission_issues"]:
                print(f"    - {issue['hist_id']}: {issue['path']}")
    else:
        print("  ✓ No permission issues detected")

    if compat["line_ending_issues"]:
        print(f"  ⚠ Line ending issues found: {len(compat['line_ending_issues'])}")
        if args.verbose:
            for issue in compat["line_ending_issues"][:10]:
                print(f"    - {issue['path']}: {issue['issue']}")
    else:
        print("  ✓ No line ending issues detected")

    # Step 2: Check file permissions
    print("\n[2/4] Checking file permissions...")
    perms = check_file_permissions(corpus_root)
    print(f"  Directories checked: {len(perms['directories'])}")
    print(f"  Files checked: {len(perms['files'])}")

    if perms["issues"]:
        print(f"  ⚠ Permission issues: {len(perms['issues'])}")
        exit_code = 1
        if args.verbose:
            for issue in perms["issues"]:
                print(f"    - {issue['path']}: {issue['issue']}")
    else:
        print("  ✓ All permissions OK")

    # Step 3: Check for path case issues
    print("\n[3/4] Checking for path case sensitivity issues...")
    case_issues = detect_path_case_issues(corpus_root)
    print(f"  Paths checked: {case_issues['checked_paths']}")

    if case_issues["potential_conflicts"]:
        print(f"  ⚠ Potential conflicts: {len(case_issues['potential_conflicts'])}")
        exit_code = 1
        if args.verbose:
            for conflict in case_issues["potential_conflicts"]:
                print(f"    - {conflict['path1']} vs {conflict['path2']}")
    else:
        print("  ✓ No case sensitivity issues detected")

    # Step 4: Apply fixes if requested
    print("\n[4/4] Applying fixes...")

    if args.fix_line_endings:
        print("  Normalizing line endings...")
        stats = normalize_line_endings(corpus_root)
        print(f"    Files checked: {stats['files_checked']}")
        print(f"    Files normalized: {stats['files_normalized']}")
    else:
        print("  (Skipping line ending normalization - use --fix-line-endings)")

    if args.fix_permissions:
        print("  Fixing file permissions...")
        fix_results = fix_file_permissions(corpus_root, fix=True)
        print(f"    Items checked: {fix_results['checked']}")
        print(f"    Items fixed: {fix_results['fixed']}")
        if fix_results["errors"]:
            print(f"    Errors: {len(fix_results['errors'])}")
            exit_code = 1
    else:
        print("  (Skipping permission fixes - use --fix-permissions)")

    # Final summary
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ NORMALIZATION COMPLETE")
    else:
        print("⚠ NORMALIZATION COMPLETED WITH ISSUES")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
