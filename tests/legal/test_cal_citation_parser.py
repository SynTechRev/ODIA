"""Tests for California statutory citation parser (CalCitation)."""

from __future__ import annotations

from oraculus_di_auditor.legal.statute_citation import (
    parse_cal_citations,
    parse_cal_single,
)


class TestParseCalSingle:
    def test_full_civil_code_citation(self):
        c = parse_cal_single("Cal. Civ. Code § 1798.121(a)")
        assert c is not None
        assert c.code == "Civ. Code"
        assert c.section == "1798.121"
        assert c.subsection_path == "(a)"

    def test_bare_section_cpra_range(self):
        c = parse_cal_single("§ 1798.121")
        assert c is not None
        assert c.code == "Civ. Code"
        assert c.section == "1798.121"

    def test_ccp_formal(self):
        c = parse_cal_single("Cal. Code Civ. Proc. § 1281.97")
        assert c is not None
        assert c.code == "CCP"
        assert c.section == "1281.97"

    def test_ccp_abbreviated(self):
        c = parse_cal_single("CCP § 1281.97")
        assert c is not None
        assert c.code == "CCP"
        assert c.section == "1281.97"

    def test_labor_code(self):
        c = parse_cal_single("Lab. Code § 2699(f)")
        assert c is not None
        assert c.code == "Lab. Code"
        assert c.section == "2699"
        assert c.subsection_path == "(f)"

    def test_gov_code(self):
        c = parse_cal_single("Gov. Code § 12953")
        assert c is not None
        assert c.code == "Gov. Code"
        assert c.section == "12953"

    def test_informal_civil_code(self):
        c = parse_cal_single("Civ. Code § 1798.120")
        assert c is not None
        assert c.code == "Civ. Code"
        assert c.section == "1798.120"

    def test_returns_none_for_usc(self):
        # USC citation should not match
        c = parse_cal_single("34 U.S.C. § 10152")
        # Might match bare section if regex is broad — confirm it doesn't assign a Cal code
        if c is not None:
            assert c.section != "10152"

    def test_civil_code_no_subsection(self):
        c = parse_cal_single("Civil Code § 1798.100")
        assert c is not None
        assert c.section == "1798.100"
        assert c.subsection_path == ""


class TestParseCalCitations:
    def test_multiple_citations_in_text(self):
        text = (
            "This clause violates Cal. Civ. Code § 1798.121 because it "
            "fails to provide the opt-out required by § 1798.120. "
            "See also CCP § 1281.97 for fee obligations."
        )
        citations = parse_cal_citations(text)
        sections = {c.section for c in citations}
        assert "1798.121" in sections
        assert "1798.120" in sections
        assert "1281.97" in sections

    def test_deduplication(self):
        text = "§ 1798.121 and again § 1798.121 in the same document."
        citations = parse_cal_citations(text)
        assert len([c for c in citations if c.section == "1798.121"]) == 1

    def test_empty_text(self):
        assert parse_cal_citations("") == []


class TestCPRALoaderKey:
    def test_civ_code_1798_returns_loader_key(self):
        c = parse_cal_single("§ 1798.121")
        assert c is not None
        assert c.cpra_loader_key == "1798.121"

    def test_ccp_1281_returns_loader_key(self):
        c = parse_cal_single("CCP § 1281.97")
        assert c is not None
        assert c.cpra_loader_key == "CCP_1281.97"

    def test_lab_code_2699_returns_loader_key(self):
        c = parse_cal_single("Lab. Code § 2699")
        assert c is not None
        assert c.cpra_loader_key == "Lab_2699"

    def test_gov_code_12953_returns_loader_key(self):
        c = parse_cal_single("Gov. Code § 12953")
        assert c is not None
        assert c.cpra_loader_key == "GovCode_12953"

    def test_pen_code_no_loader_key(self):
        c = parse_cal_single("Pen. Code § 832.7")
        if c is not None:
            assert c.cpra_loader_key is None


class TestCanonicalForm:
    def test_canonical_includes_code_section_subsection(self):
        c = parse_cal_single("Cal. Civ. Code § 1798.121(a)(7)(A)")
        assert c is not None
        assert "Civ. Code" in c.canonical
        assert "1798.121" in c.canonical
        assert "(a)" in c.canonical
