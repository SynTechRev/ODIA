from __future__ import annotations

from oraculus_di_auditor.analysis.scalar_core import (
    compute_recursive_scalar_score,
)


def test_scalar_core_scores_empty_anomalies_as_one():
    score = compute_recursive_scalar_score({"document_id": "d"}, [])
    assert 0.99 <= score <= 1.0


def test_scalar_core_penalizes_each_anomaly_slightly():
    doc = {"document_id": "d"}
    one = compute_recursive_scalar_score(doc, [{}])
    two = compute_recursive_scalar_score(doc, [{}, {}])
    assert one > two
    assert 0.0 <= two <= 1.0
