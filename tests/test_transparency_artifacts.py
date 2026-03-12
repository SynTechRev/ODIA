#!/usr/bin/env python3
"""
Test for transparency release artifacts.

Ensures ALL_AUDIT_FULL.txt is generated and meets minimum size requirements.
"""

import sys
from pathlib import Path

import pytest

# Add repo root to path
_test_dir = Path(__file__).parent
_repo_root = _test_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))


def test_all_audit_full_exists():
    """Test that ALL_AUDIT_FULL.txt exists."""
    audit_file = _repo_root / "transparency_release" / "ALL_AUDIT_FULL.txt"
    assert audit_file.exists(), "ALL_AUDIT_FULL.txt not found"


def test_all_audit_full_minimum_size():
    """Test that ALL_AUDIT_FULL.txt is at least 10KB (sanity check)."""
    audit_file = _repo_root / "transparency_release" / "ALL_AUDIT_FULL.txt"
    assert audit_file.exists(), "ALL_AUDIT_FULL.txt not found"

    file_size = audit_file.stat().st_size
    min_size = 10 * 1024  # 10KB

    assert (
        file_size >= min_size
    ), f"ALL_AUDIT_FULL.txt is too small: {file_size} bytes (minimum {min_size} bytes)"


def test_all_audit_full_no_unknown():
    """Test that ALL_AUDIT_FULL.txt contains no 'unknown' or 'None' data values."""
    audit_file = _repo_root / "transparency_release" / "ALL_AUDIT_FULL.txt"
    assert audit_file.exists(), "ALL_AUDIT_FULL.txt not found"

    content = audit_file.read_text(encoding="utf-8")

    # Look for lines with data values (contain colon)
    import re

    # Pattern to match data lines like "- Field: value" where value is unknown/None
    unknown_pattern = re.compile(
        r"^[- ]*[^:]+:\s*(unknown|None)\s*$", re.IGNORECASE | re.MULTILINE
    )

    unknown_matches = list(unknown_pattern.finditer(content))

    error_msg = []
    if unknown_matches:
        error_msg.append(f"Found {len(unknown_matches)} 'unknown/None' data values:")
        for match in unknown_matches[:5]:
            line_num = content[: match.start()].count("\n") + 1
            error_msg.append(f"  Line {line_num}: {match.group().strip()}")

    assert not error_msg, "\n".join(error_msg)


def test_all_audit_full_has_required_sections():
    """Test that ALL_AUDIT_FULL.txt contains required sections."""
    audit_file = _repo_root / "transparency_release" / "ALL_AUDIT_FULL.txt"
    assert audit_file.exists(), "ALL_AUDIT_FULL.txt not found"

    content = audit_file.read_text(encoding="utf-8")

    required_sections = [
        "EXECUTIVE SUMMARY",
        "METHODOLOGY",
        "ANOMALIES & INCONSISTENCIES",
        "RECOMMENDATIONS",
    ]

    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    assert (
        not missing_sections
    ), f"Missing required sections: {', '.join(missing_sections)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
