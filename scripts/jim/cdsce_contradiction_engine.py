"""
CDSCE Contradiction Detection Engine.

Detects and classifies contradictions across:
- Lexical contradictions (word-level)
- Doctrinal contradictions (legal doctrine level)
- Interpretive contradictions (constitutional interpretation)
- Temporal contradictions (meaning shifts over time)
- Constitutional framework contradictions (CLF conflicts)
- Etymological contradictions (root origin conflicts)
"""

from datetime import UTC, datetime
from typing import Any


class CDSCEContradictionEngine:
    """
    Contradiction Detection Engine for CDSCE.

    Detects and classifies six types of contradictions:
    1. Lexical: Dictionary definitions conflict
    2. Doctrinal: Legal doctrine interpretations conflict
    3. Interpretive: Constitutional interpretation methods conflict
    4. Temporal: Meaning changed incompatibly over time
    5. Constitutional Framework: CLF frameworks provide conflicting guidance
    6. Etymological: Root origins suggest conflicting meanings
    """

    VERSION = "1.0.0"

    # Contradiction types with severity weights
    CONTRADICTION_TYPES = {
        "lexical": {
            "weight": 0.7,
            "description": "Dictionary definitions conflict at word level",
        },
        "doctrinal": {
            "weight": 0.9,
            "description": "Legal doctrine interpretations conflict",
        },
        "interpretive": {
            "weight": 0.85,
            "description": "Constitutional interpretation methods conflict",
        },
        "temporal": {
            "weight": 0.75,
            "description": "Meaning changed incompatibly over time",
        },
        "constitutional_framework": {
            "weight": 0.8,
            "description": "CLF frameworks provide conflicting guidance",
        },
        "etymological": {
            "weight": 0.65,
            "description": "Root origins suggest conflicting meanings",
        },
    }

    def __init__(self):
        """Initialize contradiction engine."""
        self.contradictions: list[dict[str, Any]] = []

    def detect_lexical_contradiction(
        self,
        term: str,
        source1: dict[str, Any],
        source2: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect lexical contradiction between two dictionary sources.

        Args:
            term: Legal term
            source1: First dictionary source
            source2: Second dictionary source

        Returns:
            Contradiction dict if detected, None otherwise
        """
        def1 = source1.get("definition", "")
        def2 = source2.get("definition", "")

        if not def1 or not def2:
            return None

        # Calculate semantic similarity
        similarity = self._calculate_semantic_similarity(def1, def2)

        # Check for explicit contradiction markers
        contradiction_markers = [
            "not",
            "contrary to",
            "opposite of",
            "differs from",
            "contradicts",
            "incompatible with",
        ]

        has_marker = any(marker in def2.lower() for marker in contradiction_markers)

        # Determine if contradiction exists
        if similarity < 0.25 or has_marker:
            severity = self._calculate_severity(similarity, has_marker)

            return {
                "term": term,
                "conflict_type": "lexical",
                "sources_involved": [
                    source1.get("source", "unknown"),
                    source2.get("source", "unknown"),
                ],
                "severity": severity,
                "details": {
                    "source1": {
                        "name": source1.get("source"),
                        "definition": def1[:200],
                        "year": source1.get("year"),
                    },
                    "source2": {
                        "name": source2.get("source"),
                        "definition": def2[:200],
                        "year": source2.get("year"),
                    },
                    "similarity_score": round(similarity, 3),
                    "has_contradiction_marker": has_marker,
                },
                "notes": (
                    f"{source1.get('source')} and {source2.get('source')} define "
                    f"'{term}' incompatibly; semantic similarity is only "
                    f"{round(similarity * 100)}%"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return None

    def detect_doctrinal_contradiction(
        self,
        term: str,
        doctrine1: dict[str, Any],
        doctrine2: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect doctrinal contradiction between doctrine interpretations.

        Args:
            term: Legal term
            doctrine1: First doctrine interpretation
            doctrine2: Second doctrine interpretation

        Returns:
            Contradiction dict if detected, None otherwise
        """
        doctrine1_name = doctrine1.get("doctrine", "")
        doctrine2_name = doctrine2.get("doctrine", "")

        if not doctrine1_name or not doctrine2_name:
            return None

        # Check if doctrines are inherently conflicting
        conflicting_pairs = [
            ("strict_scrutiny", "rational_basis"),
            ("originalism", "living_constitution"),
            ("textualism", "purposivism"),
        ]

        is_conflicting = any(
            (doctrine1_name in pair and doctrine2_name in pair)
            for pair in conflicting_pairs
        )

        if is_conflicting:
            return {
                "term": term,
                "conflict_type": "doctrinal",
                "sources_involved": [doctrine1_name, doctrine2_name],
                "severity": 0.85,
                "details": {
                    "doctrine1": doctrine1_name,
                    "doctrine2": doctrine2_name,
                    "related_cases1": doctrine1.get("related_cases", [])[:3],
                    "related_cases2": doctrine2.get("related_cases", [])[:3],
                },
                "notes": (
                    f"Doctrines '{doctrine1_name}' and '{doctrine2_name}' provide "
                    f"conflicting interpretations of '{term}'"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return None

    def detect_interpretive_contradiction(
        self,
        term: str,
        framework1: dict[str, Any],
        framework2: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect interpretive contradiction between constitutional frameworks.

        Args:
            term: Legal term
            framework1: First CLF framework
            framework2: Second CLF framework

        Returns:
            Contradiction dict if detected, None otherwise
        """
        framework1_name = framework1.get("framework", "")
        framework2_name = framework2.get("framework", "")

        if not framework1_name or not framework2_name:
            return None

        # Known conflicting framework pairs
        conflicting_frameworks = [
            ("originalism", "living_constitutionalism"),
            ("textualism", "purposivism"),
            ("strict_construction", "loose_construction"),
            ("framers_intent", "contemporary_interpretation"),
        ]

        is_conflicting = any(
            (framework1_name in pair and framework2_name in pair)
            for pair in conflicting_frameworks
        )

        if is_conflicting:
            return {
                "term": term,
                "conflict_type": "interpretive",
                "sources_involved": [framework1_name, framework2_name],
                "severity": 0.8,
                "details": {
                    "framework1": {
                        "name": framework1_name,
                        "era": framework1.get("era", ""),
                        "weight": framework1.get("weight", 0.0),
                    },
                    "framework2": {
                        "name": framework2_name,
                        "era": framework2.get("era", ""),
                        "weight": framework2.get("weight", 0.0),
                    },
                },
                "notes": (
                    f"Constitutional frameworks '{framework1_name}' and "
                    f"'{framework2_name}' provide conflicting interpretations "
                    f"of '{term}'"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return None

    def detect_temporal_contradiction(
        self,
        term: str,
        era1: int,
        era1_definition: str,
        era2: int,
        era2_definition: str,
    ) -> dict[str, Any] | None:
        """
        Detect temporal contradiction - meaning changed incompatibly over time.

        Args:
            term: Legal term
            era1: First era (year)
            era1_definition: Definition in first era
            era2: Second era (year)
            era2_definition: Definition in second era

        Returns:
            Contradiction dict if detected, None otherwise
        """
        if not era1_definition or not era2_definition:
            return None

        # Calculate semantic drift
        similarity = self._calculate_semantic_similarity(
            era1_definition, era2_definition
        )

        # Temporal contradiction if meaning has significantly changed
        if similarity < 0.3:
            return {
                "term": term,
                "conflict_type": "temporal",
                "sources_involved": [f"era_{era1}", f"era_{era2}"],
                "severity": round(0.75 + (0.3 - similarity) * 0.5, 3),
                "details": {
                    "era1": {
                        "year": era1,
                        "definition": era1_definition[:200],
                    },
                    "era2": {
                        "year": era2,
                        "definition": era2_definition[:200],
                    },
                    "similarity_score": round(similarity, 3),
                    "time_span_years": era2 - era1,
                },
                "notes": (
                    f"Definition of '{term}' changed incompatibly from {era1} to "
                    f"{era2} (similarity: {round(similarity * 100)}%)"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return None

    def detect_constitutional_framework_contradiction(
        self,
        term: str,
        frameworks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Detect contradictions among multiple constitutional frameworks.

        Args:
            term: Legal term
            frameworks: List of CLF frameworks mentioning the term

        Returns:
            List of detected contradictions
        """
        contradictions = []

        # Check all pairs
        for i in range(len(frameworks)):
            for j in range(i + 1, len(frameworks)):
                contradiction = self.detect_interpretive_contradiction(
                    term, frameworks[i], frameworks[j]
                )
                if contradiction:
                    contradictions.append(contradiction)

        return contradictions

    def detect_etymological_contradiction(
        self,
        term: str,
        etymology1: dict[str, Any],
        etymology2: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Detect etymological contradiction - root origins suggest conflicting meanings.

        Args:
            term: Legal term
            etymology1: First etymology entry
            etymology2: Second etymology entry

        Returns:
            Contradiction dict if detected, None otherwise
        """
        lang1 = etymology1.get("language", "")
        lang2 = etymology2.get("language", "")
        meaning1 = etymology1.get("meaning", "")
        meaning2 = etymology2.get("meaning", "")

        if not meaning1 or not meaning2:
            return None

        # Calculate semantic similarity between etymological meanings
        similarity = self._calculate_semantic_similarity(meaning1, meaning2)

        # Contradiction if different language origins with different meanings
        if lang1 != lang2 and similarity < 0.35:
            return {
                "term": term,
                "conflict_type": "etymological",
                "sources_involved": [lang1, lang2],
                "severity": 0.7,
                "details": {
                    "etymology1": {
                        "language": lang1,
                        "root": etymology1.get("root", ""),
                        "meaning": meaning1[:200],
                        "era": etymology1.get("era", ""),
                    },
                    "etymology2": {
                        "language": lang2,
                        "root": etymology2.get("root", ""),
                        "meaning": meaning2[:200],
                        "era": etymology2.get("era", ""),
                    },
                    "similarity_score": round(similarity, 3),
                },
                "notes": (
                    f"Etymological origins of '{term}' conflict: {lang1} vs {lang2} "
                    f"roots suggest different meanings "
                    f"({round(similarity * 100)}% similarity)"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

        return None

    def _scan_lexical_contradictions(
        self, term: str, sources: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Scan for lexical contradictions between dictionary sources."""
        contradictions = []
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                contradiction = self.detect_lexical_contradiction(
                    term, sources[i], sources[j]
                )
                if contradiction:
                    contradictions.append(contradiction)
        return contradictions

    def _scan_doctrinal_contradictions(
        self, term: str, doctrinal_mappings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Scan for doctrinal contradictions."""
        contradictions = []
        for i in range(len(doctrinal_mappings)):
            for j in range(i + 1, len(doctrinal_mappings)):
                contradiction = self.detect_doctrinal_contradiction(
                    term, doctrinal_mappings[i], doctrinal_mappings[j]
                )
                if contradiction:
                    contradictions.append(contradiction)
        return contradictions

    def _scan_temporal_contradictions(
        self, term: str, era_definitions: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Scan for temporal contradictions across eras."""
        contradictions = []
        eras = sorted(int(e) for e in era_definitions.keys())
        for i in range(len(eras) - 1):
            era1 = eras[i]
            era2 = eras[i + 1]
            contradiction = self.detect_temporal_contradiction(
                term,
                era1,
                era_definitions[str(era1)].get("definition", ""),
                era2,
                era_definitions[str(era2)].get("definition", ""),
            )
            if contradiction:
                contradictions.append(contradiction)
        return contradictions

    def _scan_etymological_contradictions(
        self, term: str, etymology_lineage: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Scan for etymological contradictions."""
        contradictions = []
        for i in range(len(etymology_lineage)):
            for j in range(i + 1, len(etymology_lineage)):
                contradiction = self.detect_etymological_contradiction(
                    term, etymology_lineage[i], etymology_lineage[j]
                )
                if contradiction:
                    contradictions.append(contradiction)
        return contradictions

    def scan_term_contradictions(
        self, term: str, correlation_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Scan a term for all types of contradictions.

        Args:
            term: Legal term
            correlation_data: Full correlation data from CDSCE engine

        Returns:
            List of detected contradictions
        """
        contradictions = []

        # 1. Lexical contradictions
        sources = correlation_data.get("dictionary_sources", [])
        contradictions.extend(self._scan_lexical_contradictions(term, sources))

        # 2. Doctrinal contradictions
        doctrinal_mappings = correlation_data.get("doctrinal_mappings", [])
        contradictions.extend(
            self._scan_doctrinal_contradictions(term, doctrinal_mappings)
        )

        # 3. Interpretive contradictions
        frameworks = correlation_data.get("framework_context", [])
        framework_contradictions = self.detect_constitutional_framework_contradiction(
            term, frameworks
        )
        contradictions.extend(framework_contradictions)

        # 4. Temporal contradictions
        era_definitions = correlation_data.get("era_definitions", {})
        contradictions.extend(self._scan_temporal_contradictions(term, era_definitions))

        # 5. Etymological contradictions
        etymology_lineage = correlation_data.get("etymology_lineage", [])
        contradictions.extend(
            self._scan_etymological_contradictions(term, etymology_lineage)
        )

        return contradictions

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

    def _calculate_severity(self, similarity: float, has_marker: bool) -> float:
        """Calculate contradiction severity score (0.0-1.0)."""
        base_severity = 0.7

        # Lower similarity = higher severity
        similarity_factor = (1.0 - similarity) * 0.2

        # Explicit markers increase severity
        marker_factor = 0.1 if has_marker else 0.0

        severity = base_severity + similarity_factor + marker_factor

        return round(min(severity, 1.0), 3)

    def generate_contradiction_report(
        self, contradictions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Generate comprehensive contradiction report.

        Args:
            contradictions: List of detected contradictions

        Returns:
            Structured contradiction report
        """
        # Group by type
        by_type: dict[str, list[dict[str, Any]]] = {}
        for contradiction in contradictions:
            conflict_type = contradiction.get("conflict_type", "unknown")
            if conflict_type not in by_type:
                by_type[conflict_type] = []
            by_type[conflict_type].append(contradiction)

        # Group by severity
        high_severity = [c for c in contradictions if c.get("severity", 0) >= 0.8]
        medium_severity = [
            c for c in contradictions if 0.5 <= c.get("severity", 0) < 0.8
        ]
        low_severity = [c for c in contradictions if c.get("severity", 0) < 0.5]

        # Calculate statistics
        severity_scores = [c.get("severity", 0) for c in contradictions]
        avg_severity = (
            sum(severity_scores) / len(severity_scores) if severity_scores else 0
        )

        return {
            "version": self.VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "total_contradictions": len(contradictions),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_severity": {
                "high": len(high_severity),
                "medium": len(medium_severity),
                "low": len(low_severity),
            },
            "statistics": {
                "average_severity": round(avg_severity, 3),
                "max_severity": max(severity_scores) if severity_scores else 0,
                "min_severity": min(severity_scores) if severity_scores else 0,
            },
            "contradictions": contradictions,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get contradiction engine statistics."""
        return {
            "version": self.VERSION,
            "total_contradictions": len(self.contradictions),
        }
