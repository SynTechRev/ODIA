"""Evaluation harness for Layer 2 extraction backends."""

from odia_ai.evaluation.harness import (
    EvaluationResult,
    SetMetrics,
    compare_backends,
    evaluate_backend,
    write_evaluation_report,
)

__all__ = [
    "EvaluationResult",
    "SetMetrics",
    "evaluate_backend",
    "compare_backends",
    "write_evaluation_report",
]
