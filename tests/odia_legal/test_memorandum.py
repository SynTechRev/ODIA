"""Tests for the litigation-grade memorandum generator."""

from __future__ import annotations

from odia_legal.reports.memorandum import Memorandum, generate_memorandum

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_DOC_META = {
    "title": "ALPR Retention Policy 2024",
    "agency": "Anytown Police Department",
    "date": "2024-03-15",
}

_FINDINGS_HIGH = [
    {
        "id": "legal:l3:exemption_misapplication:cpra_catchall_no_balancing",
        "issue": "CPRA catch-all exemption invoked without balancing test",
        "severity": "high",
        "layer": "l3_exemption_misapplication",
        "details": {
            "statute": "Gov. Code § 7922.000",
            "framework": "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325",
            "detail": "Agency must specifically demonstrate why nondisclosure clearly outweighs disclosure interest.",
        },
    },
    {
        "id": "legal:l5:federal_grant_compliance:supplanting",
        "issue": "Federal funds used to supplant existing state/local funding",
        "severity": "high",
        "layer": "l5_federal_grant_compliance",
        "details": {
            "regulation": "2 C.F.R. § 200.306",
            "detail": "JAG grant conditions prohibit supplanting.",
        },
    },
]

_FINDINGS_MIXED = _FINDINGS_HIGH + [
    {
        "id": "legal:l1:statutory_applicability:alpr_sb34",
        "issue": "Statute applies: Civ. Code § 1798.90.53 — ALPR retention",
        "severity": "low",
        "layer": "l1_statutory_applicability",
        "details": {
            "statute": "Civ. Code § 1798.90.53",
            "detail": "SB 34 limits ALPR retention to 60 days.",
        },
    },
    {
        "id": "legal:l2:procedural_compliance:ab481_missing",
        "issue": "AB 481 policy not adopted before ALPR deployment",
        "severity": "medium",
        "layer": "l2_procedural_compliance",
        "details": {
            "statute": "Gov. Code § 7070",
            "detail": "AB 481 requires governing body approval prior to deployment.",
        },
    },
]


# ===========================================================================
# Basic structure
# ===========================================================================


def test_returns_memorandum_instance():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert isinstance(memo, Memorandum)


def test_to_field_appears_in_output():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH, to_field="City Council")
    text = memo.to_text()
    assert "City Council" in text


def test_memo_date_appears():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH, memo_date="2025-01-01")
    assert "2025-01-01" in memo.to_text()


def test_re_field_contains_title():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "ALPR Retention Policy 2024" in memo.re_field


def test_re_field_contains_agency():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "Anytown Police Department" in memo.re_field


def test_section_headers_in_text():
    memo = generate_memorandum(_DOC_META, _FINDINGS_MIXED)
    text = memo.to_text()
    assert "I. OVERVIEW" in text
    assert "II. TABLE OF AUTHORITIES" in text
    assert "III. ANALYSIS" in text
    assert "IV. CONCLUSION" in text


# ===========================================================================
# Overview
# ===========================================================================


def test_overview_counts_findings():
    memo = generate_memorandum(_DOC_META, _FINDINGS_MIXED)
    assert "4" in memo.overview  # total
    assert "2" in memo.overview  # high count appears somewhere


def test_overview_empty_findings():
    memo = generate_memorandum(_DOC_META, [])
    assert "No legal findings" in memo.overview


# ===========================================================================
# Table of Authorities
# ===========================================================================


def test_toa_contains_statute_from_findings():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "Gov. Code" in memo.toa
    assert "7922.000" in memo.toa


def test_toa_contains_cfr_regulation():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "C.F.R." in memo.toa


def test_toa_contains_case_citation():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "Times Mirror" in memo.toa


def test_toa_deduplicates_citations():
    doubled = _FINDINGS_HIGH + _FINDINGS_HIGH
    memo = generate_memorandum(_DOC_META, doubled)
    # Gov. Code § 7922.000 should appear only once
    assert memo.toa.count("7922.000") == 1


def test_toa_no_citations_fallback():
    findings = [
        {
            "id": "x",
            "issue": "no citation here",
            "severity": "low",
            "layer": "l1",
            "details": {},
        }
    ]
    memo = generate_memorandum(_DOC_META, findings)
    assert "No citations identified" in memo.toa


# ===========================================================================
# Analysis section
# ===========================================================================


def test_analysis_high_severity_label():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "High-Severity" in memo.analysis


def test_analysis_medium_severity_label():
    memo = generate_memorandum(_DOC_META, _FINDINGS_MIXED)
    assert "Medium-Severity" in memo.analysis


def test_analysis_low_severity_label():
    memo = generate_memorandum(_DOC_META, _FINDINGS_MIXED)
    assert "Low-Severity" in memo.analysis


def test_analysis_finding_issue_present():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "CPRA catch-all exemption" in memo.analysis


def test_analysis_finding_id_present():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert "legal:l3:" in memo.analysis


def test_analysis_no_findings():
    memo = generate_memorandum(_DOC_META, [])
    assert "No findings to report" in memo.analysis


# ===========================================================================
# Conclusion
# ===========================================================================


def test_conclusion_high_severity_mentions_litigation():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert (
        "litigation" in memo.conclusion.lower()
        or "corrective" in memo.conclusion.lower()
    )


def test_conclusion_custom_recommended_actions():
    actions = ["Adopt AB 481 use policy", "Delete ALPR data older than 60 days"]
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH, recommended_actions=actions)
    assert "Adopt AB 481" in memo.conclusion
    assert "Delete ALPR" in memo.conclusion


def test_conclusion_no_high_severity_softer_tone():
    low_findings = [
        {
            "id": "legal:l1:x",
            "issue": "Statute applies",
            "severity": "low",
            "layer": "l1",
            "details": {},
        }
    ]
    memo = generate_memorandum(_DOC_META, low_findings)
    # Soft conclusion mentions "no immediate litigation risk", not an urgent call to action
    assert "no immediate" in memo.conclusion.lower()
    assert "corrective action" not in memo.conclusion.lower()


# ===========================================================================
# Markdown output
# ===========================================================================


def test_markdown_has_h1():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert memo.to_markdown().startswith("# MEMORANDUM")


def test_markdown_has_h2_sections():
    md = generate_memorandum(_DOC_META, _FINDINGS_MIXED).to_markdown()
    assert "## I. Overview" in md
    assert "## II. Table of Authorities" in md
    assert "## III. Analysis" in md
    assert "## IV. Conclusion" in md


def test_markdown_italic_case_in_toa():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    # The TOA uses cal_style (no italics), but markdown render keeps it readable
    md = memo.to_markdown()
    assert "Times Mirror" in md


def test_str_equals_to_text():
    memo = generate_memorandum(_DOC_META, _FINDINGS_HIGH)
    assert str(memo) == memo.to_text()
