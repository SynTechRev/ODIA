"""
CDSCE Graph Builder.

Generates graph models for semantic relationships:
- Synonym graphs
- Antonym graphs
- Etymology lineage graphs
- Doctrine-meaning graphs
- Cross-dictionary concept clusters
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class CDSCEGraphBuilder:
    """
    Graph Builder for CDSCE.

    Generates:
    - Synonym graph: terms with similar meanings
    - Antonym graph: terms with opposite meanings
    - Etymology lineage graph: etymological relationships
    - Doctrine-meaning graph: doctrine to term mappings
    - Concept clusters: groups of semantically related terms
    """

    VERSION = "1.0.0"

    def __init__(self, output_dir: Path | None = None):
        """
        Initialize graph builder.

        Args:
            output_dir: Path to output directory for graph index
        """
        if output_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            output_dir = repo_root / "legal" / "semiotics"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.synonym_graph: dict[str, list[str]] = {}
        self.antonym_graph: dict[str, list[str]] = {}
        self.etymology_graph: dict[str, dict[str, Any]] = {}
        self.doctrine_graph: dict[str, list[str]] = {}
        self.concept_clusters: list[dict[str, Any]] = []

    def build_synonym_graph(self, corpus: dict[str, Any]) -> dict[str, list[str]]:
        """
        Build synonym graph from semiotic corpus.

        Args:
            corpus: Semiotic corpus with term correlations

        Returns:
            Synonym graph as adjacency list
        """
        synonym_graph: dict[str, list[str]] = {}

        terms = corpus.get("terms", {})

        # Extract synonyms from dictionary sources
        for term, term_data in terms.items():
            synonyms: set[str] = set()

            # Get synonyms from each dictionary source
            for source in term_data.get("dictionary_sources", []):
                source_def = source.get("definition", "")

                # Simple heuristic: look for "also known as", "synonym:", etc.
                if "synonym" in source_def.lower():
                    # Extract potential synonyms (simplified)
                    pass

            # Also check related terms from harmonization
            # This would integrate with MSH data
            # For now, placeholder logic

            if synonyms:
                synonym_graph[term] = list(synonyms)

        self.synonym_graph = synonym_graph
        return synonym_graph

    def build_antonym_graph(self, corpus: dict[str, Any]) -> dict[str, list[str]]:
        """
        Build antonym graph from semiotic corpus.

        Args:
            corpus: Semiotic corpus with term correlations

        Returns:
            Antonym graph as adjacency list
        """
        antonym_graph: dict[str, list[str]] = {}

        terms = corpus.get("terms", {})

        # Extract antonyms from dictionary sources
        for term, term_data in terms.items():
            antonyms: set[str] = set()

            # Get antonyms from each dictionary source
            for source in term_data.get("dictionary_sources", []):
                source_def = source.get("definition", "")

                # Simple heuristic: look for "opposite of", "antonym:", etc.
                if "opposite" in source_def.lower() or "antonym" in source_def.lower():
                    # Extract potential antonyms (simplified)
                    pass

            if antonyms:
                antonym_graph[term] = list(antonyms)

        self.antonym_graph = antonym_graph
        return antonym_graph

    def build_etymology_graph(
        self, corpus: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """
        Build etymology lineage graph.

        Creates hierarchical graph showing:
        - Root languages (Latin, Greek, Canon)
        - Derivative terms
        - Semantic evolution paths

        Args:
            corpus: Semiotic corpus with term correlations

        Returns:
            Etymology graph with nodes and edges
        """
        etymology_graph: dict[str, dict[str, Any]] = {}

        terms = corpus.get("terms", {})

        for term, term_data in terms.items():
            etymology_lineage = term_data.get("etymology_lineage", [])

            if etymology_lineage:
                for lineage in etymology_lineage:
                    language = lineage.get("language", "unknown")
                    root = lineage.get("root", "")
                    meaning = lineage.get("meaning", "")
                    era = lineage.get("era", "unknown")

                    # Create node for this etymology entry
                    node_id = f"{language}:{root}"

                    if node_id not in etymology_graph:
                        etymology_graph[node_id] = {
                            "language": language,
                            "root": root,
                            "meaning": meaning,
                            "era": era,
                            "derivatives": [],
                        }

                    # Add term as derivative
                    if term not in etymology_graph[node_id]["derivatives"]:
                        etymology_graph[node_id]["derivatives"].append(term)

        self.etymology_graph = etymology_graph
        return etymology_graph

    def build_doctrine_graph(self, corpus: dict[str, Any]) -> dict[str, list[str]]:
        """
        Build doctrine-meaning graph.

        Maps doctrines to terms they define.

        Args:
            corpus: Semiotic corpus with term correlations

        Returns:
            Doctrine graph mapping doctrine to terms
        """
        doctrine_graph: dict[str, list[str]] = {}

        terms = corpus.get("terms", {})

        for term, term_data in terms.items():
            doctrinal_mappings = term_data.get("doctrinal_mappings", [])

            for mapping in doctrinal_mappings:
                doctrine = mapping.get("doctrine", "")

                if doctrine:
                    if doctrine not in doctrine_graph:
                        doctrine_graph[doctrine] = []

                    if term not in doctrine_graph[doctrine]:
                        doctrine_graph[doctrine].append(term)

        self.doctrine_graph = doctrine_graph
        return doctrine_graph

    def build_concept_clusters(
        self, corpus: dict[str, Any], similarity_threshold: float = 0.6
    ) -> list[dict[str, Any]]:
        """
        Build concept clusters - groups of semantically related terms.

        Uses simple clustering based on:
        - Shared doctrines
        - Shared etymology
        - Shared era definitions

        Args:
            corpus: Semiotic corpus with term correlations
            similarity_threshold: Minimum similarity for clustering

        Returns:
            List of concept clusters
        """
        terms = corpus.get("terms", {})
        term_list = list(terms.keys())

        # Build similarity matrix
        clusters: list[set[str]] = []

        for i, term1 in enumerate(term_list):
            term1_data = terms[term1]

            # Create cluster for this term if not already in one
            in_cluster = False
            for cluster in clusters:
                if term1 in cluster:
                    in_cluster = True
                    break

            if not in_cluster:
                new_cluster = {term1}

                # Find similar terms
                for term2 in term_list[i + 1 :]:
                    term2_data = terms[term2]

                    similarity = self._calculate_term_similarity(term1_data, term2_data)

                    if similarity >= similarity_threshold:
                        new_cluster.add(term2)

                if len(new_cluster) > 1:
                    clusters.append(new_cluster)

        # Convert clusters to structured format
        structured_clusters = []
        for i, cluster in enumerate(clusters):
            cluster_terms = list(cluster)

            # Find common features
            common_doctrines = self._find_common_doctrines(
                [terms[t] for t in cluster_terms]
            )
            common_etymology = self._find_common_etymology(
                [terms[t] for t in cluster_terms]
            )

            structured_clusters.append(
                {
                    "cluster_id": i + 1,
                    "terms": cluster_terms,
                    "size": len(cluster_terms),
                    "common_doctrines": common_doctrines,
                    "common_etymology": common_etymology,
                }
            )

        self.concept_clusters = structured_clusters
        return structured_clusters

    def _calculate_term_similarity(
        self, term1_data: dict[str, Any], term2_data: dict[str, Any]
    ) -> float:
        """
        Calculate similarity between two terms.

        Based on:
        - Shared doctrines
        - Shared etymology language
        - Shared eras

        Returns:
            Similarity score 0.0-1.0
        """
        score = 0.0

        # Shared doctrines (weight 0.4)
        doctrines1 = set(
            m.get("doctrine", "") for m in term1_data.get("doctrinal_mappings", [])
        )
        doctrines2 = set(
            m.get("doctrine", "") for m in term2_data.get("doctrinal_mappings", [])
        )

        if doctrines1 and doctrines2:
            doctrine_intersection = len(doctrines1 & doctrines2)
            doctrine_union = len(doctrines1 | doctrines2)
            if doctrine_union > 0:
                score += (doctrine_intersection / doctrine_union) * 0.4

        # Shared etymology language (weight 0.3)
        etymology1 = set(
            e.get("language", "") for e in term1_data.get("etymology_lineage", [])
        )
        etymology2 = set(
            e.get("language", "") for e in term2_data.get("etymology_lineage", [])
        )

        if etymology1 and etymology2:
            etymology_intersection = len(etymology1 & etymology2)
            etymology_union = len(etymology1 | etymology2)
            if etymology_union > 0:
                score += (etymology_intersection / etymology_union) * 0.3

        # Shared eras (weight 0.3)
        eras1 = set(term1_data.get("era_definitions", {}).keys())
        eras2 = set(term2_data.get("era_definitions", {}).keys())

        if eras1 and eras2:
            era_intersection = len(eras1 & eras2)
            era_union = len(eras1 | eras2)
            if era_union > 0:
                score += (era_intersection / era_union) * 0.3

        return score

    def _find_common_doctrines(self, term_data_list: list[dict[str, Any]]) -> list[str]:
        """Find doctrines common to multiple terms."""
        if not term_data_list:
            return []

        # Get all doctrine sets
        doctrine_sets = [
            set(m.get("doctrine", "") for m in td.get("doctrinal_mappings", []))
            for td in term_data_list
        ]

        # Find intersection
        common = doctrine_sets[0]
        for doctrine_set in doctrine_sets[1:]:
            common = common & doctrine_set

        return list(common)

    def _find_common_etymology(self, term_data_list: list[dict[str, Any]]) -> list[str]:
        """Find etymology languages common to multiple terms."""
        if not term_data_list:
            return []

        # Get all etymology language sets
        etymology_sets = [
            set(e.get("language", "") for e in td.get("etymology_lineage", []))
            for td in term_data_list
        ]

        # Find intersection
        common = etymology_sets[0]
        for etymology_set in etymology_sets[1:]:
            common = common & etymology_set

        return list(common)

    def detect_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        """
        Detect cycles in a directed graph.

        Args:
            graph: Adjacency list representation

        Returns:
            List of cycles found
        """
        cycles = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> bool:
            """DFS helper for cycle detection."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def build_all_graphs(self, corpus: dict[str, Any]) -> dict[str, Any]:
        """
        Build all graph types from corpus.

        Args:
            corpus: Semiotic corpus with term correlations

        Returns:
            Dictionary containing all graphs
        """
        synonym_graph = self.build_synonym_graph(corpus)
        antonym_graph = self.build_antonym_graph(corpus)
        etymology_graph = self.build_etymology_graph(corpus)
        doctrine_graph = self.build_doctrine_graph(corpus)
        concept_clusters = self.build_concept_clusters(corpus)

        # Detect cycles in etymology graph (simplified - treat as directed)
        etymology_cycles = []  # Would need to convert etymology_graph format

        all_graphs = {
            "version": self.VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "synonym_graph": {
                "node_count": len(synonym_graph),
                "edges": synonym_graph,
            },
            "antonym_graph": {
                "node_count": len(antonym_graph),
                "edges": antonym_graph,
            },
            "etymology_graph": {
                "node_count": len(etymology_graph),
                "nodes": etymology_graph,
            },
            "doctrine_graph": {
                "node_count": len(doctrine_graph),
                "edges": doctrine_graph,
            },
            "concept_clusters": {
                "cluster_count": len(concept_clusters),
                "clusters": concept_clusters,
            },
            "cycles": {
                "etymology_cycles": etymology_cycles,
            },
        }

        return all_graphs

    def save_graph_index(self, graphs: dict[str, Any]) -> dict[str, Any]:
        """
        Save graph index to disk.

        Args:
            graphs: Graph structures to save

        Returns:
            Save status report
        """
        output_path = self.output_dir / "SEMIOTIC_GRAPH_INDEX.json"

        try:
            with open(output_path, "w") as f:
                json.dump(graphs, f, indent=2)

            return {
                "success": True,
                "output_path": str(output_path),
                "size_bytes": output_path.stat().st_size,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save graph index: {str(e)}",
            }

    def get_statistics(self) -> dict[str, Any]:
        """Get graph builder statistics."""
        return {
            "version": self.VERSION,
            "synonym_nodes": len(self.synonym_graph),
            "antonym_nodes": len(self.antonym_graph),
            "etymology_nodes": len(self.etymology_graph),
            "doctrine_nodes": len(self.doctrine_graph),
            "concept_clusters": len(self.concept_clusters),
        }
