"""Tests for FederalAdjudicationLoader (OAH, MSPB, EEOC, PCLOB)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from odia_legal.corpus.federal_adjudication_loader import FederalAdjudicationLoader


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    """Write minimal decision files to a temp directory."""
    bodies = {
        "oah": [
            {
                "body": "oah",
                "decision_id": "TEST-OAH-001",
                "title": "In the Matter of ALPR Data Retention",
                "docket": "OAH-2023-01001",
                "date": "2023-06-15",
                "topics": ["alpr", "cpra"],
                "holding": "Agency violated SB 34 by retaining ALPR data beyond 60 days.",
                "text": "Full decision text about ALPR retention.",
                "url": "https://example.com/oah/001",
            }
        ],
        "mspb": [
            {
                "body": "mspb",
                "decision_id": "TEST-MSPB-001",
                "title": "Whistleblower Retaliation — Surveillance Program",
                "docket": "DC-1221-23-0001-W-1",
                "date": "2023-04-20",
                "topics": ["whistleblower", "surveillance", "5 usc 2302"],
                "holding": "Removal reversed; protected disclosure under WPA.",
                "text": "Appellant disclosed unauthorized facial recognition program.",
                "url": "https://example.com/mspb/001",
            }
        ],
        "eeoc": [
            {
                "body": "eeoc",
                "decision_id": "TEST-EEOC-001",
                "title": "Disparate Impact of Facial Recognition in Hiring",
                "docket": "2023-00123456",
                "date": "2023-08-14",
                "topics": ["facial recognition", "disparate impact", "title vii"],
                "holding": "Facial recognition with disparate impact violates Title VII.",
                "text": "Statistical analysis showed 2.3x higher rejection rates.",
                "url": "https://example.com/eeoc/001",
            }
        ],
        "pclob": [
            {
                "body": "pclob",
                "decision_id": "TEST-PCLOB-001",
                "title": "ALPR Programs and Civil Liberties",
                "docket": "2023-01",
                "date": "2023-09-15",
                "topics": ["alpr", "carpenter", "mosaic theory"],
                "holding": "ALPR without retention limits raises Carpenter concerns.",
                "text": "Carpenter mosaic theory applies to ALPR programs.",
                "url": "https://example.com/pclob/001",
            }
        ],
    }

    for body, decisions in bodies.items():
        body_dir = tmp_path / body
        body_dir.mkdir()
        for decision in decisions:
            (body_dir / f"{decision['decision_id'].lower()}.json").write_text(
                json.dumps(decision), encoding="utf-8"
            )
    return tmp_path


@pytest.fixture
def loader(corpus_dir: Path) -> FederalAdjudicationLoader:
    ldr = FederalAdjudicationLoader(corpus_dir)
    ldr.initialize()
    return ldr


# ===========================================================================
# initialize()
# ===========================================================================


def test_initialize_loads_all_bodies(loader):
    stats = loader.statistics()
    assert stats["oah"] == 1
    assert stats["mspb"] == 1
    assert stats["eeoc"] == 1
    assert stats["pclob"] == 1
    assert stats["total_decisions"] == 4


def test_initialize_missing_root_returns_empty():
    ldr = FederalAdjudicationLoader("/nonexistent/path/xyz")
    counts = ldr.initialize()
    assert counts == {}


def test_bodies_loaded(loader):
    bodies = loader.bodies_loaded()
    for b in ("oah", "mspb", "eeoc", "pclob"):
        assert b in bodies


# ===========================================================================
# resolve_citation() — OAH
# ===========================================================================


def test_resolve_oah(loader):
    result = loader.resolve_citation("OAH No. OAH-2023-01001")
    assert result is not None
    assert result.corpus_id == "federal_adjudication"
    assert "ALPR" in result.title
    assert "60 days" in result.text


def test_resolve_oah_with_period(loader):
    result = loader.resolve_citation("OAH No. OAH-2023-01001")
    assert result is not None
    assert result.as_of is not None


# ===========================================================================
# resolve_citation() — MSPB
# ===========================================================================


def test_resolve_mspb(loader):
    result = loader.resolve_citation("MSPB Docket No. DC-1221-23-0001-W-1")
    assert result is not None
    assert "Whistleblower" in result.title
    assert "MSPB" in result.citation


def test_resolve_mspb_no_docket_prefix(loader):
    result = loader.resolve_citation("MSPB DC-1221-23-0001-W-1")
    assert result is not None


# ===========================================================================
# resolve_citation() — EEOC
# ===========================================================================


def test_resolve_eeoc(loader):
    result = loader.resolve_citation("EEOC No. 2023-00123456")
    assert result is not None
    assert "Facial Recognition" in result.title
    assert result.as_of is not None


def test_resolve_eeoc_appeal_prefix(loader):
    result = loader.resolve_citation("EEOC Appeal No. 2023-00123456")
    assert result is not None


# ===========================================================================
# resolve_citation() — PCLOB
# ===========================================================================


def test_resolve_pclob(loader):
    result = loader.resolve_citation("PCLOB Report 2023-01")
    assert result is not None
    assert "ALPR" in result.title


def test_resolve_pclob_no_report_word(loader):
    result = loader.resolve_citation("PCLOB 2023-01")
    assert result is not None


# ===========================================================================
# Unknown citations
# ===========================================================================


def test_unknown_citation_returns_none(loader):
    assert loader.resolve_citation("OAH No. OAH-9999-99999") is None
    assert loader.resolve_citation("Cal. Gov. Code § 7922.000") is None
    assert loader.resolve_citation("random text") is None


# ===========================================================================
# search_text()
# ===========================================================================


def test_search_finds_by_topic(loader):
    results = loader.search_text("carpenter")
    assert len(results) >= 1
    assert any("ALPR" in r.title or "mosaic" in r.text.lower() for r in results)


def test_search_case_insensitive(loader):
    results = loader.search_text("ALPR")
    assert len(results) >= 1


def test_search_limit(loader):
    results = loader.search_text("decision", limit=2)
    assert len(results) <= 2


def test_search_no_match(loader):
    assert loader.search_text("xyzzynotreal") == []


# ===========================================================================
# Utility methods
# ===========================================================================


def test_list_amendments_returns_empty(loader):
    assert loader.list_amendments("OAH No. OAH-2023-01001") == []


def test_statistics(loader):
    stats = loader.statistics()
    assert "total_decisions" in stats
    assert stats["total_decisions"] == 4


def test_decisions_for_body(loader):
    decisions = loader.decisions_for_body("oah")
    assert len(decisions) == 1
    assert "ALPR" in decisions[0]["title"]


# ===========================================================================
# LegalText fields
# ===========================================================================


def test_legaltext_structure(loader):
    result = loader.resolve_citation("PCLOB Report 2023-01")
    assert result is not None
    assert result.corpus_id == "federal_adjudication"
    assert result.citation.startswith("PCLOB")
    assert result.as_of is not None
    assert result.url == "https://example.com/pclob/001"
