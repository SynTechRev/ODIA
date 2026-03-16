"""Multi-jurisdiction analysis runner.

Runs the full analysis pipeline against multiple jurisdictions and collects
results tagged by jurisdiction ID, enabling cross-jurisdiction comparison.
"""

from __future__ import annotations

import logging
from typing import Any

from oraculus_di_auditor.analysis.pipeline import run_full_analysis
from oraculus_di_auditor.multi_jurisdiction.registry import JurisdictionRegistry

logger = logging.getLogger(__name__)

_SEVERITY_LEVELS = ("critical", "high", "medium", "low")


def _build_anomaly_summary(
    doc_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate anomaly counts across a list of per-document analysis results."""
    total = 0
    by_severity: dict[str, int] = {s: 0 for s in _SEVERITY_LEVELS}
    by_detector: dict[str, int] = {}

    for result in doc_results:
        findings = result.get("findings", {})
        for detector_name, anomalies in findings.items():
            count = len(anomalies)
            by_detector[detector_name] = by_detector.get(detector_name, 0) + count
            total += count
            for anomaly in anomalies:
                sev = anomaly.get("severity", "medium")
                if sev in by_severity:
                    by_severity[sev] += 1
                else:
                    # Unknown severity bucket — count under medium
                    by_severity["medium"] += 1

    return {
        "total": total,
        "by_severity": by_severity,
        "by_detector": by_detector,
    }


class MultiJurisdictionRunner:
    """Runs analysis across multiple jurisdictions."""

    def __init__(self, registry: JurisdictionRegistry) -> None:
        self.registry = registry
        self._results: dict[str, dict[str, Any]] = {}

    def analyze_jurisdiction(
        self,
        jurisdiction_id: str,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run all detectors against documents for a single jurisdiction.

        Args:
            jurisdiction_id: Must be registered in self.registry.
            documents: List of document dicts, each containing:
                - ``document_text`` (str): raw text content
                - ``metadata`` (dict, optional): title, document_id, etc.

        Returns:
            ::

                {
                    "jurisdiction_id": str,
                    "jurisdiction_name": str,
                    "document_count": int,
                    "results": list[dict],   # per-document analysis results
                    "anomaly_summary": {
                        "total": int,
                        "by_severity": {"critical": int, "high": int, ...},
                        "by_detector": {"fiscal": int, ...},
                    },
                }

        Raises:
            KeyError: If *jurisdiction_id* is not in the registry.
        """
        config = self.registry.get(jurisdiction_id)  # raises KeyError if absent

        doc_results: list[dict[str, Any]] = []
        for doc in documents:
            text = doc.get("document_text", "")
            metadata = dict(doc.get("metadata", {}))
            try:
                result = run_full_analysis(
                    text,
                    metadata,
                    jurisdiction_config=config,
                )
                result["jurisdiction_id"] = jurisdiction_id
                doc_results.append(result)
            except Exception as exc:
                logger.warning(
                    "Analysis failed for jurisdiction %r, doc %r: %s",
                    jurisdiction_id,
                    metadata.get("document_id"),
                    exc,
                )

        summary = _build_anomaly_summary(doc_results)
        output: dict[str, Any] = {
            "jurisdiction_id": jurisdiction_id,
            "jurisdiction_name": config.name,
            "document_count": len(documents),
            "results": doc_results,
            "anomaly_summary": summary,
        }

        # Temporal analysis — best-effort, never breaks the main pipeline
        try:
            from oraculus_di_auditor.temporal.evolution_detector import (
                EvolutionPatternDetector,
            )
            from oraculus_di_auditor.temporal.lineage_builder import LineageBuilder

            builder = LineageBuilder()
            builder.load_documents(documents)
            lineages = builder.build_lineages()
            patterns = EvolutionPatternDetector(lineages).detect_all_patterns()
            output["temporal"] = {
                "lineage_count": len(lineages),
                "pattern_count": len(patterns),
                "lineages": [ln.model_dump() for ln in lineages],
                "patterns": [p.model_dump() for p in patterns],
            }
        except Exception as exc:  # noqa: BLE001
            logger.debug("Temporal analysis skipped for %r: %s", jurisdiction_id, exc)
            output["temporal"] = {"lineage_count": 0, "pattern_count": 0}

        self._results[jurisdiction_id] = output
        return output

    def analyze_all(
        self,
        documents_by_jurisdiction: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Run analysis across all jurisdictions.

        Args:
            documents_by_jurisdiction: Mapping of jurisdiction_id to a list of
                document dicts (same shape expected by
                :meth:`analyze_jurisdiction`).

        Returns:
            ::

                {
                    "jurisdictions_analyzed": int,
                    "total_documents": int,
                    "total_anomalies": int,
                    "per_jurisdiction": {jurisdiction_id: result_dict, ...},
                }
        """
        per_jurisdiction: dict[str, Any] = {}
        total_documents = 0
        total_anomalies = 0

        for jurisdiction_id, documents in documents_by_jurisdiction.items():
            result = self.analyze_jurisdiction(jurisdiction_id, documents)
            per_jurisdiction[jurisdiction_id] = result
            total_documents += result["document_count"]
            total_anomalies += result["anomaly_summary"]["total"]

        return {
            "jurisdictions_analyzed": len(per_jurisdiction),
            "total_documents": total_documents,
            "total_anomalies": total_anomalies,
            "per_jurisdiction": per_jurisdiction,
        }

    def get_results(self, jurisdiction_id: str) -> dict[str, Any] | None:
        """Retrieve cached results for a jurisdiction."""
        return self._results.get(jurisdiction_id)

    def get_all_results(self) -> dict[str, dict[str, Any]]:
        """Retrieve all cached results."""
        return dict(self._results)
