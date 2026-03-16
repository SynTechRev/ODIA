"""Tests for run_temporal_analysis.py CLI script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "run_temporal_analysis.py"
REPO_ROOT = Path(__file__).parent.parent


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO_ROOT),
        timeout=60,
    )


# ---------------------------------------------------------------------------
# Test: output files created
# ---------------------------------------------------------------------------


def test_cli_creates_output_files(tmp_path: Path) -> None:
    """CLI writes timeline.json and timeline.md when given documents."""
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    output_dir = tmp_path / "output"

    # Write a simple test document
    doc = {
        "id": "d1",
        "vendor": "TestVendor",
        "date": "2021-03-01",
        "document_type": "original",
        "amount": 100000.0,
        "title": "Original contract",
    }
    (source_dir / "doc1.json").write_text(json.dumps(doc), encoding="utf-8")

    result = _run(
        [
            "--source",
            str(source_dir),
            "--output",
            str(output_dir),
            "--format",
            "json,markdown",
        ]
    )

    assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
    assert (output_dir / "timeline.json").exists()
    assert (output_dir / "timeline.md").exists()
    assert (output_dir / "growth_chart.json").exists()

    # Validate JSON is well-formed
    data = json.loads((output_dir / "timeline.json").read_text(encoding="utf-8"))
    assert "tracks" in data
    assert "patterns" in data


def test_cli_json_only_format(tmp_path: Path) -> None:
    """CLI with --format json creates only JSON files."""
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    output_dir = tmp_path / "output"

    doc = {"id": "d1", "vendor": "V1", "date": "2022-01-01", "amount": 50000.0}
    (source_dir / "doc1.json").write_text(json.dumps(doc), encoding="utf-8")

    result = _run(
        ["--source", str(source_dir), "--output", str(output_dir), "--format", "json"]
    )

    assert result.returncode == 0
    assert (output_dir / "timeline.json").exists()
    assert not (output_dir / "timeline.md").exists()


# ---------------------------------------------------------------------------
# Test: handles missing / empty source directory
# ---------------------------------------------------------------------------


def test_cli_handles_missing_source_directory(tmp_path: Path) -> None:
    """CLI exits cleanly with 0 when source dir does not exist."""
    missing = tmp_path / "nonexistent"
    output_dir = tmp_path / "output"

    result = _run(["--source", str(missing), "--output", str(output_dir)])

    assert result.returncode == 0
    # Should write empty placeholder files
    assert (output_dir / "timeline.json").exists()


def test_cli_handles_empty_source_directory(tmp_path: Path) -> None:
    """CLI exits cleanly with 0 and placeholder files when source dir is empty."""
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    output_dir = tmp_path / "output"

    result = _run(["--source", str(source_dir), "--output", str(output_dir)])

    assert result.returncode == 0
    assert (output_dir / "timeline.json").exists()
