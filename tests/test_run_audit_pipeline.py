"""Tests for run_audit.py wired to the unified reporting system."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import run_audit  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEMPLATE_DIR = _REPO_ROOT / "templates"

_SAMPLE_TEXT = (
    "The program appropriates $500,000 for operations. "
    "This contract is unsigned and lacks provenance documentation. "
    "Surveillance cameras will be installed without governance review."
)


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create minimal config + source dirs for run_audit."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "jurisdiction.json").write_text(
        json.dumps({"name": "Test City", "state": "CA", "country": "US"}),
        encoding="utf-8",
    )
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "doc1.txt").write_text(_SAMPLE_TEXT, encoding="utf-8")
    output_dir = tmp_path / "output"
    return config_dir, source_dir, output_dir


# ---------------------------------------------------------------------------
# Backward compatibility — existing behavior unchanged without new flags
# ---------------------------------------------------------------------------

def test_backward_compat_creates_json_and_markdown(tmp_path: Path):
    """Without new flags, audit_report.json and audit_report.md are produced."""
    config_dir, source_dir, output_dir = _setup(tmp_path)
    report = run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
    )
    assert (output_dir / "audit_report.json").exists()
    assert (output_dir / "audit_report.md").exists()
    # Legacy report dict structure still returned
    assert "jurisdiction" in report
    assert "severity_summary" in report
    assert "document_count" in report


def test_backward_compat_json_has_expected_keys(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
    )
    data = json.loads((output_dir / "audit_report.json").read_text(encoding="utf-8"))
    # New reporting system produces AuditReport JSON
    assert "report_id" in data
    assert "report_type" in data
    assert "findings" in data


def test_backward_compat_markdown_is_nonempty(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
    )
    md = (output_dir / "audit_report.md").read_text(encoding="utf-8")
    assert len(md) > 100
    assert "Test City" in md


# ---------------------------------------------------------------------------
# --formats flag
# ---------------------------------------------------------------------------

def test_formats_json_only(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        formats=["json"],
    )
    assert (output_dir / "audit_report.json").exists()
    assert not (output_dir / "audit_report.md").exists()


def test_formats_json_and_markdown(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        formats=["json", "markdown"],
    )
    assert (output_dir / "audit_report.json").exists()
    assert (output_dir / "audit_report.md").exists()


def test_formats_html_creates_html_file(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        formats=["markdown", "html"],
    )
    assert (output_dir / "audit_report.html").exists()
    html = (output_dir / "audit_report.html").read_text(encoding="utf-8")
    assert "<" in html  # some HTML produced


# ---------------------------------------------------------------------------
# --executive flag
# ---------------------------------------------------------------------------

def test_executive_flag_creates_executive_report(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        executive=True,
    )
    assert (output_dir / "audit_report_executive.md").exists()


def test_executive_report_is_shorter_than_full(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        formats=["markdown"],
        executive=True,
    )
    full = (output_dir / "audit_report.md").read_text(encoding="utf-8")
    exec_md = (output_dir / "audit_report_executive.md").read_text(encoding="utf-8")
    assert len(exec_md) < len(full)


def test_executive_flag_does_not_replace_full_report(tmp_path: Path):
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        formats=["json", "markdown"],
        executive=True,
    )
    assert (output_dir / "audit_report.json").exists()
    assert (output_dir / "audit_report.md").exists()
    assert (output_dir / "audit_report_executive.md").exists()


# ---------------------------------------------------------------------------
# --template flag
# ---------------------------------------------------------------------------

def test_custom_template_name(tmp_path: Path):
    """Passing a different template name renders that template."""
    config_dir, source_dir, output_dir = _setup(tmp_path)
    run_audit.run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        formats=["markdown"],
        template_name="audit_report.md",
        template_dir=TEMPLATE_DIR,
    )
    md = (output_dir / "audit_report.md").read_text(encoding="utf-8")
    assert len(md) > 0


# ---------------------------------------------------------------------------
# Error handling (inherited from existing behavior)
# ---------------------------------------------------------------------------

def test_missing_source_dir_raises(tmp_path: Path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "jurisdiction.json").write_text(
        json.dumps({"name": "Test", "state": "CA", "country": "US"}), encoding="utf-8"
    )
    with pytest.raises(FileNotFoundError):
        run_audit.run_audit(
            config_dir=config_dir,
            source_dir=tmp_path / "nonexistent",
            output_dir=tmp_path / "output",
        )
