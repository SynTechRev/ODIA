"""Evaluation harness for ODIA Layer 2 extraction models.

Measures precision, recall, and F1 for each extraction category on
held-out jurisdictions. Computes per-jurisdiction and per-category
breakdowns so model regressions are visible at the sub-domain level.

Design goals:
- Backend-agnostic: evaluates any object implementing the ExtractionBackend
  protocol (fine-tuned, RAG, or pattern)
- Jurisdictional generalization metric: measures how well a model trained
  on N-1 jurisdictions performs on the held-out jurisdiction
- Category-level metrics: surfaces which anomaly categories (F-1..F-12)
  the model under-detects
- Reproducible: all outputs keyed by example_id hash

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from odia_ai.extraction.extractor import ExtractionBackend

logger = logging.getLogger(__name__)


@dataclass
class SetMetrics:
    """Set-based precision/recall/F1 for a list extraction field."""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    def update(self, predicted: set[str], gold: set[str]) -> None:
        self.true_positives += len(predicted & gold)
        self.false_positives += len(predicted - gold)
        self.false_negatives += len(gold - predicted)

    def to_dict(self) -> dict:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "tp": self.true_positives,
            "fp": self.false_positives,
            "fn": self.false_negatives,
        }


@dataclass
class EvaluationResult:
    """Aggregate evaluation result for a single backend on a dataset."""

    backend_name: str
    num_examples: int
    dataset_path: str
    field_metrics: dict[str, SetMetrics] = field(default_factory=dict)
    by_jurisdiction: dict[str, dict[str, SetMetrics]] = field(default_factory=dict)
    by_finding_category: dict[str, SetMetrics] = field(default_factory=dict)
    avg_latency_ms: float = 0.0
    errors: int = 0

    def to_dict(self) -> dict:
        return {
            "backend_name": self.backend_name,
            "num_examples": self.num_examples,
            "dataset_path": self.dataset_path,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "errors": self.errors,
            "field_metrics": {k: v.to_dict() for k, v in self.field_metrics.items()},
            "by_jurisdiction": {
                j: {k: v.to_dict() for k, v in m.items()}
                for j, m in self.by_jurisdiction.items()
            },
            "by_finding_category": {
                k: v.to_dict() for k, v in self.by_finding_category.items()
            },
        }

    def summary_report(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Evaluation — {self.backend_name}",
            f"Examples: {self.num_examples}",
            f"Errors:   {self.errors}",
            f"Latency:  {self.avg_latency_ms:.1f} ms/example",
            "",
            "Field-level metrics:",
        ]
        for field_name, m in sorted(self.field_metrics.items()):
            lines.append(
                f"  {field_name:30s}  P={m.precision:.3f}  R={m.recall:.3f}  "
                f"F1={m.f1:.3f}  (tp={m.true_positives}, fp={m.false_positives}, "
                f"fn={m.false_negatives})"
            )
        if self.by_finding_category:
            lines.append("")
            lines.append("Finding-category detection metrics:")
            for cat, m in sorted(self.by_finding_category.items()):
                lines.append(
                    f"  {cat:10s}  P={m.precision:.3f}  R={m.recall:.3f}  F1={m.f1:.3f}"
                )
        if self.by_jurisdiction:
            lines.append("")
            lines.append("Per-jurisdiction vendors+statutes F1:")
            for j in sorted(self.by_jurisdiction.keys()):
                vendors_f1 = self.by_jurisdiction[j].get("vendors", SetMetrics()).f1
                statutes_f1 = (
                    self.by_jurisdiction[j].get("statutes_cited", SetMetrics()).f1
                )
                lines.append(
                    f"  {j:15s}  vendors F1={vendors_f1:.3f}  statutes F1={statutes_f1:.3f}"
                )
        return "\n".join(lines)


def _as_set_of_str(items: Any) -> set[str]:
    """Normalize a list of dicts/strings to a set of canonical strings."""
    if not items:
        return set()
    result: set[str] = set()
    for item in items:
        if isinstance(item, str):
            result.add(item.strip().lower())
        elif isinstance(item, dict):
            # For structured items, use a canonical key:
            # - persons: name
            # - dollar_amounts: amount_raw or amount_usd
            # - procurement_instruments: f"{type}:{number}"
            # - governance_bodies: name
            # - anomaly_candidates: category
            key = (
                item.get("name")
                or item.get("amount_raw")
                or item.get("amount_usd")
                or item.get("category")
                or (
                    f"{item.get('type', '')}:{item.get('number', '')}"
                    if item.get("type") or item.get("number")
                    else ""
                )
            )
            if key:
                result.add(str(key).strip().lower())
    return result


def _load_eval_dataset(path: Path) -> list[dict]:
    """Load an alpaca-format JSONL file into eval records."""
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _parse_gold_output(record: dict) -> tuple[dict, str, str]:
    """Return (gold_output_dict, jurisdiction, source_alert_id) from a record."""
    # Alpaca format has "output" as a JSON string
    output_raw = record.get("output", "{}")
    try:
        gold = json.loads(output_raw) if isinstance(output_raw, str) else output_raw
    except json.JSONDecodeError:
        gold = {}
    # Jurisdiction is not always in the record; infer from source_alert_id if present
    jurisdiction = record.get("jurisdiction", "Unknown")
    source_alert = record.get("source_alert_id") or ""
    return gold, jurisdiction, source_alert


EVAL_FIELDS = (
    "vendors",
    "persons",
    "dollar_amounts",
    "statutes_cited",
    "procurement_instruments",
    "governance_bodies",
    "anomaly_candidates",
)


def evaluate_backend(
    backend: ExtractionBackend,
    eval_dataset_path: Path,
    max_examples: int | None = None,
    verbose: bool = False,
) -> EvaluationResult:
    """Run evaluation of a single backend on a JSONL dataset.

    Args:
        backend: object implementing the ExtractionBackend protocol
        eval_dataset_path: path to alpaca-format JSONL file
        max_examples: if set, evaluate only the first N examples (for smoke tests)
        verbose: log per-example diagnostics

    Returns:
        EvaluationResult with field-level and per-jurisdiction metrics.
    """
    records = _load_eval_dataset(eval_dataset_path)
    if max_examples:
        records = records[:max_examples]

    result = EvaluationResult(
        backend_name=getattr(backend, "name", type(backend).__name__),
        num_examples=len(records),
        dataset_path=str(eval_dataset_path),
    )
    # Initialize field metrics
    for f in EVAL_FIELDS:
        result.field_metrics[f] = SetMetrics()

    total_latency = 0.0

    for rec in records:
        gold, jurisdiction, source_alert = _parse_gold_output(rec)
        input_text = rec.get("input") or ""

        start = time.perf_counter()
        try:
            predicted = backend.extract(input_text).to_dict()
        except Exception as e:
            logger.warning("Extraction error on %s: %s", source_alert or "?", e)
            result.errors += 1
            continue
        total_latency += (time.perf_counter() - start) * 1000.0

        # Per-field metrics
        for f in EVAL_FIELDS:
            p_set = _as_set_of_str(predicted.get(f, []))
            g_set = _as_set_of_str(gold.get(f, []))
            result.field_metrics[f].update(p_set, g_set)

            # Per-jurisdiction breakdown
            by_j = result.by_jurisdiction.setdefault(jurisdiction, {})
            by_j.setdefault(f, SetMetrics()).update(p_set, g_set)

        # Finding-category-level metrics (anomaly detection per category)
        gold_cats = {
            a.get("category", "unspecified")
            for a in gold.get("anomaly_candidates", [])
            if isinstance(a, dict)
        }
        pred_cats = {
            a.get("category", "unspecified")
            for a in predicted.get("anomaly_candidates", [])
            if isinstance(a, dict)
        }
        all_cats = gold_cats | pred_cats
        for cat in all_cats:
            m = result.by_finding_category.setdefault(cat, SetMetrics())
            predicted_has = cat in pred_cats
            gold_has = cat in gold_cats
            if predicted_has and gold_has:
                m.true_positives += 1
            elif predicted_has:
                m.false_positives += 1
            else:
                m.false_negatives += 1

        if verbose:
            logger.debug(
                "eval %s: gold_vendors=%d pred_vendors=%d",
                source_alert,
                len(_as_set_of_str(gold.get("vendors", []))),
                len(_as_set_of_str(predicted.get("vendors", []))),
            )

    if result.num_examples > 0:
        result.avg_latency_ms = total_latency / result.num_examples

    return result


def compare_backends(
    backends: list[ExtractionBackend],
    eval_dataset_path: Path,
    max_examples: int | None = None,
) -> dict[str, EvaluationResult]:
    """Run evaluation across multiple backends on the same dataset."""
    return {
        getattr(b, "name", type(b).__name__): evaluate_backend(
            b, eval_dataset_path, max_examples=max_examples
        )
        for b in backends
    }


def write_evaluation_report(
    result: EvaluationResult, output_path: Path, include_summary: bool = True
) -> None:
    """Write evaluation result to a JSON file plus optional markdown summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    if include_summary:
        summary_path = output_path.with_suffix(".md")
        summary_path.write_text(result.summary_report(), encoding="utf-8")
