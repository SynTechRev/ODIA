"""Tests for the plain-language community education explainer."""

from __future__ import annotations

from odia_legal.reports.explainer import generate_explainer, Explainer

_DOC_META = {
    "title": "ALPR Retention Policy 2024",
    "agency": "Anytown Police Department",
    "date": "2024-03-15",
}

_FINDINGS = [
    {
        "id": "legal:l3:exemption_misapplication:cpra_catchall",
        "issue": "CPRA catch-all exemption invoked without balancing test",
        "severity": "high",
        "layer": "l3_exemption_misapplication",
        "details": {
            "statute": "Gov. Code § 7922.000",
            "detail": "Agency must demonstrate why nondisclosure clearly outweighs disclosure.",
        },
    },
    {
        "id": "legal:l2:procedural_compliance:ab481_missing",
        "issue": "AB 481 policy not adopted before ALPR deployment",
        "severity": "medium",
        "layer": "l2_procedural_compliance",
        "details": {
            "detail": "AB 481 requires governing body approval prior to surveillance deployment.",
        },
    },
    {
        "id": "legal:l1:statutory_applicability:alpr_retention",
        "issue": "Statute applies: Civ. Code § 1798.90.53 — ALPR retention",
        "severity": "low",
        "layer": "l1_statutory_applicability",
        "details": {
            "relevance": "SB 34 limits ALPR data retention to 60 days.",
        },
    },
]


# ===========================================================================
# Basic structure
# ===========================================================================


def test_returns_explainer_instance():
    result = generate_explainer(_DOC_META, _FINDINGS)
    assert isinstance(result, Explainer)


def test_title_line_contains_doc_title():
    result = generate_explainer(_DOC_META, _FINDINGS)
    assert "ALPR Retention Policy 2024" in result.title_line


def test_to_text_contains_summary():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "FINDINGS AT A GLANCE" in text


def test_to_text_total_count():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "3" in text


def test_to_text_high_count():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "1" in text


def test_str_equals_to_text():
    result = generate_explainer(_DOC_META, _FINDINGS)
    assert str(result) == result.to_text()


# ===========================================================================
# Jargon substitution
# ===========================================================================


def test_alpr_jargon_expanded():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "automated license plate readers" in text


def test_ab481_jargon_expanded():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "2021 law" in text or "Assembly Bill 481" in text


def test_cpra_jargon_expanded():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "Public Records Act" in text


# ===========================================================================
# Severity labels
# ===========================================================================


def test_high_severity_label():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "SERIOUS CONCERN" in text


def test_medium_severity_label():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "WORTH INVESTIGATING" in text


def test_low_severity_label():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "INFORMATIONAL" in text


# ===========================================================================
# Severity action guidance
# ===========================================================================


def test_high_severity_action_mentions_attorney():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "attorney" in text or "complaint" in text


# ===========================================================================
# Sections
# ===========================================================================


def test_sections_grouped_by_layer():
    result = generate_explainer(_DOC_META, _FINDINGS)
    layer_titles = [s[0] for s in result.sections]
    assert any("records" in t.lower() or "denied" in t.lower() for t in layer_titles)


def test_sections_count_equals_unique_layers():
    result = generate_explainer(_DOC_META, _FINDINGS)
    unique_layers = len({f["layer"] for f in _FINDINGS})
    assert len(result.sections) == unique_layers


def test_detail_text_appears_in_section():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "60 days" in text


def test_what_this_means_label():
    text = generate_explainer(_DOC_META, _FINDINGS).to_text()
    assert "What this means" in text


# ===========================================================================
# Audience variants
# ===========================================================================


def test_community_audience_closing():
    result = generate_explainer(_DOC_META, _FINDINGS, audience="community")
    assert "public records request" in result.closing.lower() or "muckrock" in result.closing.lower()


def test_council_audience_closing():
    result = generate_explainer(_DOC_META, _FINDINGS, audience="council")
    assert "council" in result.closing.lower() or "agency counsel" in result.closing.lower()


def test_media_audience_closing():
    result = generate_explainer(_DOC_META, _FINDINGS, audience="media")
    assert "questions" in result.closing.lower() or "agency" in result.closing.lower()


def test_council_intro_different_from_community():
    comm = generate_explainer(_DOC_META, _FINDINGS, audience="community").intro
    council = generate_explainer(_DOC_META, _FINDINGS, audience="council").intro
    assert comm != council


# ===========================================================================
# Empty findings
# ===========================================================================


def test_empty_findings_zero_counts():
    result = generate_explainer(_DOC_META, [])
    assert "0" in result.summary_table
    assert result.sections == []


# ===========================================================================
# HTML output
# ===========================================================================


def test_html_has_h1():
    html = generate_explainer(_DOC_META, _FINDINGS).to_html()
    assert "<h1>" in html


def test_html_has_h2_sections():
    html = generate_explainer(_DOC_META, _FINDINGS).to_html()
    assert html.count("<h2>") >= 3  # Summary + at least 1 layer section + closing


def test_html_contains_finding_issue():
    html = generate_explainer(_DOC_META, _FINDINGS).to_html()
    assert "balancing test" in html or "catch-all exemption" in html
