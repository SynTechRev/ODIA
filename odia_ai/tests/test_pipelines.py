"""Tests for extraction, evaluation, continual-learning, and registry."""

from __future__ import annotations

import json
from pathlib import Path

from odia_ai.extraction import (
    ExtractionService,
    PatternExtractionBackend,
)
from odia_ai.extraction.extractor import _extract_first_json

SAMPLE_DOC = (
    "The City of Sampleton authorized a $49,700 Flock Safety sole-source "
    "procurement on consent calendar Item 7.4 via Resolution 2024-15. "
    "CJIS Security Addendum not referenced. SB 524 compliance not "
    "documented. This is a CRITICAL F-2 finding. Axon Evidence.com is "
    "used for BWC storage."
)


# -------------------- Extraction tests --------------------


def test_pattern_backend_always_available():
    backend = PatternExtractionBackend()
    assert backend.is_available()
    assert backend.name == "pattern"


def test_pattern_backend_extracts_vendors():
    backend = PatternExtractionBackend()
    out = backend.extract(SAMPLE_DOC)
    assert any("flock" in v.lower() for v in out.vendors)
    assert any("axon" in v.lower() for v in out.vendors)


def test_pattern_backend_extracts_statutes():
    backend = PatternExtractionBackend()
    out = backend.extract(SAMPLE_DOC)
    assert any("524" in s for s in out.statutes_cited)
    assert any("cjis" in s.lower() for s in out.statutes_cited)


def test_pattern_backend_detects_anomalies():
    backend = PatternExtractionBackend()
    out = backend.extract(SAMPLE_DOC)
    categories = [c.get("category") for c in out.anomaly_candidates]
    # Sample doc has CRITICAL F-2 + Flock without SB 524 (F-3) + Axon without CJIS (F-5)
    assert "F-2" in categories or any(
        c.get("category", "").startswith("F-") for c in out.anomaly_candidates
    )


def test_extraction_service_uses_pattern_as_fallback():
    svc = ExtractionService(force_backend="pattern")
    out = svc.extract(SAMPLE_DOC)
    assert out.backend_used == "pattern"
    assert len(out.vendors) > 0


def test_extraction_service_empty_text_returns_stub():
    svc = ExtractionService(force_backend="pattern")
    out = svc.extract("")
    assert out.backend_used == "stub"


def test_extract_first_json_handles_prose_wrapping():
    text = 'Here is some output:\n{"key": "value"}\nThanks!'
    result = _extract_first_json(text)
    assert result == {"key": "value"}


def test_extract_first_json_handles_nested_braces():
    text = 'Output: {"outer": {"inner": "val"}, "list": [1, 2]}'
    result = _extract_first_json(text)
    assert result["outer"]["inner"] == "val"


def test_extract_first_json_raises_on_no_json():
    import pytest

    with pytest.raises(ValueError):
        _extract_first_json("no json here at all")


# -------------------- Evaluation tests --------------------


def test_set_metrics_math():
    from odia_ai.evaluation import SetMetrics

    m = SetMetrics()
    m.update({"a", "b", "c"}, {"a", "b"})
    # predicted = {a,b,c}, gold = {a,b}
    # TP=2 (a,b), FP=1 (c), FN=0
    assert m.true_positives == 2
    assert m.false_positives == 1
    assert m.false_negatives == 0
    assert abs(m.precision - 2 / 3) < 0.001
    assert m.recall == 1.0
    assert abs(m.f1 - 0.8) < 0.001


def test_evaluate_backend_on_tiny_dataset(tmp_path: Path):
    from odia_ai.evaluation import evaluate_backend

    eval_file = tmp_path / "eval.jsonl"
    record = {
        "instruction": "Extract.",
        "input": SAMPLE_DOC,
        "output": json.dumps(
            {
                "vendors": ["Flock Safety", "Axon Enterprise"],
                "persons": [],
                "dollar_amounts": [],
                "statutes_cited": ["SB 524", "CJIS"],
                "procurement_instruments": [],
                "governance_bodies": [],
                "anomaly_candidates": [
                    {"category": "F-2", "severity": "CRITICAL", "reasoning": ""}
                ],
            }
        ),
        "system": "",
    }
    eval_file.write_text(json.dumps(record) + "\n", encoding="utf-8")

    backend = PatternExtractionBackend()
    result = evaluate_backend(backend, eval_file)

    assert result.num_examples == 1
    assert result.errors == 0
    assert "vendors" in result.field_metrics
    # Pattern backend should find at least some vendors (Flock, Axon)
    assert result.field_metrics["vendors"].true_positives >= 1


# -------------------- Continual-learning tests --------------------


def test_correction_store_round_trip(tmp_path: Path):
    from odia_ai.continual import CorrectionStore, new_correction

    db_path = tmp_path / "corrections.db"
    store = CorrectionStore(db_path)

    corr = new_correction(
        input_text="some document text",
        field_name="vendors",
        correction_type="addition",
        original_value=json.dumps([]),
        corrected_value=json.dumps(["Spartan Camera"]),
        model_version_id="test-v1",
        jurisdiction="Woodlake",
    )
    store.record(corr)

    assert store.count() == 1
    # mark reviewed
    store.mark_reviewed([corr.correction_id])
    assert store.count(reviewed_only=True) == 1

    # Pending for training
    pending = store.pending_for_training()
    assert len(pending) == 1
    assert pending[0].correction_id == corr.correction_id

    # Apply and verify
    n = store.mark_applied([corr.correction_id])
    assert n == 1
    assert store.count(unapplied_only=True) == 0


def test_trigger_decision_below_threshold(tmp_path: Path):
    from odia_ai.continual import (
        CorrectionStore,
        TriggerConfig,
        new_correction,
        should_trigger_retraining,
    )

    store = CorrectionStore(tmp_path / "c.db")
    # Add 5 corrections (below default threshold of 50)
    for i in range(5):
        c = new_correction(
            input_text=f"doc{i}",
            field_name="vendors",
            correction_type="addition",
            original_value="[]",
            corrected_value=f'["v{i}"]',
            model_version_id="v1",
        )
        store.record(c)
        store.mark_reviewed([c.correction_id])

    decision = should_trigger_retraining(store, TriggerConfig())
    assert not decision.should_retrain


def test_trigger_decision_at_threshold(tmp_path: Path):
    from odia_ai.continual import (
        CorrectionStore,
        TriggerConfig,
        new_correction,
        should_trigger_retraining,
    )

    store = CorrectionStore(tmp_path / "c.db")
    for i in range(10):
        c = new_correction(
            input_text=f"doc{i}",
            field_name="vendors",
            correction_type="addition",
            original_value="[]",
            corrected_value=f'["v{i}"]',
            model_version_id="v1",
        )
        store.record(c)
        store.mark_reviewed([c.correction_id])

    # Lower threshold to 10 -> should trigger
    decision = should_trigger_retraining(store, TriggerConfig(min_new_corrections=10))
    assert decision.should_retrain


def test_correction_to_training_example():
    from odia_ai.continual import Correction, correction_to_training_example

    corr = Correction(
        correction_id="c1",
        document_hash="h1",
        field_name="vendors",
        correction_type="addition",
        original_value="[]",
        corrected_value=json.dumps(["Spartan Camera"]),
        input_text="some doc",
        model_version_id="v1",
        jurisdiction="Woodlake",
    )
    rec = correction_to_training_example(corr)
    assert "instruction" in rec
    assert "input" in rec
    assert "output" in rec
    output = json.loads(rec["output"])
    assert "Spartan Camera" in output["vendors"]


# -------------------- Registry tests --------------------


def test_registry_register_and_get(tmp_path: Path):
    from odia_ai.registry import ModelRegistry, ModelVersion, generate_version_id

    registry = ModelRegistry(tmp_path / "registry")
    version = ModelVersion(
        version_id=generate_version_id(),
        base_model="meta-llama/Llama-3.1-8B-Instruct",
        model_path="/tmp/fake",
    )
    vid = registry.register(version)
    loaded = registry.get(vid)
    assert loaded is not None
    assert loaded.version_id == vid


def test_registry_promotion_demotes_prior_production(tmp_path: Path):
    from odia_ai.registry import ModelRegistry, ModelVersion, generate_version_id

    registry = ModelRegistry(tmp_path / "registry")

    v1 = ModelVersion(
        version_id=generate_version_id(), base_model="base", model_path="p1"
    )
    v2 = ModelVersion(
        version_id=generate_version_id(), base_model="base", model_path="p2"
    )
    registry.register(v1)
    registry.register(v2)

    registry.set_deployment_status(v1.version_id, "production")
    assert registry.production_version().version_id == v1.version_id  # type: ignore

    registry.set_deployment_status(v2.version_id, "production")
    prod = registry.production_version()
    assert prod is not None
    assert prod.version_id == v2.version_id

    # v1 should be demoted to staging
    v1_reloaded = registry.get(v1.version_id)
    assert v1_reloaded.deployment_status == "staging"  # type: ignore


def test_registry_list_versions(tmp_path: Path):
    from odia_ai.registry import ModelRegistry, ModelVersion, generate_version_id

    registry = ModelRegistry(tmp_path / "registry")
    v1 = ModelVersion(version_id=generate_version_id(), base_model="b", model_path="p1")
    v2 = ModelVersion(version_id=generate_version_id(), base_model="b", model_path="p2")
    registry.register(v1)
    registry.register(v2)

    versions = registry.list_versions()
    assert len(versions) == 2


# -------------------- Config tests --------------------


def test_config_round_trip(tmp_path: Path):
    from odia_ai.configs import ODIAAIConfig, load_config, write_config

    cfg = ODIAAIConfig()
    cfg.training.base_model = "custom/model"
    cfg.dataset.random_seed = 999

    path = tmp_path / "test_config.json"
    write_config(cfg, path)

    reloaded = load_config(path)
    assert reloaded.training.base_model == "custom/model"
    assert reloaded.dataset.random_seed == 999


def test_config_defaults_when_no_file():
    from odia_ai.configs import load_config

    cfg = load_config(None)
    assert cfg.training.base_model  # non-empty default
    assert cfg.dataset.holdout_validation_jurisdiction == "TCSO"
    assert cfg.dataset.holdout_test_jurisdiction == "Exeter"
