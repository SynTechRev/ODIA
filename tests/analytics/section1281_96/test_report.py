"""Unit tests for the CCP § 1281.96 report generator.

Tests verify that build_summary_report() produces a valid .docx file whose
content includes the key sections and data points.  Tests use only stdlib and
the cases built in-process — no network, no DB, no python-docx state mocking.
"""

from datetime import date, datetime
from pathlib import Path

import pytest

from oraculus_di_auditor.analytics.section1281_96.normalize import NormalizedCase

# Guard: skip entire module if python-docx is not installed
docx = pytest.importorskip(
    "docx", reason="python-docx not installed; skipping report tests"
)


from oraculus_di_auditor.analytics.section1281_96.report import build_summary_report

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _case(
    *,
    provider: str = "AAA",
    disposition_type: str = "AWARD_AFTER_HEARING",
    prevailing_party: str | None = "CONSUMER",
    consumer_represented: str = "YES",
    claim_amount_tier: str | None = "1K_10K",
    claim_amount_usd: float | None = 5000.0,
    award_amount_usd: float | None = 4500.0,
    arbitrator_names: list[str] | None = None,
    non_consumer_party_name: str = "Acme Corp",
    non_consumer_party_entity_id: str | None = None,
    fee_total: float | None = 1200.0,
    fee_consumer_pct: float | None = 0.2,
    fee_waiver: bool | None = False,
    quality_flags: list[str] | None = None,
) -> NormalizedCase:
    return NormalizedCase(
        case_id="test",
        provider=provider,
        case_url=None,
        retrieval_ts=datetime(2024, 4, 1),
        retrieval_sha256="x" * 64,
        case_year=2024,
        case_quarter=1,
        filing_date=date(2024, 1, 5),
        disposition_date=date(2024, 2, 20),
        days_to_disposition=46,
        non_consumer_party_name=non_consumer_party_name,
        non_consumer_party_entity_id=non_consumer_party_entity_id,
        non_consumer_initiating=None,
        dispute_type="Consumer Contract",
        dispute_subtype=None,
        consumer_represented=consumer_represented,
        prevailing_party=prevailing_party,
        claim_amount_usd=claim_amount_usd,
        claim_amount_tier=claim_amount_tier,
        award_amount_usd=award_amount_usd,
        claim_to_award_ratio=None,
        disposition_type=disposition_type,
        arbitrator_names=arbitrator_names or ["Test Arbitrator"],
        arbitrator_fee_total_usd=fee_total,
        arbitrator_fee_alloc_consumer_pct=fee_consumer_pct,
        fee_waiver=fee_waiver,
        other_relief=None,
        quality_flags=quality_flags or [],
    )


def _read_docx_text(path: Path) -> str:
    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _collect_table_text(path: Path) -> str:
    doc = docx.Document(str(path))
    parts = []
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Basic output tests
# ---------------------------------------------------------------------------


class TestBuildSummaryReport:
    def test_creates_docx_file(self, tmp_path):
        cases = [_case()]
        out = build_summary_report(cases, path=tmp_path / "test.docx")
        assert out.exists()
        assert out.suffix == ".docx"

    def test_returns_path(self, tmp_path):
        cases = [_case()]
        result = build_summary_report(cases, path=tmp_path / "out.docx")
        assert isinstance(result, Path)

    def test_docx_valid(self, tmp_path):
        cases = [_case()]
        out = build_summary_report(cases, path=tmp_path / "valid.docx")
        doc = docx.Document(str(out))
        assert len(doc.paragraphs) > 0

    def test_heading_present(self, tmp_path):
        cases = [_case()]
        out = build_summary_report(cases, path=tmp_path / "h.docx")
        text = _read_docx_text(out)
        assert "1281.96" in text

    def test_section_headers_present(self, tmp_path):
        cases = [_case()]
        out = build_summary_report(cases, path=tmp_path / "sections.docx")
        text = _read_docx_text(out)
        assert "Dataset Overview" in text
        assert "Prevailing Rate" in text
        assert "Arbitrator" in text
        assert "Corporate" in text

    def test_case_count_in_overview(self, tmp_path):
        cases = [_case() for _ in range(5)]
        out = build_summary_report(cases, path=tmp_path / "count.docx")
        text = _read_docx_text(out)
        assert "5" in text

    def test_provider_name_in_table(self, tmp_path):
        cases = [_case(provider="AAA")]
        out = build_summary_report(cases, path=tmp_path / "prov.docx")
        tbl_text = _collect_table_text(out)
        assert "AAA" in tbl_text

    def test_year_range_in_overview(self, tmp_path):
        cases = [_case()]
        out = build_summary_report(cases, path=tmp_path / "year.docx")
        text = _read_docx_text(out)
        assert "2024" in text


# ---------------------------------------------------------------------------
# Stratified prevailing rate section
# ---------------------------------------------------------------------------


class TestPrevailingRateSection:
    def test_win_rate_in_table(self, tmp_path):
        cases = [
            _case(
                prevailing_party="CONSUMER",
                consumer_represented="YES",
                claim_amount_tier="1K_10K",
            ),
            _case(
                prevailing_party="CONSUMER",
                consumer_represented="YES",
                claim_amount_tier="1K_10K",
            ),
            _case(
                prevailing_party="BUSINESS",
                consumer_represented="YES",
                claim_amount_tier="1K_10K",
            ),
        ]
        out = build_summary_report(cases, path=tmp_path / "rate.docx")
        tbl_text = _collect_table_text(out)
        assert "YES" in tbl_text

    def test_excluded_settled_not_in_denominator(self, tmp_path):
        cases = [
            _case(disposition_type="SETTLED", prevailing_party=None),
            _case(disposition_type="AWARD_AFTER_HEARING", prevailing_party="CONSUMER"),
        ]
        out = build_summary_report(cases, path=tmp_path / "excl.docx")
        tbl_text = _collect_table_text(out)
        assert "1" in tbl_text


# ---------------------------------------------------------------------------
# Arbitrator section
# ---------------------------------------------------------------------------


class TestArbitratorSection:
    def test_arbitrator_name_in_table(self, tmp_path):
        cases = [_case(arbitrator_names=["Jane Doe"]) for _ in range(5)]
        out = build_summary_report(cases, path=tmp_path / "arb.docx")
        tbl_text = _collect_table_text(out)
        assert "Jane Doe" in tbl_text


# ---------------------------------------------------------------------------
# CONTRA cross-reference section
# ---------------------------------------------------------------------------


class TestContraSection:
    def test_contra_section_absent_when_no_entity_ids(self, tmp_path):
        cases = [_case()]
        out = build_summary_report(cases, path=tmp_path / "no_contra.docx")
        text = _read_docx_text(out)
        assert "CONTRA" not in text

    def test_contra_section_present_when_entity_ids_provided(self, tmp_path):
        cases = [_case(non_consumer_party_entity_id="eid-1")]
        out = build_summary_report(
            cases, path=tmp_path / "contra.docx", entity_ids={"eid-1"}
        )
        text = _read_docx_text(out)
        assert "CONTRA" in text

    def test_entity_id_in_contra_table(self, tmp_path):
        cases = [_case(non_consumer_party_entity_id="eid-abc")]
        out = build_summary_report(
            cases, path=tmp_path / "contra_tbl.docx", entity_ids={"eid-abc"}
        )
        tbl_text = _collect_table_text(out)
        assert "eid-abc" in tbl_text

    def test_no_match_shows_no_entities_message(self, tmp_path):
        cases = [_case(non_consumer_party_entity_id=None)]
        out = build_summary_report(
            cases, path=tmp_path / "contra_none.docx", entity_ids={"eid-1"}
        )
        text = _read_docx_text(out)
        assert "No CONTRA corpus entities" in text


# ---------------------------------------------------------------------------
# Quality flag section
# ---------------------------------------------------------------------------


class TestQualityFlagSection:
    def test_quality_flag_section_present(self, tmp_path):
        cases = [_case(quality_flags=["MISSING_CLAIM_AMOUNT"])]
        out = build_summary_report(cases, path=tmp_path / "qf.docx")
        text = _read_docx_text(out)
        assert "Quality" in text

    def test_no_flags_message(self, tmp_path):
        cases = [_case(quality_flags=[])]
        out = build_summary_report(cases, path=tmp_path / "no_qf.docx")
        text = _read_docx_text(out)
        assert "No quality flags" in text

    def test_missing_claim_flag_in_table(self, tmp_path):
        cases = [_case(quality_flags=["MISSING_CLAIM_AMOUNT"])]
        out = build_summary_report(cases, path=tmp_path / "flag_tbl.docx")
        tbl_text = _collect_table_text(out)
        assert "MISSING_CLAIM_AMOUNT" in tbl_text


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_cases_list(self, tmp_path):
        out = build_summary_report([], path=tmp_path / "empty.docx")
        assert out.exists()
        text = _read_docx_text(out)
        assert "0" in text

    def test_multiple_providers(self, tmp_path):
        cases = [
            _case(provider="AAA"),
            _case(provider="JAMS"),
            _case(provider="ADRS"),
        ]
        out = build_summary_report(cases, path=tmp_path / "multi.docx")
        tbl_text = _collect_table_text(out)
        assert "AAA" in tbl_text
        assert "JAMS" in tbl_text
        assert "ADRS" in tbl_text

    def test_custom_generated_by(self, tmp_path):
        cases = [_case()]
        out = build_summary_report(
            cases, path=tmp_path / "custom.docx", generated_by="Test Suite"
        )
        text = _read_docx_text(out)
        assert "Test Suite" in text
