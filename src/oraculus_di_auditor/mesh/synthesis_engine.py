"""Synthesis Engine for Phase 10 Agent Mesh.

Aggregates and harmonizes results from multiple agents into
unified insights.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class SynthesisEngine:
    """Multi-source result synthesis and harmonization engine.

    Merges results from multiple agents, resolves conflicts,
    and produces unified analytical outputs.
    """

    def __init__(self):
        """Initialize synthesis engine."""
        self.synthesis_history: list[dict[str, Any]] = []
        logger.info("SynthesisEngine initialized")

    def synthesize_results(
        self,
        results: list[dict[str, Any]],
        synthesis_strategy: str = "merge",
    ) -> dict[str, Any]:
        """Synthesize results from multiple agents.

        Args:
            results: List of agent task results
            synthesis_strategy: Strategy (merge, harmonize, aggregate, consensus)

        Returns:
            Synthesized result
        """
        logger.info(
            f"Synthesizing {len(results)} results with strategy: {synthesis_strategy}"
        )

        if not results:
            return {
                "success": False,
                "message": "No results to synthesize",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Apply synthesis strategy
        if synthesis_strategy == "merge":
            synthesized = self._merge_results(results)
        elif synthesis_strategy == "harmonize":
            synthesized = self._harmonize_results(results)
        elif synthesis_strategy == "aggregate":
            synthesized = self._aggregate_results(results)
        elif synthesis_strategy == "consensus":
            synthesized = self._consensus_results(results)
        else:
            synthesized = self._merge_results(results)

        # Record synthesis
        synthesis_record = {
            "result_count": len(results),
            "strategy": synthesis_strategy,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.synthesis_history.append(synthesis_record)

        return {
            "success": True,
            "synthesized_result": synthesized,
            "strategy_used": synthesis_strategy,
            "sources_count": len(results),
            "timestamp": synthesis_record["timestamp"],
        }

    def _merge_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge results by combining all data."""
        merged: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "sources": len(results),
            "merged_data": {},
            "metadata": {},
        }

        for result in results:
            agent_id = result.get("agent_id", "unknown")
            result_data = result.get("result", {})
            merged["merged_data"][agent_id] = result_data

            # Merge metrics
            if "metrics" in result:
                if "metrics" not in merged["metadata"]:
                    merged["metadata"]["metrics"] = {}
                merged["metadata"]["metrics"][agent_id] = result["metrics"]

        return merged

    def _resolve_most_common_value(self, values: list[Any]) -> Any:
        """Resolve conflicts by finding the most common value."""
        try:
            return max(set(values), key=values.count)
        except TypeError:
            # Values are unhashable, use string representation for counting
            str_values = [str(v) for v in values]
            most_common_str = max(set(str_values), key=str_values.count)
            # Find and return original value matching the most common string
            for v in values:
                if str(v) == most_common_str:
                    return v
            return values[0] if values else None

    def _detect_conflicts(self, values: list[Any]) -> bool:
        """Detect if there are conflicts among values."""
        hashable_values = []
        for v in values:
            try:
                hashable_values.append((type(v), v))
            except TypeError:
                hashable_values.append((type(v), str(v)))
        return len(set(hashable_values)) > 1

    def _harmonize_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Harmonize conflicting results through conflict resolution."""
        harmonized: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "sources": len(results),
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "harmonized_data": {},
        }

        # Collect all keys across results
        all_keys: set[str] = set()
        for result in results:
            result_data = result.get("result", {})
            all_keys.update(result_data.keys())

        # For each key, detect and resolve conflicts
        for key in all_keys:
            values = []
            for result in results:
                result_data = result.get("result", {})
                if key in result_data:
                    values.append(result_data[key])

            # Check for conflicts and resolve if needed
            if self._detect_conflicts(values):
                harmonized["conflicts_detected"] += 1
                harmonized["harmonized_data"][key] = self._resolve_most_common_value(
                    values
                )
                harmonized["conflicts_resolved"] += 1
            else:
                # No conflict
                harmonized["harmonized_data"][key] = values[0] if values else None

        return harmonized

    def _aggregate_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate numerical and statistical results."""
        aggregated: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "sources": len(results),
            "aggregations": {},
        }

        # Collect all numerical keys
        numerical_keys: set[str] = set()
        for result in results:
            result_data = result.get("result", {})
            for key, value in result_data.items():
                if isinstance(value, int | float):
                    numerical_keys.add(key)

        # Aggregate each numerical key
        for key in numerical_keys:
            values = []
            for result in results:
                result_data = result.get("result", {})
                if key in result_data:
                    value = result_data[key]
                    if isinstance(value, int | float):
                        values.append(value)

            if values:
                aggregated["aggregations"][key] = {
                    "sum": sum(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        return aggregated

    def _consensus_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Build consensus view from multiple agent results."""
        consensus: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "sources": len(results),
            "consensus_data": {},
            "confidence": {},
        }

        # Collect all keys
        all_keys: set[str] = set()
        for result in results:
            result_data = result.get("result", {})
            all_keys.update(result_data.keys())

        # For each key, build consensus
        for key in all_keys:
            values = []
            for result in results:
                result_data = result.get("result", {})
                if key in result_data:
                    values.append(result_data[key])

            if not values:
                continue

            # Calculate consensus value (most common)
            value_counts: dict[str, int] = {}
            for value in values:
                value_str = str(value)
                value_counts[value_str] = value_counts.get(value_str, 0) + 1

            consensus_value_str = max(value_counts.items(), key=lambda x: x[1])[0]
            consensus_count = value_counts[consensus_value_str]

            # Calculate confidence (percentage of agents agreeing)
            confidence = consensus_count / len(values)

            # Store consensus value (convert back from string if possible)
            consensus["consensus_data"][key] = consensus_value_str
            consensus["confidence"][key] = confidence

        return consensus

    def get_synthesis_stats(self) -> dict[str, Any]:
        """Get synthesis statistics.

        Returns:
            Synthesis statistics and metrics
        """
        total_syntheses = len(self.synthesis_history)

        if total_syntheses == 0:
            return {
                "total_syntheses": 0,
                "syntheses_by_strategy": {},
                "average_source_count": 0,
            }

        # Count by strategy
        by_strategy: dict[str, int] = {}
        total_sources = 0

        for record in self.synthesis_history:
            strategy = record.get("strategy", "unknown")
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1
            total_sources += record.get("result_count", 0)

        avg_sources = total_sources / total_syntheses if total_syntheses > 0 else 0

        return {
            "total_syntheses": total_syntheses,
            "syntheses_by_strategy": by_strategy,
            "average_source_count": avg_sources,
            "timestamp": datetime.now(UTC).isoformat(),
        }


__all__ = ["SynthesisEngine"]
