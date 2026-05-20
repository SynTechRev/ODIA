"""Tests for USCodeLoader against the real nickvido/us-code submodule.

Skipped when the submodule isn't initialized (so CI without `git
submodule update --init` doesn't fail hard).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from oraculus_di_auditor.legal.us_code_loader import USCodeLoader


@pytest.fixture(scope="module")
def loader():
    submodule = Path("data/legal_corpora/us-code")
    if not (submodule / "uscode").exists():
        pytest.skip(
            "USC submodule not initialized; run "
            "`git submodule update --init --recursive`"
        )
    ldr = USCodeLoader(submodule)
    stats = ldr.initialize()
    assert stats["titles"] >= 50, f"expected ~54 USC titles, got {stats['titles']}"
    return ldr


def test_resolves_jag_anti_supplanting(loader):
    """34 U.S.C. § 10152 — the JAG grant statute O.D.I.A. cites in
    real findings across the corpus. Must resolve and the resolved
    text must talk about the JAG program (grants, formula, allocation)."""
    result = loader.resolve_citation("34 U.S.C. § 10152")
    assert result is not None, "JAG statute must resolve"
    assert result.corpus_id == "us-code"
    # Title-34 section 10152 is "Description" of JAG program;
    # text mentions grants and the program structure.
    body_lower = result.text.lower()
    assert "grant" in body_lower or "program" in body_lower
    # Source path must point at the chapter file in the submodule.
    assert "title-34" in result.source_path
    assert "chapter-101" in result.source_path


def test_resolves_section_1983(loader):
    """42 U.S.C. § 1983 — Monell, civil rights deprivation.
    The exact statute cited in plain_language.py:253."""
    result = loader.resolve_citation("42 U.S.C. § 1983")
    assert result is not None
    # § 1983 is the classic "deprivation of any rights, privileges,
    # or immunities" under color of law statute.
    body_lower = result.text.lower()
    assert (
        "color" in body_lower or "deprivation" in body_lower or "rights" in body_lower
    )


def test_returns_none_on_nonexistent_section(loader):
    """A section that doesn't exist in title 34 must return None
    (not raise, not return garbage)."""
    result = loader.resolve_citation("34 U.S.C. § 99999")
    assert result is None


def test_url_points_at_cornell_lii(loader):
    """Every resolved citation gets a Cornell LII URL so the operator
    can verify the text against an authoritative external source."""
    result = loader.resolve_citation("18 U.S.C. § 242")
    assert result is not None
    assert result.url is not None
    assert "law.cornell.edu" in result.url
    assert "/uscode/text/18/242" in result.url


def test_statistics_reports_substantive_corpus(loader):
    """Stats endpoint feeds /api/v1/legal/status; must report a
    plausibly-complete index."""
    stats = loader.statistics()
    assert stats["titles_indexed"] >= 50, stats
    # The USC has on the order of 50,000+ sections; we should index
    # a substantive fraction (5000+ is the conservative floor).
    assert stats["sections_indexed"] >= 5000, stats


def test_canonical_citation_preserved(loader):
    """The .citation field on a LegalText must be the canonical form
    of the input (so cache keys are stable)."""
    result = loader.resolve_citation("34 USC 10152")  # informal input
    assert result is not None
    assert result.citation == "34 U.S.C. § 10152"  # canonical output
    assert result.citation_raw == "34 USC 10152"  # raw preserved
