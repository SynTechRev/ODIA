"""Unit tests for oraculus_di_auditor.analytics.section1281_96.compute."""

from datetime import datetime

import pytest

from oraculus_di_auditor.analytics.section1281_96.compute import (
    arbitrator_repeat_player_concentration,
    contra_corpus_entity_slice,
    corporate_repeat_player_concentration,
    prevailing_rate_stratified,
    wilson_ci,
)
from oraculus_di_auditor.analytics.section1281_96.normalize import NormalizedCase

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _case(
    *,
    disposition_type: str = "AWARD_AFTER_HEARING",
    prevailing_party: str | None = "CONSUMER",
    consumer_represented: str = "YES",
    claim_amount_tier: str | None = "1K_10K",
    arbitrator_names: list[str] | None = None,
    non_consumer_party_name: str = "Acme Corp",
    non_consumer_party_entity_id: str | None = None,
    provider: str = "AAA",
    case_year: int = 2024,
    case_quarter: int = 1,
) -> NormalizedCase:
    return NormalizedCase(
        case_id="test",
        provider=provider,
        case_url=None,
        retrieval_ts=datetime(2024, 4, 1),
        retrieval_sha256="x" * 64,
        case_year=case_year,
        case_quarter=case_quarter,
        filing_date=None,
        disposition_date=None,
        days_to_disposition=None,
        non_consumer_party_name=non_consumer_party_name,
        non_consumer_party_entity_id=non_consumer_party_entity_id,
        non_consumer_initiating=None,
        dispute_type=None,
        dispute_subtype=None,
        consumer_represented=consumer_represented,
        prevailing_party=prevailing_party,
        claim_amount_usd=None,
        claim_amount_tier=claim_amount_tier,
        award_amount_usd=None,
        claim_to_award_ratio=None,
        disposition_type=disposition_type,
        arbitrator_names=arbitrator_names or [],
        quality_flags=[],
    )


# ---------------------------------------------------------------------------
# wilson_ci
# ---------------------------------------------------------------------------


class TestWilsonCI:
    def test_zero_denominator(self):
        lo, hi = wilson_ci(0, 0)
        assert lo == 0.0
        assert hi == 0.0

    def test_all_wins(self):
        lo, hi = wilson_ci(100, 100)
        assert lo > 0.9
        assert hi == 1.0

    def test_no_wins(self):
        lo, hi = wilson_ci(0, 100)
        assert lo == 0.0
        assert hi < 0.05

    def test_half_wins(self):
        lo, hi = wilson_ci(50, 100)
        assert lo < 0.5 < hi

    def test_bounds_clamped(self):
        lo, hi = wilson_ci(1, 1)
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0

    def test_ci_width_shrinks_with_n(self):
        lo10, hi10 = wilson_ci(5, 10)
        lo100, hi100 = wilson_ci(50, 100)
        assert (hi10 - lo10) > (hi100 - lo100)


# ---------------------------------------------------------------------------
# prevailing_rate_stratified
# ---------------------------------------------------------------------------


class TestPrevailingRateStratified:
    def test_empty_list(self):
        result = prevailing_rate_stratified([])
        assert result == {}

    def test_excludes_non_award_cases(self):
        cases = [
            _case(disposition_type="SETTLED", prevailing_party=None),
            _case(disposition_type="WITHDRAWN", prevailing_party=None),
            _case(disposition_type="AWARD_AFTER_HEARING", prevailing_party="CONSUMER"),
        ]
        result = prevailing_rate_stratified(cases)
        total = sum(
            v["n_cases"] for rep_data in result.values() for v in rep_data.values()
        )
        assert total == 1

    def test_rate_calculation(self):
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
        result = prevailing_rate_stratified(cases)
        cell = result["YES"]["1K_10K"]
        assert cell["n_cases"] == 3
        assert cell["n_consumer_wins"] == 2
        assert cell["rate"] == pytest.approx(2 / 3, abs=1e-4)

    def test_ci_present(self):
        cases = [_case(prevailing_party="CONSUMER", consumer_represented="YES")]
        result = prevailing_rate_stratified(cases)
        cell = result["YES"]["1K_10K"]
        assert "ci_lower" in cell
        assert "ci_upper" in cell
        assert cell["ci_lower"] <= cell["rate"] <= cell["ci_upper"]

    def test_none_tier_bucketed_as_unknown(self):
        cases = [
            _case(
                claim_amount_tier=None,
                prevailing_party="CONSUMER",
                consumer_represented="YES",
            )
        ]
        result = prevailing_rate_stratified(cases)
        assert "UNKNOWN" in result["YES"]


# ---------------------------------------------------------------------------
# arbitrator_repeat_player_concentration
# ---------------------------------------------------------------------------


class TestArbitratorRepeatPlayerConcentration:
    def test_empty(self):
        result = arbitrator_repeat_player_concentration([])
        assert result["total_case_assignments"] == 0
        assert result["unique_arbitrators"] == 0
        assert result["top_10_by_volume"] == []

    def test_single_arbitrator(self):
        cases = [_case(arbitrator_names=["Jane Doe"]) for _ in range(5)]
        result = arbitrator_repeat_player_concentration(cases)
        assert result["total_case_assignments"] == 5
        assert result["unique_arbitrators"] == 1
        assert result["top_5pct_arbitrators"] == 1
        assert result["top_5pct_case_share"] == pytest.approx(1.0)

    def test_multiple_arbitrators(self):
        cases = (
            [_case(arbitrator_names=["Alice"]) for _ in range(60)]
            + [_case(arbitrator_names=["Bob"]) for _ in range(30)]
            + [_case(arbitrator_names=["Carol"]) for _ in range(10)]
        )
        result = arbitrator_repeat_player_concentration(cases)
        assert result["total_case_assignments"] == 100
        assert result["unique_arbitrators"] == 3
        top1 = result["top_10_by_volume"][0]
        assert top1["name"] == "Alice"
        assert top1["case_count"] == 60
        assert top1["share"] == pytest.approx(0.6)

    def test_top_10_max_length(self):
        cases = [_case(arbitrator_names=[f"Arb{i}"]) for i in range(20)]
        result = arbitrator_repeat_player_concentration(cases)
        assert len(result["top_10_by_volume"]) == 10

    def test_multi_arbitrator_case_counted_per_name(self):
        cases = [_case(arbitrator_names=["Alice", "Bob"])]
        result = arbitrator_repeat_player_concentration(cases)
        assert result["total_case_assignments"] == 2
        assert result["unique_arbitrators"] == 2


# ---------------------------------------------------------------------------
# corporate_repeat_player_concentration
# ---------------------------------------------------------------------------


class TestCorporateRepeatPlayerConcentration:
    def test_empty(self):
        result = corporate_repeat_player_concentration([])
        assert result["total_cases"] == 0
        assert result["herfindahl_index"] == 0.0

    def test_single_company_hhi(self):
        cases = [_case(non_consumer_party_name="Acme") for _ in range(10)]
        result = corporate_repeat_player_concentration(cases)
        assert result["herfindahl_index"] == pytest.approx(10_000.0)
        assert result["unique_companies"] == 1

    def test_equal_share_hhi(self):
        cases = [_case(non_consumer_party_name="A") for _ in range(50)] + [
            _case(non_consumer_party_name="B") for _ in range(50)
        ]
        result = corporate_repeat_player_concentration(cases)
        assert result["herfindahl_index"] == pytest.approx(5_000.0)

    def test_entity_id_grouping(self):
        cases = [
            _case(
                non_consumer_party_name="Acme Corp",
                non_consumer_party_entity_id="eid-1",
            ),
            _case(
                non_consumer_party_name="Acme Corporation",
                non_consumer_party_entity_id="eid-1",
            ),
        ]
        result = corporate_repeat_player_concentration(cases)
        assert result["unique_companies"] == 1
        assert result["top_10_by_volume"][0]["case_count"] == 2

    def test_consumer_win_rate_in_top10(self):
        cases = [
            _case(
                non_consumer_party_name="Lender",
                disposition_type="AWARD_AFTER_HEARING",
                prevailing_party="CONSUMER",
            ),
            _case(
                non_consumer_party_name="Lender",
                disposition_type="AWARD_AFTER_HEARING",
                prevailing_party="BUSINESS",
            ),
        ]
        result = corporate_repeat_player_concentration(cases)
        top = result["top_10_by_volume"][0]
        assert top["award_cases"] == 2
        assert top["consumer_win_rate"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# contra_corpus_entity_slice
# ---------------------------------------------------------------------------


class TestContraCorpusEntitySlice:
    def test_empty_entity_ids(self):
        cases = [_case(non_consumer_party_entity_id="eid-1")]
        result = contra_corpus_entity_slice(cases, set())
        assert result == {}

    def test_filters_by_entity_id(self):
        cases = [
            _case(non_consumer_party_entity_id="eid-1"),
            _case(non_consumer_party_entity_id="eid-2"),
            _case(non_consumer_party_entity_id=None),
        ]
        result = contra_corpus_entity_slice(cases, {"eid-1"})
        assert "eid-1" in result
        assert "eid-2" not in result
        assert len(result["eid-1"]) == 1

    def test_none_entity_id_excluded(self):
        cases = [_case(non_consumer_party_entity_id=None)]
        result = contra_corpus_entity_slice(cases, {"eid-1"})
        assert result == {}

    def test_multiple_cases_per_entity(self):
        cases = [_case(non_consumer_party_entity_id="eid-1") for _ in range(3)]
        result = contra_corpus_entity_slice(cases, {"eid-1"})
        assert len(result["eid-1"]) == 3
