"""
Etymology Loader - LGCEP-v1 (Latin, Greek, and Canonical Etymology Pack).

Loads and provides access to etymological roots, semantic lineage, and drift
analysis for legal terms across Latin, Greek, and Canon Law traditions.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class EtymologyLoader:
    """
    Etymology loader for JIM semantic engine.

    Capabilities:
    - Load Latin maxims, Greek roots, Canon law roots
    - Access harmonized etymology matrix
    - Calculate semantic drift scores
    - Trace semantic lineage across eras
    - Integrate with MSH, CLF, and Lexicon systems
    """

    VERSION = "1.0.0"
    SCHEMA_VERSION = "1.0"

    def __init__(self, etymology_dir: Path | None = None):
        """
        Initialize etymology loader.

        Args:
            etymology_dir: Path to legal/etymology directory
        """
        if etymology_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            etymology_dir = repo_root / "legal" / "etymology"
        self.etymology_dir = Path(etymology_dir)

        # Loaded data
        self.latin_maxims: dict[str, Any] = {}
        self.greek_roots: dict[str, Any] = {}
        self.canon_roots: dict[str, Any] = {}
        self.etymology_matrix: dict[str, Any] = {}
        self.index: dict[str, Any] = {}

        # Processed structures
        self.semantic_lineage_map: dict[str, list[str]] = {}
        self.drift_scores: dict[str, float] = {}
        self.doctrine_etymology_map: dict[str, list[str]] = {}

        self.loaded = False

    def load_all_sources(self) -> dict[str, Any]:
        """
        Load all etymology sources.

        Returns:
            Dictionary with:
                - success: bool
                - latin_maxims: int count
                - greek_roots: int count
                - canon_roots: int count
                - matrix_entries: int count
                - total_entries: int
        """
        try:
            # Load Latin maxims
            with open(self.etymology_dir / "latin_maxims.json") as f:
                self.latin_maxims = json.load(f)

            # Load Greek roots
            with open(self.etymology_dir / "greek_roots.json") as f:
                self.greek_roots = json.load(f)

            # Load Canon law roots
            with open(self.etymology_dir / "canon_law_roots.json") as f:
                self.canon_roots = json.load(f)

            # Load etymology matrix
            with open(self.etymology_dir / "ETYMOLOGY_MATRIX.json") as f:
                self.etymology_matrix = json.load(f)

            # Load index
            with open(self.etymology_dir / "ETYMOLOGY_INDEX.json") as f:
                self.index = json.load(f)

            self.loaded = True

            # Build derivative structures
            self._build_semantic_lineage_map()
            self._build_drift_scores()
            self._build_doctrine_etymology_map()

            return {
                "success": True,
                "latin_maxims": self.latin_maxims.get("total_maxims", 0),
                "greek_roots": self.greek_roots.get("total_roots", 0),
                "canon_roots": self.canon_roots.get("total_entries", 0),
                "matrix_entries": self.etymology_matrix.get("total_entries", 0),
                "total_entries": self.index.get("total_entries", 0),
                "version": self.VERSION,
                "schema_version": self.SCHEMA_VERSION,
            }

        except FileNotFoundError as e:
            return {"success": False, "error": f"Etymology file not found: {e}"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}

    def _build_semantic_lineage_map(self) -> None:
        """Build semantic lineage mapping from matrix."""
        if "entries" not in self.etymology_matrix:
            return

        for entry in self.etymology_matrix["entries"]:
            term = entry.get("term", "")
            if term:
                self.semantic_lineage_map[term] = entry.get("semantic_lineage", [])

    def _build_drift_scores(self) -> None:
        """Extract drift scores from matrix."""
        if "entries" not in self.etymology_matrix:
            return

        for entry in self.etymology_matrix["entries"]:
            term = entry.get("term", "")
            if term:
                self.drift_scores[term] = entry.get("drift_score", 0.0)

    def _build_doctrine_etymology_map(self) -> None:
        """Map doctrines to their etymological roots."""
        if "doctrine_mappings" in self.index:
            self.doctrine_etymology_map = self.index["doctrine_mappings"]
        else:
            # Initialize empty map if not present in index
            self.doctrine_etymology_map = {}

    def get_semantic_lineage(self, term: str) -> list[str]:
        """
        Get semantic lineage for a term.

        Args:
            term: English legal term

        Returns:
            List of semantic chains showing evolution
        """
        return self.semantic_lineage_map.get(term.lower(), [])

    def get_drift_score(self, term: str) -> float:
        """
        Get semantic drift score for a term.

        Args:
            term: English legal term

        Returns:
            Drift score (0.0-1.0) or 0.0 if not found
        """
        return self.drift_scores.get(term.lower(), 0.0)

    def get_etymology_for_term(self, term: str) -> dict[str, Any]:
        """
        Get complete etymology information for a term.

        Args:
            term: English legal term

        Returns:
            Dictionary with etymology data or empty dict if not found
        """
        if "entries" not in self.etymology_matrix:
            return {}

        term_lower = term.lower()
        for entry in self.etymology_matrix["entries"]:
            if entry.get("term", "").lower() == term_lower:
                return entry

        return {}

    def get_latin_maxim(self, latin_term: str) -> dict[str, Any]:
        """
        Get Latin maxim by term.

        Args:
            latin_term: Latin term (e.g., "stare decisis")

        Returns:
            Maxim data or empty dict if not found
        """
        if "maxims" not in self.latin_maxims:
            return {}

        for maxim in self.latin_maxims["maxims"]:
            if maxim.get("term", "").lower() == latin_term.lower():
                return maxim

        return {}

    def get_greek_root(self, greek_root: str) -> dict[str, Any]:
        """
        Get Greek root by root name.

        Args:
            greek_root: Greek root (e.g., "dike", "nomos")

        Returns:
            Root data or empty dict if not found
        """
        if "roots" not in self.greek_roots:
            return {}

        for root in self.greek_roots["roots"]:
            if root.get("root", "").lower() == greek_root.lower():
                return root

        return {}

    def get_canon_root(self, canon_term: str) -> dict[str, Any]:
        """
        Get Canon law root by term.

        Args:
            canon_term: Canon law term (e.g., "ius naturale")

        Returns:
            Canon root data or empty dict if not found
        """
        if "entries" not in self.canon_roots:
            return {}

        for entry in self.canon_roots["entries"]:
            if entry.get("term", "").lower() == canon_term.lower():
                return entry

        return {}

    def get_doctrine_etymology(self, doctrine: str) -> list[str]:
        """
        Get etymological roots for a legal doctrine.

        Args:
            doctrine: Legal doctrine name

        Returns:
            List of etymological root terms
        """
        return self.doctrine_etymology_map.get(doctrine, [])

    def calculate_semantic_stability(self, term: str) -> dict[str, Any]:
        """
        Calculate semantic stability metrics for a term.

        Args:
            term: English legal term

        Returns:
            Dictionary with:
                - drift_score: float
                - stability_rating: str (stable/moderate/significant_drift)
                - era_meanings: dict
        """
        etymology = self.get_etymology_for_term(term)
        if not etymology:
            return {
                "drift_score": 0.0,
                "stability_rating": "unknown",
                "era_meanings": {},
            }

        drift_score = etymology.get("drift_score", 0.0)

        if drift_score < 0.3:
            rating = "stable"
        elif drift_score < 0.5:
            rating = "moderate_drift"
        else:
            rating = "significant_drift"

        return {
            "drift_score": drift_score,
            "stability_rating": rating,
            "era_meanings": etymology.get("era_meanings", {}),
            "semantic_lineage": etymology.get("semantic_lineage", []),
        }

    def detect_meaning_divergence(
        self, term: str, source_era: str, target_era: str
    ) -> dict[str, Any]:
        """
        Detect meaning divergence between two eras.

        Args:
            term: English legal term
            source_era: Source era (e.g., "roman_law")
            target_era: Target era (e.g., "modern")

        Returns:
            Dictionary with:
                - has_divergence: bool
                - source_meaning: str
                - target_meaning: str
                - drift_score: float
        """
        etymology = self.get_etymology_for_term(term)
        if not etymology:
            return {
                "has_divergence": False,
                "source_meaning": "",
                "target_meaning": "",
                "drift_score": 0.0,
            }

        era_meanings = etymology.get("era_meanings", {})
        source_meaning = era_meanings.get(source_era, "")
        target_meaning = era_meanings.get(target_era, "")

        has_divergence = (
            source_meaning != target_meaning and source_meaning and target_meaning
        )

        return {
            "has_divergence": has_divergence,
            "source_meaning": source_meaning,
            "target_meaning": target_meaning,
            "drift_score": etymology.get("drift_score", 0.0),
        }

    def trace_concept_evolution(self, concept: str) -> list[dict[str, Any]]:
        """
        Trace the evolution of a concept across eras.

        Args:
            concept: Legal concept (e.g., "justice", "law", "liberty")

        Returns:
            List of era meanings with timestamps
        """
        etymology = self.get_etymology_for_term(concept)
        if not etymology:
            return []

        era_meanings = etymology.get("era_meanings", {})

        # Define era ordering
        era_order = [
            "classical_greek",
            "roman_law",
            "medieval_canon",
            "enlightenment",
            "modern",
        ]

        evolution = []
        for era in era_order:
            if era in era_meanings:
                evolution.append({"era": era, "meaning": era_meanings[era]})

        return evolution

    def get_cross_references(self, term: str) -> list[str]:
        """
        Get cross-references for a term.

        Args:
            term: English legal term

        Returns:
            List of related terms in different languages/traditions
        """
        if "cross_references" not in self.index:
            return []

        return self.index["cross_references"].get(term, [])

    def validate_schema(self) -> dict[str, Any]:
        """
        Validate schema of all loaded files.

        Returns:
            Dictionary with validation results
        """
        if not self.loaded:
            return {"valid": False, "error": "Sources not loaded"}

        errors = []

        # Validate Latin maxims
        if "maxims" not in self.latin_maxims:
            errors.append("latin_maxims: missing 'maxims' key")

        # Validate Greek roots
        if "roots" not in self.greek_roots:
            errors.append("greek_roots: missing 'roots' key")

        # Validate Canon roots
        if "entries" not in self.canon_roots:
            errors.append("canon_roots: missing 'entries' key")

        # Validate etymology matrix
        if "entries" not in self.etymology_matrix:
            errors.append("etymology_matrix: missing 'entries' key")

        # Validate index
        if "sources" not in self.index:
            errors.append("index: missing 'sources' key")

        return {"valid": len(errors) == 0, "errors": errors}

    def generate_etymology_report(self) -> dict[str, Any]:
        """
        Generate comprehensive etymology report.

        Returns:
            Dictionary with statistics and summary
        """
        if not self.loaded:
            return {"error": "Sources not loaded"}

        return {
            "version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "statistics": {
                "latin_maxims": len(self.latin_maxims.get("maxims", [])),
                "greek_roots": len(self.greek_roots.get("roots", [])),
                "canon_roots": len(self.canon_roots.get("entries", [])),
                "matrix_entries": len(self.etymology_matrix.get("entries", [])),
                "total_entries": self.index.get("total_entries", 0),
                "semantic_lineage_mappings": len(self.semantic_lineage_map),
                "drift_scores_tracked": len(self.drift_scores),
                "doctrines_mapped": len(self.doctrine_etymology_map),
            },
            "drift_analysis": {
                "stable_terms": sum(
                    1 for score in self.drift_scores.values() if score < 0.3
                ),
                "moderate_drift": sum(
                    1 for score in self.drift_scores.values() if 0.3 <= score < 0.5
                ),
                "significant_drift": sum(
                    1 for score in self.drift_scores.values() if score >= 0.5
                ),
            },
            "integration_points": {
                "msh_compatible": True,
                "clf_compatible": True,
                "lexicon_compatible": True,
            },
        }
