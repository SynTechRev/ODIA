"""Tests for the multi-code citation parser."""

from __future__ import annotations

from odia_legal.citations.parser import (
    parse_cal_case,
    parse_cal_code,
    parse_cfr,
    parse_citations,
    parse_usc,
)

# ---------------------------------------------------------------------------
# USC
# ---------------------------------------------------------------------------


def test_usc_basic():
    results = parse_usc("34 U.S.C. § 10152")
    assert len(results) == 1
    c = results[0]
    assert c.citation_type == "usc"
    assert c.usc_title == 34
    assert c.section == "10152"
    assert c.canonical == "34 U.S.C. § 10152"


def test_usc_with_subsection():
    results = parse_usc("42 U.S.C. § 1983(a)(1)")
    assert results[0].section == "1983"
    assert results[0].subdivision == "(a)(1)"


def test_usc_informal():
    results = parse_usc("42 USC 1983")
    assert results[0].usc_title == 42
    assert results[0].section == "1983"


def test_usc_multiple_in_text():
    text = "See 34 U.S.C. § 10152 and 42 U.S.C. § 1983."
    results = parse_usc(text)
    titles = {c.usc_title for c in results}
    assert 34 in titles
    assert 42 in titles


def test_usc_rejects_cfr():
    results = parse_usc("2 C.F.R. § 200.303")
    assert results == []


def test_usc_title_range_guard():
    # Title 99 doesn't exist — should be filtered out
    results = parse_usc("99 U.S.C. § 100")
    assert results == []


# ---------------------------------------------------------------------------
# CFR
# ---------------------------------------------------------------------------


def test_cfr_section():
    results = parse_cfr("2 C.F.R. § 200.303")
    assert len(results) == 1
    c = results[0]
    assert c.citation_type == "cfr"
    assert c.cfr_title == 2
    assert c.section == "200.303"
    assert "2 C.F.R. § 200.303" in c.canonical


def test_cfr_part():
    results = parse_cfr("28 C.F.R. Part 23")
    assert len(results) == 1
    c = results[0]
    assert c.cfr_title == 28
    assert c.cfr_part == "23"
    assert "Part 23" in c.canonical


def test_cfr_informal():
    results = parse_cfr("34 CFR part 85")
    assert results[0].cfr_title == 34


def test_cfr_with_subdivision():
    results = parse_cfr("2 C.F.R. § 200.303(a)")
    assert results[0].subdivision == "(a)"


# ---------------------------------------------------------------------------
# California codes
# ---------------------------------------------------------------------------


def test_cal_gov_code_old_form():
    results = parse_cal_code("Gov. Code § 6254(f)")
    assert len(results) == 1
    c = results[0]
    assert c.citation_type == "cal_code"
    assert c.corpus_id == "cal_gov_code"
    assert c.section == "6254"
    assert "(f)" in (c.subdivision or "")
    assert "Gov. Code § 6254" in c.canonical


def test_cal_gov_code_new_form():
    results = parse_cal_code("Gov. Code § 7923.650")
    assert results[0].section == "7923.650"
    assert results[0].corpus_id == "cal_gov_code"


def test_cal_gov_code_full_name():
    results = parse_cal_code("Government Code section 6250")
    assert results[0].section == "6250"


def test_cal_gov_code_with_cal_prefix():
    results = parse_cal_code("Cal. Gov. Code § 6255")
    assert results[0].section == "6255"


def test_cal_penal_code():
    results = parse_cal_code("Pen. Code § 832.7")
    assert results[0].corpus_id == "cal_pen_code"
    assert results[0].section == "832.7"


def test_cal_civil_code_alpr():
    results = parse_cal_code("Civ. Code § 1798.90.55")
    assert results[0].corpus_id == "cal_civ_code"
    assert results[0].section == "1798.90.55"


def test_cal_ccp():
    results = parse_cal_code("Code Civ. Proc. § 1085")
    assert results[0].corpus_id == "cal_ccp"
    assert results[0].section == "1085"


def test_cal_welfare_code():
    results = parse_cal_code("Welf. & Inst. Code § 827")
    assert results[0].corpus_id == "cal_welf_inst_code"
    assert results[0].section == "827"


def test_cal_vehicle_code():
    results = parse_cal_code("Veh. Code § 2413")
    assert results[0].corpus_id == "cal_veh_code"
    assert results[0].section == "2413"


def test_cal_code_no_false_positive_on_usc():
    # Plain "42 U.S.C. § 1983" should NOT be picked up by cal_code parser
    results = parse_cal_code("42 U.S.C. § 1983")
    assert results == []


# ---------------------------------------------------------------------------
# California case law
# ---------------------------------------------------------------------------


def test_cal_case_basic():
    results = parse_cal_case("CBS, Inc. v. Block (1986) 42 Cal.3d 646")
    assert len(results) == 1
    c = results[0]
    assert c.citation_type == "cal_case"
    assert "CBS" in c.parties
    assert c.year == 1986
    assert c.volume == 42
    assert c.reporter == "Cal.3d"
    assert c.page == 646


def test_cal_case_app_reporter():
    results = parse_cal_case(
        "ACLU v. Superior Court (2011) 202 Cal.App.4th 55"
    )
    assert results[0].reporter == "Cal.App.4th"
    assert results[0].volume == 202


def test_cal_case_canonical():
    results = parse_cal_case("City of San Jose v. Superior Court (1974) 12 Cal.3d 447")
    c = results[0]
    assert "City of San Jose" in c.canonical
    assert "1974" in c.canonical
    assert "Cal.3d" in c.canonical


def test_cal_case_no_false_positive():
    # Generic non-case text should not match
    results = parse_cal_case("See the documents filed in 2023.")
    assert results == []


# ---------------------------------------------------------------------------
# Combined parse_citations()
# ---------------------------------------------------------------------------


def test_parse_citations_mixed_text():
    text = (
        "The agency invoked Gov. Code § 6254(f) and 34 U.S.C. § 10152, "
        "citing 2 C.F.R. § 200.303 compliance. See CBS, Inc. v. Block "
        "(1986) 42 Cal.3d 646."
    )
    cites = parse_citations(text)
    types = {c.citation_type for c in cites}
    assert "usc" in types
    assert "cfr" in types
    assert "cal_code" in types
    assert "cal_case" in types


def test_parse_citations_empty_returns_empty():
    assert parse_citations("") == []
    assert parse_citations("no citations here at all") == []
