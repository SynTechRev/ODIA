"""Agent definitions for Phase 5 orchestration.

Each agent represents a specialized subsystem with specific responsibilities:
- IngestionAgent: Materializes documents into structured chunks
- AnalysisAgent: Executes unified pipeline (fiscal, constitutional, surveillance)
- AnomalyAgent: Identifies inconsistencies, contradictions, risk patterns
- SynthesisAgent: Produces summaries, narratives, cross-document findings
- DatabaseAgent: Persists documents, analyses, anomalies
- InterfaceAgent: Prepares responses for external systems

All agents are stateless, deterministic, and maintain full provenance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any


class Agent(ABC):
    """Base class for all Phase 5 agents.

    Agents are stateless, pure functions that operate on inputs
    and produce structured outputs with full provenance tracking.
    """

    def __init__(self, name: str):
        """Initialize agent with name."""
        self.name = name

    @abstractmethod
    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute agent task on inputs and return structured output.

        Args:
            inputs: Input data dictionary

        Returns:
            Structured output with provenance
        """
        pass

    def _create_provenance(self, action: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Create provenance metadata for agent action.

        Args:
            action: Action performed
            inputs: Input data used

        Returns:
            Provenance metadata dictionary
        """
        return {
            "agent": self.name,
            "action": action,
            "timestamp": datetime.now(UTC).isoformat(),
            "input_keys": list(inputs.keys()),
        }


class IngestionAgent(Agent):
    """Ingestion Agent - Materializes documents into structured chunks.

    Responsibilities:
    - Load raw documents from various formats
    - Normalize text and metadata
    - Create structured chunks with overlap
    - Generate document IDs and hashes
    """

    def __init__(self):
        """Initialize Ingestion Agent."""
        super().__init__("IngestionAgent")

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute document ingestion.

        Args:
            inputs: Must contain:
                - document_text (str): Raw document text
                - metadata (dict, optional): Document metadata

        Returns:
            {
                "agent": "IngestionAgent",
                "action": "ingest_document",
                "inputs": {...},
                "outputs": {
                    "document_id": str,
                    "normalized_doc": dict,
                    "chunks": list
                },
                "provenance": {...},
                "confidence": float
            }
        """

        from ..ingest import sha256_text
        from ..normalize import normalize_document

        document_text = inputs.get("document_text", "")
        metadata = inputs.get("metadata", {})

        # Create a raw document structure
        raw_doc = {
            "id": metadata.get("id", f"doc_{hash(document_text) % 10**8}"),
            "title": metadata.get("title", "Untitled Document"),
            "jurisdiction": metadata.get("jurisdiction", "unknown"),
            "source": metadata.get("source", "direct_input"),
            "source_url": metadata.get("source_url"),
            "version_date": metadata.get("version_date"),
            "ingest_timestamp": datetime.now(UTC).isoformat(),
            "checksum": sha256_text(document_text),
            "citations": metadata.get("citations", []),
            "metadata": metadata,
            "text": document_text,
        }

        # Normalize to create chunks
        normalized_doc = normalize_document(raw_doc)

        outputs = {
            "document_id": normalized_doc.get("id", "unknown"),
            "normalized_doc": normalized_doc,
            "chunks": normalized_doc.get("chunks", []),
        }

        return {
            "agent": self.name,
            "action": "ingest_document",
            "inputs": {"metadata": metadata, "text_length": len(document_text)},
            "outputs": outputs,
            "provenance": self._create_provenance("ingest_document", inputs),
            "confidence": 1.0,
        }


class AnalysisAgent(Agent):
    """Analysis Agent - Executes unified pipeline.

    Responsibilities:
    - Run fiscal analysis
    - Run constitutional analysis
    - Run surveillance analysis
    - Compute scalar scores
    - Generate structured findings
    """

    def __init__(self):
        """Initialize Analysis Agent."""
        super().__init__("AnalysisAgent")

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute unified analysis pipeline.

        Args:
            inputs: Must contain:
                - document_text (str): Document text
                - metadata (dict): Document metadata

        Returns:
            {
                "agent": "AnalysisAgent",
                "action": "run_analysis",
                "inputs": {...},
                "outputs": {
                    "findings": {...},
                    "scores": {...},
                    "summary": str
                },
                "provenance": {...},
                "confidence": float
            }
        """
        from ..analysis.pipeline import run_full_analysis

        document_text = inputs.get("document_text", "")
        metadata = inputs.get("metadata", {})

        # Run full analysis
        result = run_full_analysis(document_text, metadata)

        outputs = {
            "findings": result.get("findings", {}),
            "scores": {
                "severity": result.get("severity_score", 0.0),
                "lattice": result.get("lattice_score", 1.0),
                "coherence": result.get("coherence_bonus", 0.0),
            },
            "flags": result.get("flags", []),
            "summary": result.get("summary", ""),
        }

        return {
            "agent": self.name,
            "action": "run_analysis",
            "inputs": {"metadata": metadata, "text_length": len(document_text)},
            "outputs": outputs,
            "provenance": self._create_provenance("run_analysis", inputs),
            "confidence": result.get("lattice_score", 1.0),
        }


class AnomalyAgent(Agent):
    """Anomaly Agent - Identifies inconsistencies and risk patterns.

    Responsibilities:
    - Detect contradictions
    - Identify missing citations
    - Flag structural anomalies
    - Assess risk patterns
    """

    def __init__(self):
        """Initialize Anomaly Agent."""
        super().__init__("AnomalyAgent")

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute anomaly detection.

        Args:
            inputs: Must contain:
                - findings (dict): Analysis findings from AnalysisAgent

        Returns:
            {
                "agent": "AnomalyAgent",
                "action": "detect_anomalies",
                "inputs": {...},
                "outputs": {
                    "anomalies": list,
                    "risk_score": float,
                    "high_priority": list
                },
                "provenance": {...},
                "confidence": float
            }
        """
        findings = inputs.get("findings", {})

        # Aggregate all anomalies from findings
        anomalies = []
        for category in ["fiscal", "constitutional", "surveillance"]:
            anomalies.extend(findings.get(category, []))

        # Compute risk score based on severity
        high_severity_count = sum(1 for a in anomalies if a.get("severity") == "high")
        risk_score = min(1.0, high_severity_count * 0.2)

        # Extract high priority anomalies
        high_priority = [
            f"{a.get('id', 'unknown')}: {a.get('issue', 'Unknown issue')}"
            for a in anomalies
            if a.get("severity") == "high"
        ]

        outputs = {
            "anomalies": anomalies,
            "risk_score": risk_score,
            "high_priority": high_priority,
            "total_count": len(anomalies),
        }

        return {
            "agent": self.name,
            "action": "detect_anomalies",
            "inputs": {"findings_categories": list(findings.keys())},
            "outputs": outputs,
            "provenance": self._create_provenance("detect_anomalies", inputs),
            "confidence": 1.0 - risk_score * 0.3,
        }


class SynthesisAgent(Agent):
    """Synthesis Agent - Produces summaries and cross-document findings.

    Responsibilities:
    - Generate narrative summaries
    - Identify cross-document themes
    - Detect structural divergences
    - Track patterns across documents
    """

    def __init__(self):
        """Initialize Synthesis Agent."""
        super().__init__("SynthesisAgent")

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute synthesis and narrative generation.

        Args:
            inputs: Must contain:
                - analyses (list): List of analysis results
                - mode (str): "single" or "cross_document"

        Returns:
            {
                "agent": "SynthesisAgent",
                "action": "synthesize",
                "inputs": {...},
                "outputs": {
                    "summary": str,
                    "themes": list,
                    "cross_links": list,
                    "recommendations": list
                },
                "provenance": {...},
                "confidence": float
            }
        """
        analyses = inputs.get("analyses", [])
        mode = inputs.get("mode", "single")

        if mode == "single" and len(analyses) == 1:
            # Single document synthesis
            analysis = analyses[0]
            summary = analysis.get("summary", "")
            themes = self._extract_themes(analysis)
        else:
            # Cross-document synthesis
            summary = self._generate_cross_document_summary(analyses)
            themes = self._extract_cross_document_themes(analyses)

        outputs = {
            "summary": summary,
            "themes": themes,
            "cross_links": (
                self._find_cross_links(analyses) if len(analyses) > 1 else []
            ),
            "recommendations": self._generate_recommendations(analyses),
        }

        return {
            "agent": self.name,
            "action": "synthesize",
            "inputs": {"mode": mode, "document_count": len(analyses)},
            "outputs": outputs,
            "provenance": self._create_provenance("synthesize", inputs),
            "confidence": 0.85,
        }

    def _extract_themes(self, analysis: dict[str, Any]) -> list[str]:
        """Extract themes from single analysis."""
        themes = []
        findings = analysis.get("findings", {})

        if findings.get("fiscal"):
            themes.append("fiscal_oversight")
        if findings.get("constitutional"):
            themes.append("constitutional_concerns")
        if findings.get("surveillance"):
            themes.append("surveillance_risks")

        return themes or ["no_significant_themes"]

    def _extract_cross_document_themes(
        self, analyses: list[dict[str, Any]]
    ) -> list[str]:
        """Extract themes across multiple documents."""
        theme_counts: dict[str, int] = {}

        for analysis in analyses:
            themes = self._extract_themes(analysis)
            for theme in themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1

        if len(analyses) == 1:
            # For a single document, return all themes found
            return list(theme_counts.keys())
        # For multiple documents, return themes that appear in more than one document
        return [theme for theme, count in theme_counts.items() if count > 1]

    def _generate_cross_document_summary(self, analyses: list[dict[str, Any]]) -> str:
        """Generate summary across multiple documents."""
        total_anomalies = sum(
            len(a.get("findings", {}).get("fiscal", []))
            + len(a.get("findings", {}).get("constitutional", []))
            + len(a.get("findings", {}).get("surveillance", []))
            for a in analyses
        )

        return (
            f"Cross-document analysis of {len(analyses)} documents "
            f"identified {total_anomalies} total anomalies. "
            f"See detailed findings for theme analysis."
        )

    def _find_cross_links(self, analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find connections between documents."""
        # Simplified cross-linking based on shared themes
        links = []
        themes_by_doc = {i: self._extract_themes(a) for i, a in enumerate(analyses)}

        for i in range(len(analyses)):
            for j in range(i + 1, len(analyses)):
                shared = set(themes_by_doc[i]) & set(themes_by_doc[j])
                if shared:
                    links.append(
                        {
                            "doc1_index": i,
                            "doc2_index": j,
                            "shared_themes": list(shared),
                        }
                    )

        return links

    def _generate_recommendations(self, analyses: list[dict[str, Any]]) -> list[str]:
        """Generate recommendations based on analyses."""
        recommendations = []

        # Check for high severity issues
        has_high_severity = any(
            any(
                f.get("severity") == "high"
                for f in analysis.get("findings", {}).get(category, [])
            )
            for analysis in analyses
            for category in ["fiscal", "constitutional", "surveillance"]
        )

        if has_high_severity:
            recommendations.append(
                "Immediate review of high-severity anomalies required"
            )

        # Check for cross-document patterns
        if len(analyses) > 1:
            themes = self._extract_cross_document_themes(analyses)
            if len(themes) > 2:
                recommendations.append(
                    "Pattern detected across multiple documents; "
                    "recommend systematic review"
                )

        return recommendations or ["No immediate action required"]


class DatabaseAgent(Agent):
    """Database Agent - Persists documents, analyses, and anomalies.

    Responsibilities:
    - Store documents
    - Store analysis results
    - Store anomalies
    - Maintain provenance records
    """

    def __init__(self):
        """Initialize Database Agent."""
        super().__init__("DatabaseAgent")

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute database persistence.

        Args:
            inputs: Must contain:
                - operation (str): "store_document", "store_analysis", etc.
                - data (dict): Data to persist

        Returns:
            {
                "agent": "DatabaseAgent",
                "action": "persist",
                "inputs": {...},
                "outputs": {
                    "status": str,
                    "record_id": str
                },
                "provenance": {...},
                "confidence": float
            }
        """
        operation = inputs.get("operation", "store_document")
        data = inputs.get("data", {})

        # Simulate persistence (actual DB operations would go here)
        record_id = f"{operation}_{hash(str(data)) % 10**8}"

        outputs = {
            "status": "success",
            "operation": operation,
            "record_id": record_id,
        }

        return {
            "agent": self.name,
            "action": "persist",
            "inputs": {"operation": operation, "data_keys": list(data.keys())},
            "outputs": outputs,
            "provenance": self._create_provenance("persist", inputs),
            "confidence": 1.0,
        }


class InterfaceAgent(Agent):
    """Interface Agent - Prepares responses for external systems.

    Responsibilities:
    - Format results for API responses
    - Generate reports
    - Create visualizations
    - Prepare exports
    """

    def __init__(self):
        """Initialize Interface Agent."""
        super().__init__("InterfaceAgent")

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute response preparation.

        Args:
            inputs: Must contain:
                - format (str): "json", "csv", "report"
                - data (dict): Data to format

        Returns:
            {
                "agent": "InterfaceAgent",
                "action": "prepare_response",
                "inputs": {...},
                "outputs": {
                    "formatted_data": Any,
                    "format": str
                },
                "provenance": {...},
                "confidence": float
            }
        """
        format_type = inputs.get("format", "json")
        data = inputs.get("data", {})

        # Format data based on type
        if format_type == "json":
            formatted_data = data
        elif format_type == "csv":
            formatted_data = self._format_as_csv(data)
        else:
            formatted_data = data

        outputs = {
            "formatted_data": formatted_data,
            "format": format_type,
        }

        return {
            "agent": self.name,
            "action": "prepare_response",
            "inputs": {"format": format_type, "data_keys": list(data.keys())},
            "outputs": outputs,
            "provenance": self._create_provenance("prepare_response", inputs),
            "confidence": 1.0,
        }

    def _format_as_csv(self, data: dict[str, Any]) -> str:
        """Format data as CSV string."""
        # Simplified CSV formatting
        lines = ["key,value"]
        for key, value in data.items():
            lines.append(f"{key},{value}")
        return "\n".join(lines)


__all__ = [
    "Agent",
    "IngestionAgent",
    "AnalysisAgent",
    "AnomalyAgent",
    "SynthesisAgent",
    "DatabaseAgent",
    "InterfaceAgent",
]
