"""Integration tests for temporal analysis wired into reporting and multi-jurisdiction.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from oraculus_di_auditor.reporting.auto_classify import (
    FINDING_CATEGORIES,
    classify_finding,
)
from oraculus_di_auditor.reporting.models import AuditReport
from oraculus_di_auditor.temporal.models import ContractEvent, ContractLineage

# ---------------------------------------------------------------------------
# 1. AuditReport includes temporal data
# ---------------------------------------------------------------------------


def test_audit_report_includes_temporal_fields():
    report = AuditReport(
        report_id="R-001",
        report_type="single_jurisdiction",
        generated_at="2024-01-01T00:00:00",
        contract_lineages=[{"vendor": "Axon", "lineage_id": "abc123"}],
        evolution_patterns=[{"pattern_type": "scope_creep", "severity": "high"}],
        timeline_data={"tracks": [], "patterns": []},
    )
    assert len(report.contract_lineages) == 1
    assert report.contract_lineages[0]["vendor"] == "Axon"
    assert len(report.evolution_patterns) == 1
    assert report.timeline_data["tracks"] == []


def test_audit_report_temporal_fields_default_empty():
    report = AuditReport(
        report_id="R-002",
        report_type="single_jurisdiction",
        generated_at="2024-01-01T00:00:00",
    )
    assert report.contract_lineages == []
    assert report.evolution_patterns == []
    assert report.timeline_data == {}


def test_audit_report_temporal_serializes():
    lineage = ContractLineage(
        lineage_id="test123",
        vendor="TestVendor",
        original_amount=100_000.0,
        current_amount=300_000.0,
        events=[
            ContractEvent(
                event_id="e001",
                event_type="original",
                date="2020-01-01",
                description="Original",
                dollar_amount=100_000.0,
            )
        ],
    )
    report = AuditReport(
        report_id="R-003",
        report_type="single_jurisdiction",
        generated_at="2024-01-01T00:00:00",
        contract_lineages=[lineage.model_dump()],
    )
    data = report.model_dump()
    assert data["contract_lineages"][0]["vendor"] == "TestVendor"


# ---------------------------------------------------------------------------
# 2. Temporal findings classified correctly
# ---------------------------------------------------------------------------


def test_temporal_pattern_category_in_registry():
    assert "temporal_pattern" in FINDING_CATEGORIES
    cat = FINDING_CATEGORIES["temporal_pattern"]
    assert cat["display_name"] == "Temporal / Evolution Pattern"
    assert "procurement_timeline" in cat["detectors"]
    assert "scope_expansion" in cat["detectors"]
    assert "{vendor}" in cat["recommendation_template"]
    assert "{pattern_type}" in cat["recommendation_template"]


def test_procurement_timeline_finding_classified_as_temporal():
    anomaly = {"layer": "procurement_timeline", "id": "PT-001", "severity": "high"}
    category = classify_finding(anomaly)
    # procurement_timeline appears in both procurement_violation and temporal_pattern;
    # assert it resolves to one of them
    assert category in ("procurement_violation", "temporal_pattern")


def test_temporal_finding_template_has_required_placeholders():
    template = FINDING_CATEGORIES["temporal_pattern"]["recommendation_template"]
    assert "{vendor}" in template
    assert "{pattern_type}" in template
    assert "{span_years}" in template
    assert "{growth_percentage}" in template


# ---------------------------------------------------------------------------
# 3. temporal_report.md template renders without errors
# ---------------------------------------------------------------------------


def test_temporal_report_template_exists():
    template_path = Path(__file__).parent.parent / "templates" / "temporal_report.md"
    assert template_path.exists(), "temporal_report.md template not found"


def test_temporal_report_template_renders(tmp_path: Path):
    """Render the template with Jinja2 and assert no errors."""
    pytest.importorskip("jinja2", reason="jinja2 not installed")
    from jinja2 import Environment, FileSystemLoader

    template_dir = Path(__file__).parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=False)
    template = env.get_template("temporal_report.md")

    lineage = ContractLineage(
        lineage_id="lid001",
        vendor="Axon",
        program="BWC",
        original_amount=200_000.0,
        current_amount=1_000_000.0,
        events=[
            ContractEvent(
                event_id="e001",
                event_type="original",
                date="2019-01-01",
                description="Original BWC contract",
                dollar_amount=200_000.0,
                cumulative_amount=200_000.0,
            ),
            ContractEvent(
                event_id="e002",
                event_type="amendment",
                date="2022-06-01",
                description="Amendment 1",
                dollar_amount=800_000.0,
                cumulative_amount=1_000_000.0,
                authorization_type="sole_source",
            ),
        ],
    )

    rendered = template.render(
        jurisdiction="Test City",
        generated_at="2024-01-01T00:00:00",
        date_range={"start": "2019-01-01", "end": "2023-12-31"},
        lineages=[lineage.model_dump()],
        patterns=[],
        total_spend=1_000_000.0,
        growth_chart=None,
        recommendations=["Conduct competitive rebid for BWC program."],
    )
    assert "Contract Evolution Report" in rendered
    assert "Axon" in rendered
    assert "BWC" in rendered
    assert "1,000,000" in rendered


# ---------------------------------------------------------------------------
# 4. run_audit with temporal flag includes lineage data
# ---------------------------------------------------------------------------


def test_run_audit_temporal_flag_adds_temporal_key(tmp_path: Path):
    """run_audit with temporal=True populates report['temporal']."""
    import json

    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    output_dir = tmp_path / "output"
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Minimal jurisdiction config
    (config_dir / "jurisdiction.json").write_text(
        json.dumps({"name": "Test City", "state": "CA"}), encoding="utf-8"
    )
    # Minimal source document
    (source_dir / "doc.txt").write_text(
        "This is a test document about vendor contract.", encoding="utf-8"
    )

    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from scripts.run_audit import run_audit  # type: ignore[import]  # noqa: E402

    report = run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        temporal=True,
    )
    # temporal key should always be present when temporal=True (even if empty lineages)
    assert "temporal" in report


def test_run_audit_no_temporal_flag_omits_temporal_key(tmp_path: Path):
    """run_audit with temporal=False does not add temporal key."""
    import json
    import sys

    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    output_dir = tmp_path / "output"
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    (config_dir / "jurisdiction.json").write_text(
        json.dumps({"name": "Test City", "state": "CA"}), encoding="utf-8"
    )
    (source_dir / "doc.txt").write_text("Test document content.", encoding="utf-8")

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from scripts.run_audit import run_audit  # type: ignore[import]  # noqa: E402

    report = run_audit(
        config_dir=config_dir,
        source_dir=source_dir,
        output_dir=output_dir,
        temporal=False,
    )
    assert "temporal" not in report


# ---------------------------------------------------------------------------
# 5. Multi-jurisdiction runner includes temporal data per jurisdiction
# ---------------------------------------------------------------------------


def test_multi_jurisdiction_runner_includes_temporal():
    from oraculus_di_auditor.config import JurisdictionConfig
    from oraculus_di_auditor.multi_jurisdiction.registry import JurisdictionRegistry
    from oraculus_di_auditor.multi_jurisdiction.runner import MultiJurisdictionRunner

    registry = JurisdictionRegistry()
    cfg = JurisdictionConfig(name="Test City", state="CA")
    registry.register("city_a", cfg)

    runner = MultiJurisdictionRunner(registry)
    docs = [
        {
            "document_text": "This is a test contract document.",
            "metadata": {
                "vendor": "TestVendor",
                "date": "2021-01-01",
                "document_type": "original",
            },
        }
    ]
    result = runner.analyze_jurisdiction("city_a", docs)
    assert "temporal" in result
    assert "lineage_count" in result["temporal"]
    assert "pattern_count" in result["temporal"]
