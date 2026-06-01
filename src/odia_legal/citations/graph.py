"""Legal citation graph — CITES, AMENDS, IMPLEMENTS, OVERRULED_BY relationships.

Builds a directed multigraph of citations across statutes, regulations, and
case law using NetworkX.  Nodes represent legal authorities; edges represent
relationships between them.

Node types:
  statute    — California or federal statutory section (e.g. "Gov. Code § 7923.650")
  regulation — CFR section (e.g. "2 C.F.R. § 200.303")
  case       — Judicial opinion (e.g. "CBS v. Block (1986) 42 Cal.3d 646")

Edge types (relationship labels):
  CITES        — one authority explicitly cites another
  AMENDS       — one statute amends another (SB 1421 amends Pen. Code § 832.7)
  IMPLEMENTS   — regulation or policy implements a statute
  OVERRULED_BY — case or statute overrules prior authority
  CODIFIED_AS  — old-form citation recodified as new form (SB 1439 crosswalk)
  RELATED_TO   — informational relationship

Usage::

    from odia_legal.citations.graph import CitationGraph

    g = CitationGraph()
    g.add_cpra_relationships()
    g.add_alpr_relationships()

    # Find all statutes that cite § 7923.650
    citors = g.citing(\"Gov. Code § 7923.650\")

    # Find overruling chain for Copley Press
    chain = g.overruled_by_chain(\"Copley Press v. Superior Court\")

    # Export for Gephi / visualization
    data = g.to_dict()
"""

from __future__ import annotations

from typing import Any

try:
    import networkx as nx

    _NX_AVAILABLE = True
except ImportError:
    nx = None  # type: ignore
    _NX_AVAILABLE = False


class CitationGraph:
    """Directed multigraph of legal authority citations.

    Falls back to a stub implementation when NetworkX is not installed so
    the rest of the codebase can import this module unconditionally.
    """

    EDGE_TYPES = frozenset(
        {
            "CITES",
            "AMENDS",
            "IMPLEMENTS",
            "OVERRULED_BY",
            "CODIFIED_AS",
            "RELATED_TO",
        }
    )

    def __init__(self) -> None:
        if _NX_AVAILABLE:
            self._g: Any = nx.MultiDiGraph()
        else:
            self._g = None
        self._node_types: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Graph construction helpers
    # ------------------------------------------------------------------

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str | None = None,
        **attrs: Any,
    ) -> None:
        """Add a legal authority node."""
        self._node_types[node_id] = node_type
        if self._g is not None:
            self._g.add_node(
                node_id,
                node_type=node_type,
                label=label or node_id,
                **attrs,
            )

    def add_edge(
        self,
        source: str,
        target: str,
        relationship: str,
        weight: float = 1.0,
        notes: str | None = None,
    ) -> None:
        """Add a directed relationship edge.

        Both nodes are auto-added if not already present.
        """
        if relationship not in self.EDGE_TYPES:
            raise ValueError(f"Unknown relationship type: {relationship!r}")
        for nid in (source, target):
            if nid not in self._node_types:
                self.add_node(nid, "unknown")
        if self._g is not None:
            self._g.add_edge(
                source,
                target,
                relationship=relationship,
                weight=weight,
                notes=notes,
            )

    # ------------------------------------------------------------------
    # Bulk relationship builders
    # ------------------------------------------------------------------

    def add_cpra_relationships(self) -> None:
        """Add CPRA statutory relationships (SB 1439 recodification + case law)."""
        # Nodes
        for nid, label in [
            ("Gov. Code § 7920.000", "CPRA — legislative intent"),
            ("Gov. Code § 7920.540", "CPRA — public records definition"),
            ("Gov. Code § 7922.000", "CPRA — catch-all balancing (§ 6255)"),
            ("Gov. Code § 7922.500", "CPRA — right of access"),
            ("Gov. Code § 7922.535", "CPRA — 10-day response"),
            ("Gov. Code § 7923.600", "CPRA — enumerated exemptions"),
            ("Gov. Code § 7923.650", "CPRA — law enforcement records"),
            ("Gov. Code § 7923.700", "CPRA — attorney-client privilege"),
            ("Gov. Code § 7923.115", "CPRA — judicial enforcement"),
            ("Gov. Code § 7927.700", "CPRA — employee salary disclosure"),
        ]:
            self.add_node(nid, "statute", label=label)

        for nid, label in [
            (
                "CBS v. Block (1986) 42 Cal.3d 646",
                "Burden on agency; liberal construction",
            ),
            (
                "City of San Jose v. Superior Court (1974) 12 Cal.3d 447",
                "Broad public records definition",
            ),
            (
                "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325",
                "Catch-all balancing test",
            ),
            (
                "Copley Press v. Superior Court (2006) 39 Cal.4th 1272",
                "Officer records pre-SB 1421",
            ),
            (
                "LA County Board v. Superior Court (2016) 2 Cal.5th 282",
                "Attorney-client privilege scope",
            ),
            (
                "City of San Jose v. Superior Court (2017) 2 Cal.5th 608",
                "Personal-device rule",
            ),
            (
                "ACLU v. Superior Court (2011) 202 Cal.App.4th 55",
                "ALPR bulk data; particularized showing",
            ),
        ]:
            self.add_node(nid, "case", label=label)

        for nid, label in [
            ("SB 1439 (2021)", "CPRA recodification effective 2022-01-01"),
            ("SB 1421 (2018)", "Peace officer misconduct records public"),
        ]:
            self.add_node(nid, "statute", label=label)

        # Recodification edges (SB 1439)
        for old_sec in [
            "Gov. Code § 6250",
            "Gov. Code § 6254(f)",
            "Gov. Code § 6255",
        ]:
            self.add_node(old_sec, "statute", label="Pre-2022 CPRA section")
            self.add_edge(
                "SB 1439 (2021)",
                old_sec,
                "AMENDS",
                notes="SB 1439 recodified CPRA effective January 1, 2022",
            )

        # Case → statute CITES relationships
        self.add_edge(
            "CBS v. Block (1986) 42 Cal.3d 646", "Gov. Code § 7920.000", "CITES"
        )
        self.add_edge(
            "Times Mirror Co. v. Superior Court (1991) 53 Cal.3d 1325",
            "Gov. Code § 7922.000",
            "CITES",
        )
        self.add_edge(
            "Copley Press v. Superior Court (2006) 39 Cal.4th 1272",
            "Gov. Code § 7923.650",
            "CITES",
        )
        self.add_edge(
            "LA County Board v. Superior Court (2016) 2 Cal.5th 282",
            "Gov. Code § 7923.700",
            "CITES",
        )
        self.add_edge(
            "City of San Jose v. Superior Court (2017) 2 Cal.5th 608",
            "Gov. Code § 7920.540",
            "CITES",
        )
        self.add_edge(
            "ACLU v. Superior Court (2011) 202 Cal.App.4th 55",
            "Gov. Code § 7923.650",
            "CITES",
        )

        # SB 1421 overruling: Copley Press --OVERRULED_BY--> SB 1421
        self.add_edge(
            "Copley Press v. Superior Court (2006) 39 Cal.4th 1272",
            "SB 1421 (2018)",
            "OVERRULED_BY",
            notes="SB 1421 partially overruled categorical officer-record confidentiality for specified categories",
        )

    def add_alpr_relationships(self) -> None:
        """Add ALPR/surveillance statutory relationships."""
        for nid, label in [
            ("Civ. Code § 1798.90.51", "ALPR — definitions (SB 34)"),
            ("Civ. Code § 1798.90.52", "ALPR — operator requirements"),
            ("Civ. Code § 1798.90.53", "ALPR — 60-day retention limit"),
            ("Civ. Code § 1798.90.55", "ALPR — CPRA exemption"),
            ("Veh. Code § 2413", "ALPR — law enforcement use restrictions"),
            ("Gov. Code § 36000", "AB 481 — military equipment definitions"),
            ("Gov. Code § 36001", "AB 481 — governing-body approval required"),
            ("Gov. Code § 36002", "AB 481 — annual report required"),
        ]:
            self.add_node(nid, "statute", label=label)

        for nid, label in [
            ("SB 34 (2015)", "ALPR Data Privacy Act"),
            ("AB 481 (2021)", "Military Equipment Ordinance"),
        ]:
            self.add_node(nid, "statute", label=label)

        # IMPLEMENTS edges
        self.add_edge("Civ. Code § 1798.90.51", "SB 34 (2015)", "IMPLEMENTS")
        self.add_edge("Veh. Code § 2413", "SB 34 (2015)", "IMPLEMENTS")
        for sec in ["Gov. Code § 36000", "Gov. Code § 36001", "Gov. Code § 36002"]:
            self.add_edge(sec, "AB 481 (2021)", "IMPLEMENTS")

        # ALPR → CPRA relationship
        self.add_edge(
            "Civ. Code § 1798.90.55",
            "Gov. Code § 7923.650",
            "RELATED_TO",
            notes="Both govern access to ALPR records; § 1798.90.55 provides alternative CPRA exemption for SB 34 operators",
        )

    def add_federal_grant_relationships(self) -> None:
        """Add JAG/Byrne grant compliance relationships."""
        for nid, label in [
            ("34 U.S.C. § 10152", "JAG — Edward Byrne Memorial grants"),
            ("34 U.S.C. § 10101", "OJP establishment"),
            ("2 C.F.R. § 200.303", "Uniform Guidance — internal controls"),
            ("2 C.F.R. § 200.318", "Uniform Guidance — procurement standards"),
            ("2 C.F.R. § 200.330", "Uniform Guidance — pass-through entities"),
            ("28 C.F.R. § 23.20", "Criminal intelligence — operating principles"),
            ("42 U.S.C. § 1983", "Civil action for rights deprivation"),
        ]:
            self.add_node(
                nid, "statute" if "U.S.C." in nid else "regulation", label=label
            )

        self.add_edge("34 U.S.C. § 10152", "34 U.S.C. § 10101", "CITES")
        self.add_edge(
            "2 C.F.R. § 200.303",
            "34 U.S.C. § 10152",
            "IMPLEMENTS",
            notes="Uniform Guidance internal controls apply to JAG grant recipients",
        )
        self.add_edge(
            "28 C.F.R. § 23.20",
            "34 U.S.C. § 10152",
            "IMPLEMENTS",
            notes="28 CFR Part 23 governs criminal intelligence systems funded by JAG",
        )

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def citing(self, node_id: str, relationship: str = "CITES") -> list[str]:
        """Return all nodes that have a given relationship TO node_id."""
        if self._g is None:
            return []
        return [
            src
            for src, tgt, data in self._g.edges(data=True)
            if tgt == node_id and data.get("relationship") == relationship
        ]

    def cited_by(self, node_id: str, relationship: str = "CITES") -> list[str]:
        """Return all nodes that node_id has a given relationship TO."""
        if self._g is None:
            return []
        return [
            tgt
            for src, tgt, data in self._g.edges(data=True)
            if src == node_id and data.get("relationship") == relationship
        ]

    def overruled_by_chain(self, node_id: str) -> list[str]:
        """Return the chain of authorities that overrule node_id."""
        if self._g is None:
            return []
        chain: list[str] = []
        current = node_id
        seen: set[str] = set()
        while True:
            overrulers = [
                tgt
                for src, tgt, data in self._g.edges(data=True)
                if src == current and data.get("relationship") == "OVERRULED_BY"
            ]
            if not overrulers or overrulers[0] in seen:
                break
            chain.append(overrulers[0])
            seen.add(overrulers[0])
            current = overrulers[0]
        return chain

    def neighbors(self, node_id: str) -> list[str]:
        """Return all directly connected nodes (any relationship)."""
        if self._g is None:
            return []
        return list(self._g.neighbors(node_id))

    def statistics(self) -> dict[str, int]:
        """Return graph size statistics."""
        if self._g is None:
            return {"nodes": 0, "edges": 0, "nx_available": 0}
        node_counts: dict[str, int] = {}
        for _, data in self._g.nodes(data=True):
            ntype = data.get("node_type", "unknown")
            node_counts[f"nodes_{ntype}"] = node_counts.get(f"nodes_{ntype}", 0) + 1
        return {
            "nodes": self._g.number_of_nodes(),
            "edges": self._g.number_of_edges(),
            "nx_available": 1,
            **node_counts,
        }

    def to_dict(self) -> dict[str, Any]:
        """Export graph as a serializable dict (nodes + edges lists)."""
        if self._g is None:
            return {"nodes": [], "edges": []}
        nodes = [{"id": nid, **data} for nid, data in self._g.nodes(data=True)]
        edges = [
            {"source": src, "target": tgt, **data}
            for src, tgt, data in self._g.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}


def build_default_graph() -> CitationGraph:
    """Build and return the default ODIA citation graph."""
    g = CitationGraph()
    g.add_cpra_relationships()
    g.add_alpr_relationships()
    g.add_federal_grant_relationships()
    return g
