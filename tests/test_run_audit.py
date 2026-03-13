"""Integration tests for scripts/run_audit.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: load run_audit as a module without installing it as a package
# ---------------------------------------------------------------------------

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "run_audit.py"


def _load_run_audit():
    spec = importlib.util.spec_from_file_location("run_audit", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_run_audit_mod = _load_run_audit()
run_audit = _run_audit_mod.run_audit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    d = tmp_path_factory.mktemp("config")
    jurisdiction = {
        "name": "City of Testville",
        "state": "TX",
        "country": "US",
        "legistar_base_url": "https://testville.legistar.com",
        "meeting_type": "City Council Regular Meeting",
    }
    agencies = {
        "Police Department": ["police", "pd"],
        "City Council": ["city council", "council"],
    }
    (d / "jurisdiction.json").write_text(json.dumps(jurisdiction), encoding="utf-8")
    (d / "agencies.json").write_text(json.dumps(agencies), encoding="utf-8")
    return d


@pytest.fixture()
def source_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A source directory with a mix of clean and anomalous documents."""
    d = tmp_path_factory.mktemp("source")

    # Clean document — fiscal with appropriation language
    (d / "clean_budget.txt").write_text(
        "There is appropriated $500,000 for city operations in fiscal year 2024.",
        encoding="utf-8",
    )

    # Document with a fiscal anomaly (amount without appropriation keyword)
    (d / "fiscal_anomaly.txt").write_text(
        "The program receives $1,000,000 for surveillance equipment. "
        "No hash or provenance tracking was established.",
        encoding="utf-8",
    )

    # Document with retroactive language (administrative anomaly)
    (d / "retroactive_contract.txt").write_text(
        "This contract is retroactive to January 1, 2024. "
        "Final action: Approved. Status: Closed. Vote result: 7-2. "
        "Meeting date: 2024-03-15. Agenda number: 24-0312.",
        encoding="utf-8",
    )

    # JSON document — already normalized-ish
    doc_json = {
        "document_id": "json-doc-001",
        "raw_text": (
            "Amendment No. 1. Original contract $100,000. New total $250,000. "
            "Not to exceed $250,000. Sole source justification provided."
        ),
        "title": "Contract Amendment",
    }
    (d / "contract_amendment.json").write_text(json.dumps(doc_json), encoding="utf-8")

    return d


@pytest.fixture()
def output_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("output")


# ---------------------------------------------------------------------------
# Core pipeline tests
# ---------------------------------------------------------------------------


def test_run_audit_returns_report_dict(config_dir, source_dir, output_dir):
    report = run_audit(config_dir, source_dir, output_dir)
    assert isinstance(report, dict)


def test_run_audit_report_has_required_keys(config_dir, source_dir, output_dir):
    report = run_audit(config_dir, source_dir, output_dir)
    for key in (
        "audit_timestamp",
        "jurisdiction",
        "date_range",
        "document_count",
        "total_findings",
        "severity_summary",
        "findings_by_layer",
        "top_findings",
        "documents",
    ):
        assert key in report, f"Missing key: {key}"


def test_run_audit_document_count_matches_ingested(config_dir, source_dir, output_dir):
    report = run_audit(config_dir, source_dir, output_dir)
    # 4 files created in fixture: 3 .txt + 1 .json
    assert report["document_count"] == 4


def test_run_audit_jurisdiction_name_in_report(config_dir, source_dir, output_dir):
    report = run_audit(config_dir, source_dir, output_dir)
    assert report["jurisdiction"]["name"] == "City of Testville"
    assert report["jurisdiction"]["state"] == "TX"


def test_run_audit_finds_anomalies(config_dir, source_dir, output_dir):
    report = run_audit(config_dir, source_dir, output_dir)
    # The anomaly-bearing documents should produce at least some findings
    assert report["total_findings"] > 0


def test_run_audit_severity_summary_structure(config_dir, source_dir, output_dir):
    report = run_audit(config_dir, source_dir, output_dir)
    sev = report["severity_summary"]
    for k in ("critical", "high", "medium", "low"):
        assert k in sev
        assert isinstance(sev[k], int)


def test_run_audit_top_findings_list(config_dir, source_dir, output_dir):
    report = run_audit(config_dir, source_dir, output_dir)
    assert isinstance(report["top_findings"], list)
    assert len(report["top_findings"]) <= 10


def test_run_audit_top_findings_have_required_fields(
    config_dir, source_dir, output_dir
):
    report = run_audit(config_dir, source_dir, output_dir)
    for finding in report["top_findings"]:
        assert "id" in finding
        assert "severity" in finding
        assert "layer" in finding
        assert "issue" in finding


def test_run_audit_documents_list_contains_per_doc_results(
    config_dir, source_dir, output_dir
):
    report = run_audit(config_dir, source_dir, output_dir)
    for doc_result in report["documents"]:
        assert "document_id" in doc_result
        assert "findings" in doc_result
        assert "finding_count" in doc_result
        assert doc_result["finding_count"] == len(doc_result["findings"])


# ---------------------------------------------------------------------------
# Output file tests
# ---------------------------------------------------------------------------


def test_json_report_written(config_dir, source_dir, output_dir):
    run_audit(config_dir, source_dir, output_dir)
    json_path = output_dir / "audit_report.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["document_count"] == 4


def test_markdown_report_written(config_dir, source_dir, output_dir):
    run_audit(config_dir, source_dir, output_dir)
    md_path = output_dir / "audit_report.md"
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "City of Testville" in content
    assert "Severity Summary" in content
    assert "Top 10 Findings" in content


def test_markdown_report_contains_document_table(config_dir, source_dir, output_dir):
    run_audit(config_dir, source_dir, output_dir)
    md = (output_dir / "audit_report.md").read_text(encoding="utf-8")
    assert "Documents Analyzed" in md


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_missing_source_dir_raises_file_not_found(config_dir, output_dir):
    with pytest.raises(FileNotFoundError, match="Source directory not found"):
        run_audit(config_dir, "/nonexistent/path/sources", output_dir)


def test_empty_source_dir_raises_value_error(
    config_dir, tmp_path_factory: pytest.TempPathFactory, output_dir
):
    empty = tmp_path_factory.mktemp("empty_source")
    with pytest.raises(ValueError, match="No ingestable documents"):
        run_audit(config_dir, empty, output_dir)


def test_missing_config_dir_raises_file_not_found(source_dir, output_dir):
    with pytest.raises(FileNotFoundError):
        run_audit("/nonexistent/config", source_dir, output_dir)


def test_output_dir_created_if_not_exists(
    config_dir, source_dir, tmp_path_factory: pytest.TempPathFactory
):
    new_output = tmp_path_factory.mktemp("base") / "nested" / "output"
    assert not new_output.exists()
    run_audit(config_dir, source_dir, new_output)
    assert new_output.exists()
    assert (new_output / "audit_report.json").exists()


# ---------------------------------------------------------------------------
# Single-file source
# ---------------------------------------------------------------------------


def test_single_txt_file_source(
    config_dir, tmp_path_factory: pytest.TempPathFactory, output_dir
):
    d = tmp_path_factory.mktemp("single_source")
    (d / "doc.txt").write_text(
        "There is appropriated $200,000 for the parks department.",
        encoding="utf-8",
    )
    report = run_audit(config_dir, d, output_dir)
    assert report["document_count"] == 1


def test_single_json_normalized_doc(
    config_dir, tmp_path_factory: pytest.TempPathFactory, output_dir
):
    d = tmp_path_factory.mktemp("json_source")
    doc = {
        "document_id": "test-001",
        "raw_text": "Resolution was approved by the city council on March 15.",
        "title": "Test Resolution",
        "status": "Closed",
        "final_action": "Approved",
        "vote_result": "9-0",
        "meeting_date": "2024-03-15",
        "agenda_number": "24-0312",
    }
    (d / "resolution.json").write_text(json.dumps(doc), encoding="utf-8")
    report = run_audit(config_dir, d, output_dir)
    assert report["document_count"] == 1
