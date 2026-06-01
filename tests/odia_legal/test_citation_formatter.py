"""Tests for the 4-style citation formatter."""

from __future__ import annotations

import pytest

from odia_legal.citations.formatter import format_citation, format_all, Style
from odia_legal.citations.parser import (
    Citation,
    parse_citations,
    parse_cal_code,
    parse_cal_case,
    parse_usc,
    parse_cfr,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def usc(title: int, section: str, subdivision: str | None = None) -> Citation:
    return Citation(
        citation_type="usc",
        corpus_id="us_code",
        raw="",
        canonical=f"{title} U.S.C. § {section}",
        usc_title=title,
        section=section,
        subdivision=subdivision,
    )


def cfr_sec(title: int, section: str) -> Citation:
    return Citation(
        citation_type="cfr",
        corpus_id="cfr",
        raw="",
        canonical=f"{title} C.F.R. § {section}",
        cfr_title=title,
        section=section,
    )


def cfr_part(title: int, part: str) -> Citation:
    return Citation(
        citation_type="cfr",
        corpus_id="cfr",
        raw="",
        canonical=f"{title} C.F.R. Part {part}",
        cfr_title=title,
        cfr_part=part,
    )


def cal_case(parties: str, year: int, volume: int, reporter: str, page: int) -> Citation:
    return Citation(
        citation_type="cal_case",
        corpus_id="cal_case_law",
        raw="",
        canonical=f"{parties} ({year}) {volume} {reporter} {page}",
        parties=parties,
        year=year,
        volume=volume,
        reporter=reporter,
        page=page,
    )


# ===========================================================================
# USC formatting
# ===========================================================================


def test_usc_cal_style():
    c = usc(42, "1983")
    assert format_citation(c, "cal_style") == "42 U.S.C. § 1983"


def test_usc_bluebook():
    c = usc(42, "1983")
    assert format_citation(c, "bluebook") == "42 U.S.C. § 1983"


def test_usc_plain():
    c = usc(34, "10152", "(a)(1)(G)")
    result = format_citation(c, "plain")
    assert "34" in result
    assert "United States Code" in result
    assert "10152" in result


def test_usc_markdown():
    c = usc(42, "1983")
    assert format_citation(c, "markdown") == "42 U.S.C. § 1983"


def test_usc_with_subdivision():
    c = usc(34, "10152", "(a)(1)(G)")
    assert "(a)(1)(G)" in format_citation(c, "cal_style")
    assert "(a)(1)(G)" in format_citation(c, "bluebook")


# ===========================================================================
# CFR formatting
# ===========================================================================


def test_cfr_section_cal_style():
    c = cfr_sec(2, "200.303")
    assert format_citation(c, "cal_style") == "2 C.F.R. § 200.303"


def test_cfr_section_bluebook():
    c = cfr_sec(28, "23.20")
    assert format_citation(c, "bluebook") == "28 C.F.R. § 23.20"


def test_cfr_section_plain():
    c = cfr_sec(2, "200.303")
    result = format_citation(c, "plain")
    assert "Code of Federal Regulations" in result
    assert "200.303" in result


def test_cfr_part_all_styles():
    c = cfr_part(2, "200")
    for style in ("cal_style", "bluebook", "plain", "markdown"):
        result = format_citation(c, style)  # type: ignore[arg-type]
        assert "200" in result


def test_cfr_part_plain():
    c = cfr_part(28, "23")
    result = format_citation(c, "plain")
    assert "Part 23" in result
    assert "Code of Federal Regulations" in result


# ===========================================================================
# California code formatting
# ===========================================================================


def test_cal_gov_code_cal_style():
    cites = parse_cal_code("Gov. Code § 7922.000")
    assert cites
    result = format_citation(cites[0], "cal_style")
    assert result == "Gov. Code, § 7922.000"


def test_cal_gov_code_bluebook():
    cites = parse_cal_code("Gov. Code § 7922.000")
    result = format_citation(cites[0], "bluebook")
    assert "Cal. Gov't Code" in result
    assert "7922.000" in result


def test_cal_gov_code_plain():
    cites = parse_cal_code("Gov. Code § 7922.000")
    result = format_citation(cites[0], "plain")
    assert "California Government Code" in result
    assert "7922.000" in result


def test_cal_gov_code_markdown():
    cites = parse_cal_code("Gov. Code § 7922.000")
    result = format_citation(cites[0], "markdown")
    assert "§ 7922.000" in result
    assert "*" not in result  # no italics on statutes


def test_cal_pen_code():
    cites = parse_cal_code("Pen. Code § 832.7")
    result = format_citation(cites[0], "cal_style")
    assert "Pen. Code" in result
    assert "832.7" in result


def test_cal_ccp():
    cites = parse_cal_code("Code Civ. Proc. § 1085")
    assert cites
    result_bb = format_citation(cites[0], "bluebook")
    assert "Cal. Civ. Proc. Code" in result_bb


def test_cal_civ_code_with_subdivision_cal_style():
    cites = parse_cal_code("Civ. Code § 1798.90.55(a)")
    if cites:
        result = format_citation(cites[0], "cal_style")
        assert "1798.90.55" in result


def test_cal_pen_code_bluebook():
    cites = parse_cal_code("Pen. Code § 832.7(a)(2)")
    if cites:
        result = format_citation(cites[0], "bluebook")
        assert "Cal. Penal Code" in result


# ===========================================================================
# California case formatting
# ===========================================================================


def test_cal_case_cal_style():
    c = cal_case("CBS, Inc. v. Block", 1986, 42, "Cal.3d", 646)
    result = format_citation(c, "cal_style")
    assert result == "CBS, Inc. v. Block (1986) 42 Cal.3d 646"


def test_cal_case_bluebook():
    c = cal_case("CBS, Inc. v. Block", 1986, 42, "Cal.3d", 646)
    result = format_citation(c, "bluebook")
    # Bluebook: Party, volume Reporter page (year)
    assert "CBS, Inc. v. Block" in result
    assert "Cal. 3d" in result
    assert "1986" in result
    assert result.endswith("(1986)")


def test_cal_case_bluebook_app():
    c = cal_case("ACLU v. Superior Court", 2011, 202, "Cal.App.4th", 55)
    result = format_citation(c, "bluebook")
    assert "Cal. App. 4th" in result
    assert "(2011)" in result


def test_cal_case_plain():
    c = cal_case("Times Mirror Co. v. Superior Court", 1991, 53, "Cal.3d", 1325)
    result = format_citation(c, "plain")
    assert "California Supreme Court" in result
    assert "1991" in result
    assert "Times Mirror" in result


def test_cal_case_plain_app():
    c = cal_case("ACLU v. Superior Court", 2011, 202, "Cal.App.4th", 55)
    result = format_citation(c, "plain")
    assert "California Court of Appeal" in result


def test_cal_case_markdown():
    c = cal_case("CBS, Inc. v. Block", 1986, 42, "Cal.3d", 646)
    result = format_citation(c, "markdown")
    assert result.startswith("*CBS, Inc. v. Block*")
    assert "(1986)" in result


# ===========================================================================
# format_all
# ===========================================================================


def test_format_all_default_separator():
    cites = parse_citations("Gov. Code § 7922.000 and CBS, Inc. v. Block (1986) 42 Cal.3d 646")
    if len(cites) >= 2:
        result = format_all(cites, style="cal_style")
        assert "; " in result


def test_format_all_custom_separator():
    c1 = usc(42, "1983")
    c2 = cfr_sec(2, "200.303")
    result = format_all([c1, c2], style="bluebook", separator=" | ")
    assert " | " in result


def test_format_all_empty():
    assert format_all([], style="cal_style") == ""


# ===========================================================================
# Error handling
# ===========================================================================


def test_unknown_citation_type_raises():
    c = Citation(citation_type="unknown", corpus_id="x", raw="x", canonical="x")
    with pytest.raises(ValueError, match="Unknown citation_type"):
        format_citation(c, "cal_style")


# ===========================================================================
# Round-trip: parse then format
# ===========================================================================


def test_roundtrip_usc():
    text = "42 U.S.C. § 1983"
    cites = parse_usc(text)
    assert cites
    assert format_citation(cites[0], "cal_style") == "42 U.S.C. § 1983"


def test_roundtrip_cfr():
    text = "2 C.F.R. § 200.303"
    cites = parse_cfr(text)
    assert cites
    assert "200.303" in format_citation(cites[0], "cal_style")


def test_roundtrip_cal_case_cal_style():
    text = "CBS, Inc. v. Block (1986) 42 Cal.3d 646"
    cites = parse_cal_case(text)
    assert cites
    result = format_citation(cites[0], "cal_style")
    assert "CBS, Inc. v. Block (1986) 42 Cal.3d 646" == result


def test_roundtrip_cal_case_bluebook():
    text = "CBS, Inc. v. Block (1986) 42 Cal.3d 646"
    cites = parse_cal_case(text)
    result = format_citation(cites[0], "bluebook")
    assert "CBS, Inc. v. Block" in result
    assert "Cal. 3d" in result
    assert "646" in result
    assert "(1986)" in result
