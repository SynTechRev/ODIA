"""Tests for the legal citation graph."""

from __future__ import annotations

import pytest

from odia_legal.citations.graph import CitationGraph, build_default_graph

try:
    import networkx  # noqa: F401

    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False

pytestmark = pytest.mark.skipif(not NX_AVAILABLE, reason="networkx not installed")


@pytest.fixture
def cpra_graph():
    g = CitationGraph()
    g.add_cpra_relationships()
    return g


@pytest.fixture
def full_graph():
    return build_default_graph()


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def test_cpra_graph_has_nodes(cpra_graph):
    stats = cpra_graph.statistics()
    assert stats["nodes"] >= 10
    assert stats["edges"] >= 5


def test_cpra_graph_has_statute_nodes(cpra_graph):
    stats = cpra_graph.statistics()
    assert stats.get("nodes_statute", 0) >= 5


def test_cpra_graph_has_case_nodes(cpra_graph):
    stats = cpra_graph.statistics()
    assert stats.get("nodes_case", 0) >= 5


def test_full_graph_has_all_domains(full_graph):
    stats = full_graph.statistics()
    assert stats["nodes"] >= 25
    assert stats["edges"] >= 15


# ---------------------------------------------------------------------------
# CITES relationships
# ---------------------------------------------------------------------------


def test_times_mirror_cites_catch_all(cpra_graph):
    cited = cpra_graph.cited_by(
        "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325", "CITES"
    )
    assert "Gov. Code § 7922.000" in cited


def test_aclu_cites_law_enforcement_exemption(cpra_graph):
    cited = cpra_graph.cited_by(
        "ACLU v. Superior Court (2011) 202 Cal.App.4th 55", "CITES"
    )
    assert "Gov. Code § 7923.650" in cited


def test_citing_returns_cases_that_cite_statute(cpra_graph):
    citors = cpra_graph.citing("Gov. Code § 7923.650", "CITES")
    assert len(citors) >= 2  # Copley Press + ACLU


# ---------------------------------------------------------------------------
# OVERRULED_BY relationships
# ---------------------------------------------------------------------------


def test_sb1421_overrules_copley_press(cpra_graph):
    chain = cpra_graph.overruled_by_chain(
        "Copley Press v. Superior Court (2006) 39 Cal.4th 1272"
    )
    assert len(chain) >= 1
    assert "SB 1421 (2018)" in chain


def test_overruled_by_chain_stops_at_end(cpra_graph):
    chain = cpra_graph.overruled_by_chain("Gov. Code § 7920.000")
    assert chain == []


# ---------------------------------------------------------------------------
# IMPLEMENTS relationships
# ---------------------------------------------------------------------------


def test_uniform_guidance_implements_jag(full_graph):
    cited = full_graph.cited_by("2 C.F.R. § 200.303", "IMPLEMENTS")
    assert "34 U.S.C. § 10152" in cited


def test_ab481_sections_implement_statute(full_graph):
    cited = full_graph.cited_by("Gov. Code § 36000", "IMPLEMENTS")
    assert "AB 481 (2021)" in cited


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def test_to_dict_has_nodes_and_edges(cpra_graph):
    d = cpra_graph.to_dict()
    assert "nodes" in d
    assert "edges" in d
    assert len(d["nodes"]) >= 10
    assert len(d["edges"]) >= 5


def test_to_dict_nodes_have_id(cpra_graph):
    d = cpra_graph.to_dict()
    for node in d["nodes"]:
        assert "id" in node


def test_to_dict_edges_have_relationship(cpra_graph):
    d = cpra_graph.to_dict()
    for edge in d["edges"]:
        assert "source" in edge
        assert "target" in edge
        assert "relationship" in edge


# ---------------------------------------------------------------------------
# Edge validation
# ---------------------------------------------------------------------------


def test_invalid_relationship_raises():
    g = CitationGraph()
    g.add_node("A", "statute")
    g.add_node("B", "statute")
    with pytest.raises(ValueError, match="Unknown relationship"):
        g.add_edge("A", "B", "MADE_UP")


def test_auto_add_unknown_nodes():
    g = CitationGraph()
    g.add_edge("X", "Y", "CITES")
    stats = g.statistics()
    assert stats["nodes"] == 2
