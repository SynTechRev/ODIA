"""
CDSCE Semiotic Anomaly Detector.

Detects and classifies semiotic anomalies across dictionaries, doctrines,
and eras. Produces structured anomaly flags with severity scoring.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class CDSCEAnomalyDetector:
    """
    Semiotic Anomaly Detector for CDSCE.

    Detects and classifies:
    - Contradiction: Two dictionaries define a term incompatibly
    - Semantic drift spike: Modern use diverges sharply from classical
    - Doctrine meaning inversion: Doctrine meaning reversed over time
    - Interpretive instability: Courts use same word inconsistently
    - Cross-dictionary conflict: Competing roots or philosophical origins
    - Etymology divergence: Modern meaning lost connection to roots
    """

    VERSION = "1.0.0"

    # Anomaly types with base severity scores
    ANOMALY_TYPES = {
        "contradiction": {
            "severity": 0.8,
            "description": "Two dictionaries define a term incompatibly",
        },
        "semantic_drift_spike": {
            "severity": 0.7,
            "description": (
                "Modern use diverges sharply from classical/etymological meaning"
            ),
        },
        "doctrine_meaning_inversion": {
            "severity": 0.9,
            "description": "A doctrine's meaning has reversed over time",
        },
        "interpretive_instability": {
            "severity": 0.6,
            "description": "Courts use the same word inconsistently across eras",
        },
        "cross_dictionary_conflict": {
            "severity": 0.75,
            "description": (
                "Term appears in two sources with competing roots or "
                "philosophical origin"
            ),
        },
        "etymology_divergence": {
            "severity": 0.65,
            "description": "Modern meaning has lost connection to etymological roots",
        },
    }

    def __init__(self, output_dir: Path | None = None):
        """
        Initialize anomaly detector.

        Args:
            output_dir: Path to output directory for anomaly index
        """
        if output_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            output_dir = repo_root / "legal" / "semiotics"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.anomalies: list[dict[str, Any]] = []
        self.anomaly_index: dict[str, list[dict[str, Any]]] = {}

    def detect_contradiction(
        self,
        term: str,
        source1: dict[str, Any],
        source2: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect contradiction between two dictionary sources.

        Args:
            term: Legal term being analyzed
            source1: First dictionary source with definition
            source2: Second dictionary source with definition

        Returns:
            Anomaly dict if contradiction detected, None otherwise
        """
        def1 = source1.get("definition", "")
        def2 = source2.get("definition", "")

        if not def1 or not def2:
            return None

        # Calculate semantic similarity
        similarity = self._calculate_semantic_similarity(def1, def2)

        # If similarity is very low, likely a contradiction
        if similarity < 0.3:
            severity = 0.8 + (0.3 - similarity) * 0.5  # Scale from 0.8 to 0.95

            return {
                "type": "contradiction",
                "term": term,
                "sources_involved": [source1.get("source"), source2.get("source")],
                "severity": round(min(severity, 1.0), 3),
                "details": {
                    "source1_definition": def1[:200],
                    "source2_definition": def2[:200],
                    "similarity_score": round(similarity, 3),
                },
                "notes": (
                    f"{source1.get('source')} and {source2.get('source')} "
                    f"provide incompatible definitions with "
                    f"{round(similarity * 100)}% similarity"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return None

    def detect_drift_spike(
        self,
        term: str,
        drift_analysis: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect semantic drift spike from drift analysis.

        Args:
            term: Legal term being analyzed
            drift_analysis: Drift analysis from CDSCEDriftAnalyzer

        Returns:
            Anomaly dict if drift spike detected, None otherwise
        """
        if not drift_analysis.get("has_drift_spike"):
            return None

        spikes = drift_analysis.get("spikes", [])
        if not spikes:
            return None

        # Use highest drift score from spikes
        max_spike = max(spikes, key=lambda s: s.get("drift_score", 0))

        return {
            "type": "semantic_drift_spike",
            "term": term,
            "sources_involved": ["etymology", "modern_usage"],
            "severity": round(max_spike.get("drift_score", 0.7), 3),
            "details": {
                "from_era": max_spike.get("from_era"),
                "to_era": max_spike.get("to_era"),
                "drift_score": max_spike.get("drift_score"),
                "spike_count": len(spikes),
            },
            "notes": (
                f"Term underwent significant semantic shift from "
                f"{max_spike.get('from_era')} to {max_spike.get('to_era')} "
                f"with drift score of {max_spike.get('drift_score')}"
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def detect_doctrine_inversion(
        self,
        term: str,
        doctrine: str,
        original_meaning: str,
        modern_meaning: str,
        inversion_analysis: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect doctrine meaning inversion.

        Args:
            term: Legal term
            doctrine: Doctrine name
            original_meaning: Original doctrine interpretation
            modern_meaning: Modern doctrine interpretation
            inversion_analysis: Result from drift analyzer inversion detection

        Returns:
            Anomaly dict if inversion detected, None otherwise
        """
        if not inversion_analysis.get("is_inversion"):
            return None

        return {
            "type": "doctrine_meaning_inversion",
            "term": term,
            "sources_involved": ["doctrine", doctrine],
            "severity": 0.9,
            "details": {
                "doctrine": doctrine,
                "drift_score": inversion_analysis.get("drift_score"),
                "confidence": inversion_analysis.get("confidence"),
                "indicators": inversion_analysis.get("inversion_indicators_found", []),
            },
            "notes": (
                f"Doctrine '{doctrine}' meaning for term '{term}' has inverted "
                f"with {inversion_analysis.get('confidence') * 100:.0f}% confidence"
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def detect_interpretive_instability(
        self,
        term: str,
        instability_analysis: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect interpretive instability across cases.

        Args:
            term: Legal term
            instability_analysis: Result from drift analyzer instability detection

        Returns:
            Anomaly dict if instability detected, None otherwise
        """
        if not instability_analysis.get("is_unstable"):
            return None

        return {
            "type": "interpretive_instability",
            "term": term,
            "sources_involved": ["case_law"],
            "severity": round(instability_analysis.get("instability_score", 0.6), 3),
            "details": {
                "instability_score": instability_analysis.get("instability_score"),
                "variation_count": instability_analysis.get("variation_count"),
                "pairwise_comparisons": instability_analysis.get(
                    "pairwise_comparisons"
                ),
            },
            "notes": (
                f"Term '{term}' shows interpretive instability across "
                f"{instability_analysis.get('variation_count')} cases with "
                f"instability score of {instability_analysis.get('instability_score')}"
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def detect_cross_dictionary_conflict(
        self,
        term: str,
        etymology_sources: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Detect conflicts between etymological sources.

        Args:
            term: Legal term
            etymology_sources: List of etymology lineage entries

        Returns:
            Anomaly dict if conflict detected, None otherwise
        """
        if len(etymology_sources) < 2:
            return None

        # Check for conflicting language origins
        languages = set(source.get("language", "") for source in etymology_sources)

        # Multiple distinct language origins might indicate conflict
        if len(languages) >= 2:
            # Check if meanings are similar
            meanings = [source.get("meaning", "") for source in etymology_sources]
            if len(meanings) >= 2:
                similarity = self._calculate_semantic_similarity(
                    meanings[0], meanings[1]
                )

                if similarity < 0.4:
                    return {
                        "type": "cross_dictionary_conflict",
                        "term": term,
                        "sources_involved": list(languages),
                        "severity": 0.75,
                        "details": {
                            "conflicting_languages": list(languages),
                            "etymology_sources": [
                                {
                                    "language": s.get("language"),
                                    "root": s.get("root"),
                                    "meaning": s.get("meaning", "")[:100],
                                }
                                for s in etymology_sources
                            ],
                            "similarity_score": round(similarity, 3),
                        },
                        "notes": (
                            f"Term '{term}' has conflicting etymological origins in "
                            f"{', '.join(languages)} with low semantic similarity"
                        ),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

        return None

    def detect_etymology_divergence(
        self,
        term: str,
        etymology_root: str,
        etymology_meaning: str,
        modern_definition: str,
    ) -> dict[str, Any] | None:
        """
        Detect divergence from etymological roots.

        Args:
            term: Legal term
            etymology_root: Etymological root
            etymology_meaning: Original etymological meaning
            modern_definition: Modern dictionary definition

        Returns:
            Anomaly dict if divergence detected, None otherwise
        """
        if not etymology_meaning or not modern_definition:
            return None

        # Calculate semantic distance
        similarity = self._calculate_semantic_similarity(
            etymology_meaning, modern_definition
        )

        # Significant divergence if similarity < 0.35
        if similarity < 0.35:
            severity = 0.65 + (0.35 - similarity) * 0.6

            return {
                "type": "etymology_divergence",
                "term": term,
                "sources_involved": ["etymology", "modern_dictionary"],
                "severity": round(min(severity, 1.0), 3),
                "details": {
                    "etymology_root": etymology_root,
                    "etymology_meaning": etymology_meaning[:200],
                    "modern_definition": modern_definition[:200],
                    "similarity_score": round(similarity, 3),
                },
                "notes": (
                    f"Modern definition of '{term}' has diverged significantly "
                    f"from etymological root '{etymology_root}' "
                    f"({round(similarity * 100)}% similarity)"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return None

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Uses Jaccard similarity on word sets.

        Returns:
            Similarity score from 0.0 (completely different) to 1.0 (identical)
        """
        if not text1 or not text2:
            return 0.0

        # Tokenize and normalize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Remove common stopwords
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "that",
            "which",
        }
        words1 = words1 - stopwords
        words2 = words2 - stopwords

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 0.0

        return intersection / union

    def scan_term_for_anomalies(
        self,
        term: str,
        correlation_data: dict[str, Any],
        drift_analysis: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Scan a term's correlation data for all anomaly types.

        Args:
            term: Legal term
            correlation_data: Full correlation data from CDSCE engine
            drift_analysis: Optional drift analysis results

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Check for contradictions between dictionary sources
        sources = correlation_data.get("dictionary_sources", [])
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                anomaly = self.detect_contradiction(term, sources[i], sources[j])
                if anomaly:
                    anomalies.append(anomaly)

        # Check for drift spike
        if drift_analysis:
            spike_anomaly = self.detect_drift_spike(term, drift_analysis)
            if spike_anomaly:
                anomalies.append(spike_anomaly)

        # Check for cross-dictionary conflict
        etymology_lineage = correlation_data.get("etymology_lineage", [])
        conflict_anomaly = self.detect_cross_dictionary_conflict(
            term, etymology_lineage
        )
        if conflict_anomaly:
            anomalies.append(conflict_anomaly)

        # Check for etymology divergence
        if etymology_lineage and sources:
            etymology_entry = etymology_lineage[0]
            modern_source = sources[0]

            divergence_anomaly = self.detect_etymology_divergence(
                term,
                etymology_entry.get("root", ""),
                etymology_entry.get("meaning", ""),
                modern_source.get("definition", ""),
            )
            if divergence_anomaly:
                anomalies.append(divergence_anomaly)

        return anomalies

    def build_anomaly_index(self, anomalies: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Build structured anomaly index from anomaly list.

        Args:
            anomalies: List of detected anomalies

        Returns:
            Structured anomaly index
        """
        # Group by term
        by_term: dict[str, list[dict[str, Any]]] = {}
        for anomaly in anomalies:
            term = anomaly.get("term", "unknown")
            if term not in by_term:
                by_term[term] = []
            by_term[term].append(anomaly)

        # Group by type
        by_type: dict[str, list[dict[str, Any]]] = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "unknown")
            if anomaly_type not in by_type:
                by_type[anomaly_type] = []
            by_type[anomaly_type].append(anomaly)

        # Calculate statistics
        severity_scores = [a.get("severity", 0) for a in anomalies]
        avg_severity = (
            sum(severity_scores) / len(severity_scores) if severity_scores else 0
        )

        self.anomaly_index = {
            "version": self.VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "total_anomalies": len(anomalies),
            "by_term": by_term,
            "by_type": by_type,
            "statistics": {
                "total_anomalies": len(anomalies),
                "unique_terms": len(by_term),
                "anomaly_types": len(by_type),
                "average_severity": round(avg_severity, 3),
                "high_severity_count": len(
                    [a for a in anomalies if a.get("severity", 0) >= 0.8]
                ),
            },
        }

        return self.anomaly_index

    def save_anomaly_index(self) -> dict[str, Any]:
        """
        Save anomaly index to disk.

        Returns:
            Save status report
        """
        output_path = self.output_dir / "SEMIOTIC_ANOMALY_INDEX.json"

        try:
            with open(output_path, "w") as f:
                json.dump(self.anomaly_index, f, indent=2)

            return {
                "success": True,
                "output_path": str(output_path),
                "size_bytes": output_path.stat().st_size,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save anomaly index: {str(e)}",
            }

    def get_statistics(self) -> dict[str, Any]:
        """Get anomaly detector statistics."""
        return {
            "version": self.VERSION,
            "total_anomalies": len(self.anomalies),
            "anomaly_index_size": len(self.anomaly_index),
        }
