"""Unit tests for oraculus_di_auditor.analytics.section1281_96.normalize."""

from datetime import date, datetime

import pytest

from oraculus_di_auditor.analytics.section1281_96.normalize import (
    NormalizedCase,
    claim_amount_tier,
    make_case_id,
    make_retrieval_sha256,
    normalize_arbitrator_names,
    normalize_bool,
    normalize_consumer_represented,
    normalize_disposition,
    normalize_prevailing,
    parse_amount,
    parse_date,
)

# ---------------------------------------------------------------------------
# claim_amount_tier
# ---------------------------------------------------------------------------


class TestClaimAmountTier:
    def test_under_1k(self):
        assert claim_amount_tier(0.0) == "UNDER_1K"
        assert claim_amount_tier(999.99) == "UNDER_1K"

    def test_1k_10k(self):
        assert claim_amount_tier(1_000.0) == "1K_10K"
        assert claim_amount_tier(9_999.99) == "1K_10K"

    def test_10k_75k(self):
        assert claim_amount_tier(10_000.0) == "10K_75K"
        assert claim_amount_tier(74_999.99) == "10K_75K"

    def test_75k_300k(self):
        assert claim_amount_tier(75_000.0) == "75K_300K"
        assert claim_amount_tier(299_999.99) == "75K_300K"

    def test_over_300k(self):
        assert claim_amount_tier(300_000.0) == "OVER_300K"
        assert claim_amount_tier(1_000_000.0) == "OVER_300K"

    def test_none_returns_none(self):
        assert claim_amount_tier(None) is None


# ---------------------------------------------------------------------------
# parse_amount
# ---------------------------------------------------------------------------


class TestParseAmount:
    def test_dollar_string(self):
        assert parse_amount("$1,234.56") == pytest.approx(1234.56)

    def test_plain_float(self):
        assert parse_amount(500.0) == 500.0

    def test_zero(self):
        assert parse_amount("$0.00") == 0.0

    def test_none_returns_none(self):
        assert parse_amount(None) is None

    def test_na_strings(self):
        for val in ("N/A", "NA", "None", "-", ""):
            assert parse_amount(val) is None

    def test_nan_float(self):

        assert parse_amount(float("nan")) is None

    def test_commas_stripped(self):
        assert parse_amount("1,000,000.00") == pytest.approx(1_000_000.0)

    def test_int_input(self):
        assert parse_amount(250) == 250.0


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------


class TestParseDate:
    def test_mdy_slash(self):
        assert parse_date("01/15/2024") == date(2024, 1, 15)

    def test_ymd_dash(self):
        assert parse_date("2024-03-22") == date(2024, 3, 22)

    def test_full_month_name(self):
        assert parse_date("March 5, 2024") == date(2024, 3, 5)

    def test_abbrev_month(self):
        assert parse_date("Jan 08, 2024") == date(2024, 1, 8)

    def test_two_digit_year(self):
        assert parse_date("01/01/24") == date(2024, 1, 1)

    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_empty_returns_none(self):
        assert parse_date("") is None

    def test_nan_returns_none(self):
        assert parse_date("NaN") is None

    def test_invalid_format_returns_none(self):
        assert parse_date("not-a-date") is None


# ---------------------------------------------------------------------------
# normalize_consumer_represented
# ---------------------------------------------------------------------------


class TestNormalizeConsumerRepresented:
    @pytest.mark.parametrize(
        "val", ["Yes", "yes", "YES", "Y", "TRUE", "1", "Represented"]
    )
    def test_yes_variants(self, val):
        assert normalize_consumer_represented(val) == "YES"

    @pytest.mark.parametrize("val", ["No", "no", "NO", "N", "FALSE", "0", "Pro Se"])
    def test_no_variants(self, val):
        assert normalize_consumer_represented(val) == "NO"

    @pytest.mark.parametrize("val", [None, "", "maybe", "unknown"])
    def test_unknown_fallback(self, val):
        assert normalize_consumer_represented(val) == "UNKNOWN"


# ---------------------------------------------------------------------------
# normalize_disposition
# ---------------------------------------------------------------------------


class TestNormalizeDisposition:
    def test_award_after_hearing(self):
        assert normalize_disposition("Award After Hearing") == "AWARD_AFTER_HEARING"
        assert normalize_disposition("Final Award on Merits") == "AWARD_AFTER_HEARING"

    def test_default_award(self):
        assert normalize_disposition("Default Award") == "DEFAULT_AWARD"

    def test_settled(self):
        assert normalize_disposition("Settled") == "SETTLED"
        assert normalize_disposition("Settlement") == "SETTLED"

    def test_withdrawn(self):
        assert normalize_disposition("Withdrawn") == "WITHDRAWN"

    def test_dismissed(self):
        assert normalize_disposition("Dismissed") == "DISMISSED"

    def test_admin_closed(self):
        assert normalize_disposition("Administrative Closure") == "ADMIN_CLOSED"

    def test_bare_award(self):
        assert normalize_disposition("Award") == "AWARD_AFTER_HEARING"

    def test_other_fallback(self):
        assert normalize_disposition("something else entirely") == "OTHER"

    def test_none_returns_unknown(self):
        assert normalize_disposition(None) == "UNKNOWN"


# ---------------------------------------------------------------------------
# normalize_prevailing
# ---------------------------------------------------------------------------


class TestNormalizePrevailing:
    def test_consumer_wins(self):
        assert normalize_prevailing("Consumer", "AWARD_AFTER_HEARING") == "CONSUMER"
        assert normalize_prevailing("Claimant", "AWARD_AFTER_HEARING") == "CONSUMER"

    def test_business_wins(self):
        assert normalize_prevailing("Business", "AWARD_AFTER_HEARING") == "BUSINESS"
        assert normalize_prevailing("Respondent", "AWARD_AFTER_HEARING") == "BUSINESS"

    def test_neither(self):
        assert normalize_prevailing("Neither", "AWARD_AFTER_HEARING") == "NEITHER"
        assert normalize_prevailing("Split", "AWARD_AFTER_HEARING") == "NEITHER"

    def test_non_award_returns_none(self):
        assert normalize_prevailing("Consumer", "SETTLED") is None
        assert normalize_prevailing("Consumer", "WITHDRAWN") is None

    def test_none_input_returns_none(self):
        assert normalize_prevailing(None, "AWARD_AFTER_HEARING") is None


# ---------------------------------------------------------------------------
# normalize_bool
# ---------------------------------------------------------------------------


class TestNormalizeBool:
    @pytest.mark.parametrize("val", [True, "Yes", "YES", "Y", "TRUE", "1"])
    def test_true_variants(self, val):
        assert normalize_bool(val) is True

    @pytest.mark.parametrize("val", [False, "No", "NO", "N", "FALSE", "0"])
    def test_false_variants(self, val):
        assert normalize_bool(val) is False

    @pytest.mark.parametrize("val", [None, "", "maybe"])
    def test_none_for_ambiguous(self, val):
        assert normalize_bool(val) is None


# ---------------------------------------------------------------------------
# normalize_arbitrator_names
# ---------------------------------------------------------------------------


class TestNormalizeArbitratorNames:
    def test_single_name(self):
        assert normalize_arbitrator_names("Jane Doe") == ["Jane Doe"]

    def test_semicolon_delimited(self):
        result = normalize_arbitrator_names("Jane Doe; John Smith")
        assert result == ["Jane Doe", "John Smith"]

    def test_pipe_delimited(self):
        result = normalize_arbitrator_names("Jane Doe|John Smith")
        assert result == ["Jane Doe", "John Smith"]

    def test_newline_delimited(self):
        result = normalize_arbitrator_names("Jane Doe\nJohn Smith")
        assert result == ["Jane Doe", "John Smith"]

    def test_list_input(self):
        result = normalize_arbitrator_names(["Jane Doe", "John Smith"])
        assert result == ["Jane Doe", "John Smith"]

    def test_none_returns_empty(self):
        assert normalize_arbitrator_names(None) == []

    def test_empty_string_returns_empty(self):
        assert normalize_arbitrator_names("") == []


# ---------------------------------------------------------------------------
# make_case_id / make_retrieval_sha256
# ---------------------------------------------------------------------------


class TestCaseIdStability:
    def test_stable_across_calls(self):
        row = {"Business Name": "Acme Corp", "Filing Date": "01/01/2024"}
        id1 = make_case_id("AAA", row)
        id2 = make_case_id("AAA", row)
        assert id1 == id2

    def test_different_provider_different_id(self):
        row = {"Business Name": "Acme Corp", "Filing Date": "01/01/2024"}
        assert make_case_id("AAA", row) != make_case_id("JAMS", row)

    def test_hex_length(self):
        row = {"x": "y"}
        assert len(make_case_id("AAA", row)) == 64

    def test_retrieval_sha256_length(self):
        row = {"x": "y"}
        assert len(make_retrieval_sha256(row)) == 64


# ---------------------------------------------------------------------------
# NormalizedCase.to_db_dict
# ---------------------------------------------------------------------------


class TestNormalizedCaseToDbDict:
    def _make_case(self, **overrides) -> NormalizedCase:
        defaults = dict(
            case_id="abc123",
            provider="AAA",
            case_url=None,
            retrieval_ts=datetime(2024, 4, 1, 12, 0, 0),
            retrieval_sha256="deadbeef" * 8,
            case_year=2024,
            case_quarter=1,
            filing_date=date(2024, 1, 5),
            disposition_date=date(2024, 2, 20),
            days_to_disposition=46,
            non_consumer_party_name="TeleCo National Inc.",
            non_consumer_party_entity_id=None,
            non_consumer_initiating=None,
            dispute_type="Consumer Contract",
            dispute_subtype=None,
            consumer_represented="YES",
            prevailing_party="CONSUMER",
            claim_amount_usd=4250.0,
            claim_amount_tier="1K_10K",
            award_amount_usd=3900.0,
            claim_to_award_ratio=0.9176,
            disposition_type="AWARD_AFTER_HEARING",
            arbitrator_names=["Margaret R. Chen"],
            arbitrator_fee_total_usd=1450.0,
            arbitrator_fee_alloc_consumer_pct=0.1724,
            fee_waiver=False,
            other_relief=None,
            quality_flags=[],
        )
        defaults.update(overrides)
        return NormalizedCase(**defaults)

    def test_to_db_dict_keys(self):
        d = self._make_case().to_db_dict()
        assert "case_id" in d
        assert "non_consumer_entity_id" in d
        assert "arbitrator_names" in d
        assert "quality_flags" in d

    def test_dates_convert_to_datetime(self):
        d = self._make_case().to_db_dict()
        assert isinstance(d["filing_date"], datetime)
        assert d["filing_date"].year == 2024
        assert d["filing_date"].month == 1
        assert d["filing_date"].day == 5

    def test_none_date_stays_none(self):
        d = self._make_case(filing_date=None).to_db_dict()
        assert d["filing_date"] is None

    def test_arbitrator_names_json(self):
        import json

        d = self._make_case().to_db_dict()
        assert json.loads(d["arbitrator_names"]) == ["Margaret R. Chen"]

    def test_quality_flags_json(self):
        import json

        d = self._make_case(quality_flags=["MISSING_CLAIM_AMOUNT"]).to_db_dict()
        assert json.loads(d["quality_flags"]) == ["MISSING_CLAIM_AMOUNT"]
