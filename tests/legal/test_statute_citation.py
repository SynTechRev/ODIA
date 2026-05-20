"""Tests for the USC citation parser."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.legal.statute_citation import (
    parse_single,
    parse_usc_citations,
)


@pytest.mark.parametrize(
    "text, expected_title, expected_section, expected_sub",
    [
        ("34 U.S.C. § 10152", 34, "10152", ""),
        ("34 U.S.C. § 10152(a)(1)(G)", 34, "10152", "(a)(1)(G)"),
        ("42 U.S.C. § 1983", 42, "1983", ""),
        ("34 USC 10152", 34, "10152", ""),
        ("see 18 U.S.C. § 242 et seq.", 18, "242", ""),
        ("EMTALA, 42 U.S.C. § 1395dd", 42, "1395dd", ""),
    ],
)
def test_parses_known_formats(text, expected_title, expected_section, expected_sub):
    cit = parse_single(text)
    assert cit is not None, f"failed to parse: {text!r}"
    assert cit.title == expected_title
    assert cit.section == expected_section
    assert cit.subsection_path == expected_sub


def test_rejects_invalid_titles():
    """Title 99 doesn't exist in the USC; must not match."""
    assert parse_single("99 U.S.C. § 1") is None


def test_rejects_cfr_lookalike():
    """CFR is a different corpus; this parser must NOT catch it.

    Pre-v3.3.0 a naive USC regex would happily match the digits in
    '2 C.F.R. § 200.303' as title=2, section=200; the negative
    lookbehind in the pattern blocks that."""
    assert parse_single("2 C.F.R. § 200.303") is None
    assert parse_single("compliance violation under 2 C.F.R. § 200.303") is None


def test_extracts_multiple():
    text = "Violations of 34 U.S.C. § 10152 and 42 U.S.C. § 1983 are alleged."
    cits = parse_usc_citations(text)
    assert len(cits) == 2
    assert cits[0].title == 34
    assert cits[1].title == 42


def test_canonical_normalization():
    """Informal '34 USC 10152(a)(1)(G)' must normalise to the
    canonical 'N U.S.C. § N(...)' form so the cache key is stable
    regardless of how the citation appears in narrative text."""
    cit = parse_single("34 USC 10152(a)(1)(G)")
    assert cit is not None
    assert cit.canonical == "34 U.S.C. § 10152(a)(1)(G)"


def test_real_grant_compliance_narrative():
    """Regression guard: this is the exact phrasing in
    grant_compliance.py:87 (verified during pre-flight).
    The parser MUST extract it."""
    narrative = (
        "certification — 34 U.S.C. § 10152 requires certification "
        "that funds will not supplant existing State, local, or "
        "tribal funds"
    )
    cit = parse_single(narrative)
    assert cit is not None
    assert cit.title == 34
    assert cit.section == "10152"
    assert cit.canonical == "34 U.S.C. § 10152"


def test_real_plain_language_narrative():
    """Regression guard: this is plain_language.py:253 phrasing."""
    narrative = "liability under 42 U.S.C. § 1983."
    cit = parse_single(narrative)
    assert cit is not None
    assert cit.title == 42
    assert cit.section == "1983"


def test_subsection_canonical_with_real_grant_form():
    """Regression guard: grant_compliance.py:91 has
    '34 U.S.C. § 10152(a)(1)(G)' as a Pydantic field default.
    Subsection must survive parsing."""
    cit = parse_single("34 U.S.C. § 10152(a)(1)(G)")
    assert cit is not None
    assert cit.subsection_path == "(a)(1)(G)"
    assert cit.section_root == "10152"
