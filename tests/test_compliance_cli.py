"""Tests for run_compliance_check CLI (Prompt 9.5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure src/ is importable (mirrors the script's own bootstrap)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from scripts.run_compliance_check import run_compliance_check  # noqa: E402

SAMPLE_ATLAS = Path(__file__).parent.parent / "data" / "reference" / "atlas_sample.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def source_dir_with_docs(tmp_path: Path) -> Path:
    """A source directory containing one plain-text document."""
    src = tmp_path / "sources"
    src.mkdir()
    (src / "procurement_minutes.txt").write_text(
        "Council approved purchase of surveillance system on 2023-04-15. "
        "Vendor: SecureTech. Contract amount: $250,000.",
        encoding="utf-8",
    )
    return src


@pytest.fixture()
def empty_source_dir(tmp_path: Path) -> Path:
    """An empty source directory (no documents)."""
    src = tmp_path / "empty_sources"
    src.mkdir()
    return src


# ---------------------------------------------------------------------------
# Test: CLI creates output files
# ---------------------------------------------------------------------------


def test_cli_creates_json_output(tmp_path: Path, source_dir_with_docs: Path):
    output_dir = tmp_path / "reports"
    run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=output_dir,
        jurisdiction="test_city",
    )
    json_file = output_dir / "test_city_compliance.json"
    assert json_file.exists(), "JSON output file not created"
    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert data["jurisdiction"] == "test_city"
    assert "mandate_statuses" in data
    assert len(data["mandate_statuses"]) == 11


def test_cli_creates_markdown_output(tmp_path: Path, source_dir_with_docs: Path):
    output_dir = tmp_path / "reports"
    run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=output_dir,
        jurisdiction="test_city",
    )
    md_file = output_dir / "test_city_compliance.md"
    assert md_file.exists(), "Markdown output file not created"
    content = md_file.read_text(encoding="utf-8")
    assert "test_city" in content
    assert "M-01" in content


def test_cli_output_dir_created_if_missing(tmp_path: Path, source_dir_with_docs: Path):
    output_dir = tmp_path / "deep" / "nested" / "reports"
    assert not output_dir.exists()
    run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=output_dir,
        jurisdiction="test_city",
    )
    assert output_dir.exists()


def test_cli_returns_compliance_scorecard(tmp_path: Path, source_dir_with_docs: Path):
    from oraculus_di_auditor.adapters.compliance_engine import ComplianceScorecard

    scorecard = run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=tmp_path / "out",
        jurisdiction="test_city",
    )
    assert isinstance(scorecard, ComplianceScorecard)
    assert scorecard.jurisdiction == "test_city"
    assert scorecard.total_mandates == 11


def test_cli_jurisdiction_name_in_filename(tmp_path: Path, source_dir_with_docs: Path):
    output_dir = tmp_path / "reports"
    run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=output_dir,
        jurisdiction="Riverside County",
    )
    assert (output_dir / "riverside_county_compliance.json").exists()
    assert (output_dir / "riverside_county_compliance.md").exists()


def test_cli_with_atlas_data(tmp_path: Path, source_dir_with_docs: Path):
    output_dir = tmp_path / "reports"
    scorecard = run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=output_dir,
        jurisdiction="Riverside County Sheriff",
        state="CA",
        atlas_data_path=SAMPLE_ATLAS,
    )
    # Riverside County Sheriff has 4 records in the sample
    assert len(scorecard.technology_inventory) == 4


def test_cli_has_ccops_ordinance_flag(tmp_path: Path, source_dir_with_docs: Path):
    scorecard = run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=tmp_path / "out",
        jurisdiction="test_city",
        has_ccops_ordinance=True,
    )
    assert scorecard.has_ccops_ordinance is True


# ---------------------------------------------------------------------------
# Test: CLI handles missing source directory
# ---------------------------------------------------------------------------


def test_cli_handles_missing_source_directory(tmp_path: Path):
    """Missing source dir is tolerated — all mandates become unknown."""
    nonexistent = tmp_path / "does_not_exist"
    assert not nonexistent.exists()

    scorecard = run_compliance_check(
        source_dir=nonexistent,
        output_dir=tmp_path / "out",
        jurisdiction="test_city",
    )
    # No documents ingested → no detectors ran → all unknown
    assert scorecard.unknown_count == 11
    assert scorecard.compliance_percentage == 0.0


def test_cli_handles_empty_source_directory(tmp_path: Path, empty_source_dir: Path):
    """Empty source dir is tolerated — all mandates become unknown."""
    scorecard = run_compliance_check(
        source_dir=empty_source_dir,
        output_dir=tmp_path / "out",
        jurisdiction="test_city",
    )
    assert scorecard.unknown_count == 11


def test_cli_output_json_is_valid(tmp_path: Path, source_dir_with_docs: Path):
    output_dir = tmp_path / "reports"
    run_compliance_check(
        source_dir=source_dir_with_docs,
        output_dir=output_dir,
        jurisdiction="test_city",
    )
    json_file = output_dir / "test_city_compliance.json"
    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert "overall_risk" in data
    assert "compliance_percentage" in data
    assert "assessment_date" in data
