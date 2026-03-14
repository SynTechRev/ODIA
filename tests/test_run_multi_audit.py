"""Tests for scripts/run_multi_audit.py."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make scripts/ importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import run_multi_audit  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_jurisdiction_config(config_dir: Path, jid: str, name: str) -> None:
    d = config_dir / jid
    d.mkdir(parents=True, exist_ok=True)
    (d / "jurisdiction.json").write_text(
        json.dumps({"name": name, "state": "CA", "country": "US"}),
        encoding="utf-8",
    )


def _write_doc(source_dir: Path, jid: str, filename: str, text: str) -> None:
    d = source_dir / jid
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_text(text, encoding="utf-8")


def _make_args(
    config_dir: Path,
    source_dir: Path,
    output_dir: Path,
    *,
    verbose: bool = False,
    jurisdictions: str = "",
) -> argparse.Namespace:
    return argparse.Namespace(
        config_dir=str(config_dir),
        source_dir=str(source_dir),
        output=str(output_dir),
        verbose=verbose,
        jurisdictions=jurisdictions,
    )


# ---------------------------------------------------------------------------
# Test: CLI creates output files
# ---------------------------------------------------------------------------


def test_cli_creates_json_and_markdown_output(tmp_path: Path):
    config_dir = tmp_path / "config"
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"

    _write_jurisdiction_config(config_dir, "city_a", "City A")
    _write_jurisdiction_config(config_dir, "city_b", "City B")
    _write_doc(source_dir, "city_a", "doc1.txt", "Policy document text.")
    _write_doc(
        source_dir,
        "city_b",
        "doc1.txt",
        "The program receives $1,000,000 for operations.",
    )

    exit_code = run_multi_audit.run(_make_args(config_dir, source_dir, output_dir))

    assert exit_code == 0
    output_files = list(output_dir.iterdir())
    assert any(f.suffix == ".json" for f in output_files), "No JSON report created"
    assert any(f.suffix == ".md" for f in output_files), "No Markdown report created"


def test_cli_json_report_has_expected_structure(tmp_path: Path):
    config_dir = tmp_path / "config"
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"

    _write_jurisdiction_config(config_dir, "city_a", "City A")
    _write_doc(source_dir, "city_a", "doc.txt", "Routine policy text here.")

    run_multi_audit.run(_make_args(config_dir, source_dir, output_dir))

    json_files = list(output_dir.glob("*.json"))
    assert json_files
    report = json.loads(json_files[0].read_text(encoding="utf-8"))

    assert report["report_type"] == "multi_jurisdiction_comparison"
    assert "jurisdictions" in report
    assert "risk_ranking" in report


# ---------------------------------------------------------------------------
# Test: handles missing source directory gracefully
# ---------------------------------------------------------------------------


def test_cli_missing_source_dir_returns_empty_results(tmp_path: Path):
    config_dir = tmp_path / "config"
    source_dir = tmp_path / "nonexistent_source"
    output_dir = tmp_path / "output"

    _write_jurisdiction_config(config_dir, "city_a", "City A")

    # Should not crash; exit 0 with zero-document results
    exit_code = run_multi_audit.run(
        _make_args(config_dir, source_dir, output_dir, verbose=True)
    )
    assert exit_code == 0

    json_files = list(output_dir.glob("*.json"))
    assert json_files
    report = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert report["jurisdictions"]["city_a"]["document_count"] == 0


def test_cli_missing_config_dir_returns_error(tmp_path: Path):
    config_dir = tmp_path / "no_config"
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"

    exit_code = run_multi_audit.run(_make_args(config_dir, source_dir, output_dir))
    assert exit_code == 1


# ---------------------------------------------------------------------------
# Test: --jurisdictions flag filters correctly
# ---------------------------------------------------------------------------


def test_jurisdictions_flag_filters_to_requested_ids(tmp_path: Path):
    config_dir = tmp_path / "config"
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"

    for jid, name in [("city_a", "City A"), ("city_b", "City B"), ("city_c", "City C")]:
        _write_jurisdiction_config(config_dir, jid, name)
        _write_doc(source_dir, jid, "doc.txt", "Some text.")

    exit_code = run_multi_audit.run(
        _make_args(config_dir, source_dir, output_dir, jurisdictions="city_a,city_b")
    )
    assert exit_code == 0

    json_files = list(output_dir.glob("*.json"))
    report = json.loads(json_files[0].read_text(encoding="utf-8"))

    assert "city_a" in report["jurisdictions"]
    assert "city_b" in report["jurisdictions"]
    assert "city_c" not in report["jurisdictions"]


def test_jurisdictions_flag_unknown_id_is_warned_not_crashed(tmp_path: Path):
    config_dir = tmp_path / "config"
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"

    _write_jurisdiction_config(config_dir, "city_a", "City A")
    _write_doc(source_dir, "city_a", "doc.txt", "Text.")

    exit_code = run_multi_audit.run(
        _make_args(
            config_dir,
            source_dir,
            output_dir,
            jurisdictions="city_a,does_not_exist",
        )
    )
    assert exit_code == 0

    json_files = list(output_dir.glob("*.json"))
    report = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert "city_a" in report["jurisdictions"]


def test_jurisdictions_flag_all_unknown_returns_error(tmp_path: Path):
    config_dir = tmp_path / "config"
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"

    _write_jurisdiction_config(config_dir, "city_a", "City A")

    exit_code = run_multi_audit.run(
        _make_args(config_dir, source_dir, output_dir, jurisdictions="does_not_exist")
    )
    assert exit_code == 1


# ---------------------------------------------------------------------------
# Test: ingest helpers
# ---------------------------------------------------------------------------


def test_ingest_txt_file(tmp_path: Path):
    f = tmp_path / "test.txt"
    f.write_text("Hello world.", encoding="utf-8")
    result = run_multi_audit._ingest_file(f)
    assert result is not None
    assert result["document_text"] == "Hello world."
    assert result["metadata"]["document_id"] == "test"


def test_ingest_json_file(tmp_path: Path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    result = run_multi_audit._ingest_file(f)
    assert result is not None
    assert "key" in result["document_text"]


def test_ingest_json_normalized_doc(tmp_path: Path):
    """JSON files that are already normalized docs should use raw_text directly."""
    f = tmp_path / "normed.json"
    f.write_text(
        json.dumps({"raw_text": "Normalized content.", "document_id": "n1"}),
        encoding="utf-8",
    )
    result = run_multi_audit._ingest_file(f)
    assert result is not None
    assert result["document_text"] == "Normalized content."
