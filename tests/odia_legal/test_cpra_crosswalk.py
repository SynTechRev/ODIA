"""Tests for CPRA recodification crosswalk (§ 6250 → § 7920.000 family)."""

from __future__ import annotations

import pytest

from odia_legal.recodification.cpra_crosswalk import (
    _ENTRIES,
    _NEW_TO_OLD,
    _OLD_TO_NEW,
    RECODIFICATION_DATE,
    CPRACrosswalk,
)


@pytest.fixture
def xwalk():
    return CPRACrosswalk()


# ---------------------------------------------------------------------------
# Core section-to-section lookups
# ---------------------------------------------------------------------------


def test_well_known_sections_map_correctly(xwalk):
    assert xwalk.to_new("6250") == "7920.000"
    assert xwalk.to_new("6253") == "7922.500"
    assert xwalk.to_new("6253(c)") == "7922.535"
    assert xwalk.to_new("6254") == "7923.600"
    assert xwalk.to_new("6254(f)") == "7923.650"
    assert xwalk.to_new("6254(k)") == "7923.700"
    assert xwalk.to_new("6255") == "7922.000"
    assert xwalk.to_new("6258") == "7923.100"


def test_reverse_lookup(xwalk):
    assert xwalk.to_old("7920.000") == "6250"
    assert xwalk.to_old("7922.500") == "6253"
    assert xwalk.to_old("7922.535") == "6253(c)"
    assert xwalk.to_old("7923.650") == "6254(f)"
    assert xwalk.to_old("7923.700") == "6254(k)"
    assert xwalk.to_old("7922.000") == "6255"


def test_unknown_section_returns_none(xwalk):
    assert xwalk.to_new("9999") is None
    assert xwalk.to_old("9999.000") is None
    assert xwalk.to_new("") is None


def test_recodification_date():
    from datetime import date

    assert RECODIFICATION_DATE == date(2022, 1, 1)


# ---------------------------------------------------------------------------
# is_legacy / is_current detection
# ---------------------------------------------------------------------------


def test_is_legacy_detects_old_sections(xwalk):
    assert xwalk.is_legacy("Gov. Code § 6254(f)")
    assert xwalk.is_legacy("section 6250")
    assert xwalk.is_legacy("§ 6253(c)")
    assert xwalk.is_legacy("6254(f) exemption applies")


def test_is_legacy_false_for_new_sections(xwalk):
    assert not xwalk.is_legacy("Gov. Code § 7923.650")
    assert not xwalk.is_legacy("no section here at all")


def test_is_current_detects_new_sections(xwalk):
    assert xwalk.is_current("Gov. Code § 7923.650")
    assert xwalk.is_current("§ 7922.535")


def test_is_current_false_for_old_sections(xwalk):
    assert not xwalk.is_current("§ 6254(f)")


# ---------------------------------------------------------------------------
# normalize() — in-place translation of old to new
# ---------------------------------------------------------------------------


def test_normalize_bare_section(xwalk):
    assert "7923.650" in xwalk.normalize("§ 6254(f)")


def test_normalize_section_without_subdivision(xwalk):
    result = xwalk.normalize("§ 6253")
    assert "7922.500" in result


def test_normalize_already_current_is_noop(xwalk):
    s = "Gov. Code § 7923.650"
    assert xwalk.normalize(s) == s


def test_normalize_unknown_section_unchanged(xwalk):
    s = "§ 9999 does not exist"
    assert xwalk.normalize(s) == s


def test_normalize_preserves_surrounding_text(xwalk):
    result = xwalk.normalize("Under § 6254(f) the agency may withhold records.")
    assert "7923.650" in result
    assert "the agency may withhold records" in result


# ---------------------------------------------------------------------------
# translate_citation() — full citation string round-trip
# ---------------------------------------------------------------------------


def test_translate_citation_to_new(xwalk):
    result = xwalk.translate_citation("Cal. Gov. Code § 6254(f)", target="new")
    assert "7923.650" in result


def test_translate_citation_to_old(xwalk):
    result = xwalk.translate_citation("Cal. Gov. Code § 7923.650", target="old")
    assert "6254" in result


# ---------------------------------------------------------------------------
# find_all_in_text()
# ---------------------------------------------------------------------------


def test_find_all_in_text_extracts_multiple(xwalk):
    text = (
        "The agency cited § 6254(f) and § 6254(k) as grounds for withholding, "
        "but failed to apply the § 6255 balancing test."
    )
    results = xwalk.find_all_in_text(text)
    new_sections = {r.new_section for r in results}
    assert "7923.650" in new_sections  # § 6254(f)
    assert "7923.700" in new_sections  # § 6254(k)
    assert "7922.000" in new_sections  # § 6255


def test_find_all_deduplicated(xwalk):
    text = "§ 6254(f) and again § 6254(f)"
    results = xwalk.find_all_in_text(text)
    sections = [r.old_section for r in results]
    assert sections.count("6254(f)") == 1


def test_find_all_returns_empty_for_no_match(xwalk):
    assert xwalk.find_all_in_text("no cpra sections here") == []


# ---------------------------------------------------------------------------
# lookup_old() — full TranslationResult
# ---------------------------------------------------------------------------


def test_lookup_old_returns_full_result(xwalk):
    result = xwalk.lookup_old("6254(f)")
    assert result is not None
    assert result.old_section == "6254(f)"
    assert result.new_section == "7923.650"
    assert result.effective.year == 2022
    assert "law enforcement" in result.title.lower()
    assert result.notes is not None


def test_lookup_old_disclosure_affirmative(xwalk):
    result = xwalk.lookup_old("6254.3")
    assert result is not None
    assert result.new_section == "7927.700"
    assert result.notes is not None


# ---------------------------------------------------------------------------
# statistics()
# ---------------------------------------------------------------------------


def test_statistics_totals(xwalk):
    stats = xwalk.statistics()
    assert stats["total_mappings"] == len(_ENTRIES)
    assert stats["unique_old_sections"] == len(_OLD_TO_NEW)
    assert stats["unique_new_sections"] == len(_NEW_TO_OLD)
    assert stats["total_mappings"] >= 80


def test_statistics_has_article_breakdown(xwalk):
    stats = xwalk.statistics()
    assert any("exemption" in k for k in stats)
    assert any("enforcement" in k for k in stats)


# ---------------------------------------------------------------------------
# Table integrity checks
# ---------------------------------------------------------------------------


def test_all_old_sections_start_with_6(xwalk):
    for entry in _ENTRIES:
        assert entry.old.startswith("6"), f"Bad old section: {entry.old}"


def test_all_new_sections_start_with_7(xwalk):
    for entry in _ENTRIES:
        assert entry.new.startswith("7"), f"Bad new section: {entry.new}"


def test_no_duplicate_new_sections():
    seen: dict[str, str] = {}
    for entry in _ENTRIES:
        if entry.new in seen:
            # Subsection-level duplicates are allowed (e.g. 6255(a) → 7922.000)
            assert entry.old.startswith(
                seen[entry.new].rstrip("(abcdefghijklmnop)")
            ), f"Duplicate new section {entry.new}: {seen[entry.new]} and {entry.old}"
        seen[entry.new] = entry.old


def test_key_surveillance_sections_present(xwalk):
    """Sections critical for ODIA surveillance-CPRA analysis are mapped."""
    for old_sec in ["6254(f)", "6254(k)", "6255", "6253(c)", "6253.9", "6258"]:
        assert xwalk.to_new(old_sec) is not None, f"Missing: {old_sec}"
