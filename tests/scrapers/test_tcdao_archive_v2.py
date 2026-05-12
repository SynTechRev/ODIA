"""Tests for the v2 TCDAO archive scraper enhancements (D1).

Covers the three v2 additions independently of network I/O:

  1. Coverage classification (year/month -> CURRENT / SPARSE_HISTORICAL /
     GAP_INFERRED)
  2. Gap-band absence-record emission as synthetic Documents
  3. Archive-widget month parsing + CoverageManifest construction

Plus a single integration test confirming that an AbsenceRecord
payload (when ingested as a Document tagged primary_entity=E-011)
triggers the D-13 governance-chain cross-reference to BOS (E-020)
per Cross-Entity Analysis Protocol section 4.3 Type E.
"""

from __future__ import annotations

import pytest

bs4 = pytest.importorskip("bs4")  # noqa: F841

from oraculus_di_auditor.analysis.cross_entity import (  # noqa: E402
    _reset_caches_for_tests,
    detect_cross_entity_anomalies,
)
from oraculus_di_auditor.scrapers.tcdao_archive_v2 import (  # noqa: E402
    KNOWN_GAPS,
    SPARSE_HISTORICAL_MONTHS,
    AbsenceRecord,
    CoverageClass,
    CoverageManifest,
    classify_coverage,
    emit_gap_absence_records,
    parse_archive_widget,
)


# ---------------------------------------------------------------------------
# Known gap bands -- data sanity
# ---------------------------------------------------------------------------


def test_known_gaps_three_bands() -> None:
    band_ids = [g.band_id for g in KNOWN_GAPS]
    assert band_ids == ["GAP-A", "GAP-B", "GAP-C"]
    # Months absent should be positive, sum should approximate 132 months
    # (the May 11, 2026 baseline diagnostic).
    total = sum(g.months_absent for g in KNOWN_GAPS)
    assert 130 <= total <= 140


# ---------------------------------------------------------------------------
# classify_coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "year, month, expected",
    [
        (2024, 6, CoverageClass.CURRENT),
        (2018, 1, CoverageClass.CURRENT),
        (2026, 4, CoverageClass.CURRENT),
        (2006, 3, CoverageClass.SPARSE_HISTORICAL),
        (2011, 3, CoverageClass.SPARSE_HISTORICAL),
        (2015, 5, CoverageClass.SPARSE_HISTORICAL),
        (2013, 7, CoverageClass.GAP_INFERRED),
        (2008, 11, CoverageClass.GAP_INFERRED),
        (2016, 4, CoverageClass.GAP_INFERRED),
    ],
)
def test_classify_coverage_month_level(year: int, month: int, expected: str) -> None:
    assert classify_coverage(year, month) == expected


def test_classify_coverage_year_only_sparse() -> None:
    # 2006 has sparse historical entries -> year-level returns SPARSE_HISTORICAL
    assert classify_coverage(2006) == CoverageClass.SPARSE_HISTORICAL


def test_classify_coverage_year_only_gap() -> None:
    # 2013 has no surviving entries -> year-level returns GAP_INFERRED
    assert classify_coverage(2013) == CoverageClass.GAP_INFERRED


def test_classify_coverage_current_year_only() -> None:
    assert classify_coverage(2024) == CoverageClass.CURRENT


# ---------------------------------------------------------------------------
# emit_gap_absence_records + AbsenceRecord payload
# ---------------------------------------------------------------------------


def test_emit_gap_absence_records_returns_three() -> None:
    records = emit_gap_absence_records()
    assert len(records) == 3
    assert {r.band_id for r in records} == {"GAP-A", "GAP-B", "GAP-C"}


def test_absence_record_payload_shape() -> None:
    record = emit_gap_absence_records()[0]
    payload = record.as_document_payload()
    assert payload["primary_entity"] == "E-011"
    assert payload["doc_type"] == "ABSENCE_RECORD"
    assert payload["id"].startswith("TCDAO-ABS-GAP-")
    assert "COVERAGE GAP DETECTED" in payload["full_text"]
    assert record.band_id in payload["full_text"]


def test_absence_record_finding_id_constant() -> None:
    # The finding_id is the stable namespaced identifier used by MAS
    # aggregation; downstream consumers depend on this exact string.
    record = AbsenceRecord(
        band_id="GAP-A",
        start_date="2006-11-01",
        end_date="2011-02-28",
        months_absent=52,
        doc_id="TCDAO-ABS-GAP-A",
    )
    assert record.finding_id == "archival:coverage-gap"


# ---------------------------------------------------------------------------
# parse_archive_widget
# ---------------------------------------------------------------------------


ARCHIVE_WIDGET_HTML = """<html><body>
<aside><select class="widget-archives" name="archive-dropdown">
  <option value="">Select Month</option>
  <option value="https://tulareda.org/2026/04/">April 2026</option>
  <option value="https://tulareda.org/2026/03/">March 2026</option>
  <option value="https://tulareda.org/2018/01/">January 2018</option>
  <option value="https://tulareda.org/2015/05/">May 2015</option>
  <option value="https://tulareda.org/2011/03/">March 2011</option>
  <option value="https://tulareda.org/2006/03/">March 2006</option>
</select></aside>
</body></html>
"""


def test_parse_archive_widget_extracts_year_months() -> None:
    months = parse_archive_widget(ARCHIVE_WIDGET_HTML)
    # All 6 months should round-trip, sorted newest first.
    assert (2026, 4) in months
    assert (2026, 3) in months
    assert (2018, 1) in months
    assert (2015, 5) in months
    assert (2011, 3) in months
    assert (2006, 3) in months
    # Sorted newest first
    assert months == sorted(months, reverse=True)


def test_parse_archive_widget_empty_when_no_widget() -> None:
    assert parse_archive_widget("<html><body>nothing</body></html>") == []


# ---------------------------------------------------------------------------
# CoverageManifest
# ---------------------------------------------------------------------------


def test_coverage_manifest_classifies_discovered_months() -> None:
    months = [(2026, 4), (2018, 1), (2006, 3), (2011, 3)]
    manifest = CoverageManifest.from_discovered_months(months)
    assert "2026-04" in manifest.coverage_band_continuous
    assert "2018-01" in manifest.coverage_band_continuous
    assert "2006-03" in manifest.coverage_band_sparse_historical
    assert "2011-03" in manifest.coverage_band_sparse_historical
    # Manifest captures all three known gap bands even when discovery is partial
    assert len(manifest.inferred_gap_bands) == 3


def test_coverage_manifest_universe_bounds_set() -> None:
    manifest = CoverageManifest()
    # Baseline diagnostic ranges; downstream MAS aggregation reads these.
    assert manifest.estimated_total_historical_universe_min == 400
    assert manifest.estimated_total_historical_universe_max == 560


# ---------------------------------------------------------------------------
# Integration: AbsenceRecord -> D-13 -> Type E governance-chain to BOS
# ---------------------------------------------------------------------------


def test_absence_record_payload_triggers_d13_governance_chain() -> None:
    """Synthetic gap-band document, when run through D-13, should
    surface a Type E governance-chain finding pointing at BOS (E-020).

    This is the contract that ties C1+D1 (scraper emits absence record)
    to B1+B2 (D-13 sweeps the absence record and emits XREF). Without
    this integration the gap-band finding would land in TCDAO MAS but
    never cross-reference to the records-retention authority.
    """
    _reset_caches_for_tests()

    record = emit_gap_absence_records()[0]
    payload = record.as_document_payload()

    # Map the scraper-side payload shape to the normalised-document
    # shape D-13 expects (metadata.primary_entity + raw_text).
    doc = {
        "metadata": {
            "primary_entity": payload["primary_entity"],
            "document_id": payload["id"],
        },
        "raw_text": payload["full_text"],
    }
    findings = detect_cross_entity_anomalies(doc)
    type_e_to_bos = [
        f
        for f in findings
        if f["details"]["target_entity"] == "E-020"
        and f["details"]["finding_type"] == "E"
    ]
    assert type_e_to_bos, (
        f"expected Type E governance-chain XREF to BOS from gap-band "
        f"absence record; got {[f['details'] for f in findings]}"
    )
