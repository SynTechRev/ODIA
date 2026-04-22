"""Stdlib-only test runner for when pytest is unavailable.

Wraps the pytest-style test functions in unittest.TestCase subclasses
so they can run without external dependencies. Use:

    python -m odia_ai.tests.run_stdlib_tests
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Import all the test functions from our existing test modules
from odia_ai.backref import (
    ExtractedAlert,
    compute_corpus_stats,
    extract_alerts_from_file,
    write_jsonl,
)
from odia_ai.backref.extractor import (
    detect_finding_category,
    detect_severity,
    extract_dollars,
    extract_resolutions,
    extract_statutes,
    extract_vendors,
)
from odia_ai.extraction import (
    ExtractionService,
    PatternExtractionBackend,
)
from odia_ai.extraction.extractor import _extract_first_json
from odia_ai.training import (
    alert_to_training_example,
    assign_split,
    build_dataset,
    write_dataset_splits,
)
from odia_ai.training.dataset_builder import (
    jurisdiction_transfer,
    negative_example,
)

SAMPLE_MAS = """
# **EXETER MAS V16.0 — SAMPLE**

## EXE-138 CRITICAL — Public Safety Ad Hoc Task Force

On October 10, 2023, Mayor Pro Tem Mills requested that a Public Safety
Ad Hoc Task Force report be agendized for a future meeting. Council
consensus approved. No authorizing resolution exists in the 220-file
corpus. This is a CRITICAL governance-body obscurity finding (F-11).

Vendors mentioned: Flock Safety, Axon Enterprise.
Statutes: SB 524 not referenced; Brown Act implicated.
Resolution 2023-12 cited in contrast; $40,690 restroom trailer
procurement on same consent calendar.

## EXE-139 HIGH — First Community Services Officer

On October 26, 2021, City Administrator Ennis announced the appointment
of the first Community Services Officer. This was 4 years before the
Flock Safety CEQA NOE filing (November 21, 2025).
"""

SAMPLE_DOC = (
    "The City of Sampleton authorized a $49,700 Flock Safety sole-source "
    "procurement on consent calendar Item 7.4 via Resolution 2024-15. "
    "CJIS Security Addendum not referenced. SB 524 compliance not "
    "documented. This is a CRITICAL F-2 finding. Axon Evidence.com is "
    "used for BWC storage."
)


def _make_alert(alert_id: str, jurisdiction: str, severity: str = "HIGH") -> ExtractedAlert:
    return ExtractedAlert(
        alert_id=alert_id,
        jurisdiction=jurisdiction,
        severity=severity,
        finding_category="F-2",
        title=f"Sample {alert_id}",
        body=(
            f"Alert {alert_id} documents a Flock Safety deployment at "
            f"{jurisdiction} without SB 524 compliance. "
            f"Resolution 2024-15 placed item on consent calendar. "
            f"$49,700 sole-source procurement. CJIS Security Addendum absent. "
            f"This is a structural F-2 finding."
        ),
        vendors_mentioned=["Flock Safety"],
        statutes_mentioned=["SB 524", "CJIS"],
        resolutions_mentioned=["2024-15"],
        dollar_amounts=["$49,700"],
        source_mas_file=f"{jurisdiction}_MAS.md",
        source_mas_version="1.0",
        body_char_length=300,
    )


class BackrefTests(unittest.TestCase):
    def test_detect_severity(self):
        self.assertEqual(detect_severity("This is a CRITICAL finding"), "CRITICAL")
        self.assertEqual(detect_severity("this is a high alert"), "HIGH")
        self.assertIsNone(detect_severity("no severity here"))

    def test_detect_finding_category(self):
        self.assertEqual(detect_finding_category("relates to F-11 analysis"), "F-11")
        self.assertEqual(detect_finding_category("see F-3 below"), "F-3")
        self.assertIsNone(detect_finding_category("F-99 is invalid"))
        self.assertIsNone(detect_finding_category("no finding here"))

    def test_extract_vendors(self):
        text = "The Flock Safety and Axon Enterprise deployment was not authorized."
        vendors = extract_vendors(text)
        self.assertIn("Flock Safety", vendors)
        self.assertIn("Axon Enterprise", vendors)

    def test_extract_statutes(self):
        text = "Universal noncompliance with SB 524 since January 1, 2026. CJIS missing."
        statutes = extract_statutes(text)
        self.assertIn("SB 524", statutes)
        self.assertIn("CJIS", statutes)

    def test_extract_resolutions(self):
        text = "Resolution 2023-12 and Agreement 31448 were executed."
        resolutions = extract_resolutions(text)
        self.assertIn("2023-12", resolutions)
        self.assertIn("31448", resolutions)

    def test_extract_dollars(self):
        text = "The contract totaled $18,824,577 plus $2,113,660.76 amendment."
        dollars = extract_dollars(text)
        self.assertTrue(any("$18,824,577" in d for d in dollars))

    def test_extract_alerts_from_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(SAMPLE_MAS)
            path = Path(f.name)
        try:
            alerts = extract_alerts_from_file(path)
            self.assertEqual(len(alerts), 2)
            ids = [a.alert_id for a in alerts]
            self.assertIn("EXE-138", ids)
            self.assertIn("EXE-139", ids)
            critical = next(a for a in alerts if a.alert_id == "EXE-138")
            self.assertEqual(critical.jurisdiction, "Exeter")
            self.assertEqual(critical.severity, "CRITICAL")
            self.assertEqual(critical.finding_category, "F-11")
            self.assertIn("Flock Safety", critical.vendors_mentioned)
            self.assertIn("SB 524", critical.statutes_mentioned)
        finally:
            path.unlink(missing_ok=True)

    def test_compute_corpus_stats(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(SAMPLE_MAS)
            path = Path(f.name)
        try:
            alerts = extract_alerts_from_file(path)
            stats = compute_corpus_stats(alerts)
            self.assertEqual(stats["total_alerts"], 2)
            self.assertEqual(stats["by_jurisdiction"]["Exeter"], 2)
            self.assertGreaterEqual(stats["by_severity"]["CRITICAL"], 1)
        finally:
            path.unlink(missing_ok=True)

    def test_write_jsonl(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(SAMPLE_MAS)
            path = Path(f.name)
        try:
            with tempfile.TemporaryDirectory() as td:
                alerts = extract_alerts_from_file(path)
                out = Path(td) / "alerts.jsonl"
                count = write_jsonl(alerts, out)
                self.assertEqual(count, len(alerts))
                self.assertTrue(out.exists())
                lines = out.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(lines), count)
        finally:
            path.unlink(missing_ok=True)


class DatasetBuilderTests(unittest.TestCase):
    def test_alert_to_training_example(self):
        alert = _make_alert("TUL-055", "Tulare", "CRITICAL")
        ex = alert_to_training_example(alert)
        self.assertEqual(ex.source_alert_id, "TUL-055")
        self.assertEqual(ex.jurisdiction, "Tulare")
        self.assertFalse(ex.is_synthetic)
        self.assertIn("Flock Safety", ex.output_json["vendors"])

    def test_assign_split_holds_out(self):
        tcso = alert_to_training_example(_make_alert("TCSO-010", "TCSO"))
        exeter = alert_to_training_example(_make_alert("EXE-100", "Exeter"))
        visalia = alert_to_training_example(_make_alert("VPD-200", "Visalia"))
        self.assertEqual(assign_split(tcso), "validation")
        self.assertEqual(assign_split(exeter), "test")
        self.assertEqual(assign_split(visalia), "train")

    def test_jurisdiction_transfer(self):
        ex = alert_to_training_example(_make_alert("VPD-100", "Visalia"))
        transferred = jurisdiction_transfer(ex, ("Visalia", "Ridgecrest"))
        self.assertIsNotNone(transferred)
        self.assertTrue(transferred.is_synthetic)  # type: ignore
        self.assertEqual(transferred.jurisdiction, "Ridgecrest")  # type: ignore
        self.assertNotIn("Visalia", transferred.input_text)  # type: ignore
        self.assertIn("Ridgecrest", transferred.input_text)  # type: ignore

    def test_jurisdiction_transfer_no_match(self):
        ex = alert_to_training_example(_make_alert("VPD-100", "Visalia"))
        result = jurisdiction_transfer(ex, ("Porterville", "Lemoore"))
        self.assertIsNone(result)

    def test_negative_example(self):
        neg = negative_example("Routine council meeting minutes.", "test_id")
        self.assertTrue(neg.is_synthetic)
        self.assertEqual(neg.synthesis_method, "negative")
        self.assertEqual(neg.output_json["vendors"], [])

    def test_build_dataset_with_synthesis(self):
        alerts = [
            _make_alert("VPD-001", "Visalia"),
            _make_alert("PPD-002", "Porterville"),
            _make_alert("TCSO-003", "TCSO"),
            _make_alert("EXE-004", "Exeter"),
        ]
        examples = build_dataset(alerts, enable_jurisdiction_transfer=True)
        self.assertGreaterEqual(len(examples), len(alerts))

        by_j = {}
        for e in examples:
            by_j.setdefault(e.jurisdiction, []).append(e.split)
        self.assertIn("test", by_j.get("Exeter", []))
        self.assertIn("validation", by_j.get("TCSO", []))

    def test_write_dataset_splits(self):
        alerts = [
            _make_alert("VPD-001", "Visalia"),
            _make_alert("TCSO-002", "TCSO"),
            _make_alert("EXE-003", "Exeter"),
        ]
        examples = build_dataset(alerts, enable_jurisdiction_transfer=False)
        with tempfile.TemporaryDirectory() as td:
            counts = write_dataset_splits(examples, Path(td), format="alpaca")
            self.assertTrue((Path(td) / "train.jsonl").exists())
            total_written = sum(counts.values())
            self.assertEqual(total_written, len(examples))
            for split_file in Path(td).glob("*.jsonl"):
                for line in split_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        rec = json.loads(line)
                        self.assertIn("instruction", rec)
                        self.assertIn("input", rec)
                        self.assertIn("output", rec)


class ExtractionTests(unittest.TestCase):
    def test_pattern_backend_available(self):
        b = PatternExtractionBackend()
        self.assertTrue(b.is_available())
        self.assertEqual(b.name, "pattern")

    def test_pattern_backend_extracts_vendors(self):
        out = PatternExtractionBackend().extract(SAMPLE_DOC)
        self.assertTrue(any("flock" in v.lower() for v in out.vendors))
        self.assertTrue(any("axon" in v.lower() for v in out.vendors))

    def test_pattern_backend_extracts_statutes(self):
        out = PatternExtractionBackend().extract(SAMPLE_DOC)
        self.assertTrue(any("524" in s for s in out.statutes_cited))
        self.assertTrue(any("cjis" in s.lower() for s in out.statutes_cited))

    def test_pattern_backend_detects_anomalies(self):
        out = PatternExtractionBackend().extract(SAMPLE_DOC)
        categories = [c.get("category") for c in out.anomaly_candidates]
        self.assertTrue(any(c and c.startswith("F-") for c in categories))

    def test_extraction_service_pattern_forced(self):
        svc = ExtractionService(force_backend="pattern")
        out = svc.extract(SAMPLE_DOC)
        self.assertEqual(out.backend_used, "pattern")

    def test_extraction_service_empty_text_stub(self):
        svc = ExtractionService(force_backend="pattern")
        out = svc.extract("")
        self.assertEqual(out.backend_used, "stub")

    def test_extract_first_json_prose_wrapped(self):
        result = _extract_first_json('Output: {"key": "value"}. Done.')
        self.assertEqual(result, {"key": "value"})

    def test_extract_first_json_nested(self):
        result = _extract_first_json('{"outer": {"inner": "val"}, "list": [1, 2]}')
        self.assertEqual(result["outer"]["inner"], "val")

    def test_extract_first_json_no_json(self):
        with self.assertRaises(ValueError):
            _extract_first_json("no json here at all")


class EvaluationTests(unittest.TestCase):
    def test_set_metrics_math(self):
        from odia_ai.evaluation import SetMetrics
        m = SetMetrics()
        m.update({"a", "b", "c"}, {"a", "b"})
        self.assertEqual(m.true_positives, 2)
        self.assertEqual(m.false_positives, 1)
        self.assertEqual(m.false_negatives, 0)
        self.assertAlmostEqual(m.precision, 2 / 3, places=3)
        self.assertEqual(m.recall, 1.0)
        self.assertAlmostEqual(m.f1, 0.8, places=3)

    def test_evaluate_backend_tiny(self):
        from odia_ai.evaluation import evaluate_backend
        with tempfile.TemporaryDirectory() as td:
            eval_file = Path(td) / "eval.jsonl"
            record = {
                "instruction": "Extract.",
                "input": SAMPLE_DOC,
                "output": json.dumps({
                    "vendors": ["Flock Safety", "Axon Enterprise"],
                    "persons": [],
                    "dollar_amounts": [],
                    "statutes_cited": ["SB 524", "CJIS"],
                    "procurement_instruments": [],
                    "governance_bodies": [],
                    "anomaly_candidates": [
                        {"category": "F-2", "severity": "CRITICAL", "reasoning": ""}
                    ],
                }),
                "system": "",
            }
            eval_file.write_text(json.dumps(record) + "\n", encoding="utf-8")
            backend = PatternExtractionBackend()
            result = evaluate_backend(backend, eval_file)
            self.assertEqual(result.num_examples, 1)
            self.assertEqual(result.errors, 0)
            self.assertGreaterEqual(
                result.field_metrics["vendors"].true_positives, 1
            )


class ContinualLearningTests(unittest.TestCase):
    def test_correction_store_round_trip(self):
        from odia_ai.continual import CorrectionStore, new_correction
        with tempfile.TemporaryDirectory() as td:
            store = CorrectionStore(Path(td) / "corrections.db")
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
            self.assertEqual(store.count(), 1)
            store.mark_reviewed([corr.correction_id])
            self.assertEqual(store.count(reviewed_only=True), 1)
            pending = store.pending_for_training()
            self.assertEqual(len(pending), 1)
            n = store.mark_applied([corr.correction_id])
            self.assertEqual(n, 1)
            self.assertEqual(store.count(unapplied_only=True), 0)

    def test_trigger_below_threshold(self):
        from odia_ai.continual import (
            CorrectionStore,
            TriggerConfig,
            new_correction,
            should_trigger_retraining,
        )
        with tempfile.TemporaryDirectory() as td:
            store = CorrectionStore(Path(td) / "c.db")
            for i in range(5):
                c = new_correction(
                    input_text=f"doc{i}", field_name="vendors",
                    correction_type="addition",
                    original_value="[]", corrected_value=f'["v{i}"]',
                    model_version_id="v1",
                )
                store.record(c)
                store.mark_reviewed([c.correction_id])
            decision = should_trigger_retraining(store, TriggerConfig())
            self.assertFalse(decision.should_retrain)

    def test_trigger_at_lowered_threshold(self):
        from odia_ai.continual import (
            CorrectionStore,
            TriggerConfig,
            new_correction,
            should_trigger_retraining,
        )
        with tempfile.TemporaryDirectory() as td:
            store = CorrectionStore(Path(td) / "c.db")
            for i in range(10):
                c = new_correction(
                    input_text=f"doc{i}", field_name="vendors",
                    correction_type="addition",
                    original_value="[]", corrected_value=f'["v{i}"]',
                    model_version_id="v1",
                )
                store.record(c)
                store.mark_reviewed([c.correction_id])
            decision = should_trigger_retraining(
                store, TriggerConfig(min_new_corrections=10)
            )
            self.assertTrue(decision.should_retrain)


class RegistryTests(unittest.TestCase):
    def test_register_and_get(self):
        from odia_ai.registry import ModelRegistry, ModelVersion, generate_version_id
        with tempfile.TemporaryDirectory() as td:
            registry = ModelRegistry(Path(td) / "registry")
            version = ModelVersion(
                version_id=generate_version_id(),
                base_model="meta-llama/Llama-3.1-8B-Instruct",
                model_path="/tmp/fake",
            )
            vid = registry.register(version)
            loaded = registry.get(vid)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.version_id, vid)  # type: ignore

    def test_promotion_demotes_prior(self):
        from odia_ai.registry import ModelRegistry, ModelVersion, generate_version_id
        with tempfile.TemporaryDirectory() as td:
            registry = ModelRegistry(Path(td) / "registry")
            v1 = ModelVersion(version_id=generate_version_id(), base_model="b", model_path="p1")
            v2 = ModelVersion(version_id=generate_version_id(), base_model="b", model_path="p2")
            registry.register(v1)
            registry.register(v2)
            registry.set_deployment_status(v1.version_id, "production")
            self.assertEqual(
                registry.production_version().version_id, v1.version_id  # type: ignore
            )
            registry.set_deployment_status(v2.version_id, "production")
            self.assertEqual(
                registry.production_version().version_id, v2.version_id  # type: ignore
            )
            v1_reloaded = registry.get(v1.version_id)
            self.assertEqual(v1_reloaded.deployment_status, "staging")  # type: ignore


class ConfigTests(unittest.TestCase):
    def test_config_round_trip(self):
        from odia_ai.configs import ODIAAIConfig, load_config, write_config
        with tempfile.TemporaryDirectory() as td:
            cfg = ODIAAIConfig()
            cfg.training.base_model = "custom/model"
            cfg.dataset.random_seed = 999
            path = Path(td) / "test_config.json"
            write_config(cfg, path)
            reloaded = load_config(path)
            self.assertEqual(reloaded.training.base_model, "custom/model")
            self.assertEqual(reloaded.dataset.random_seed, 999)

    def test_config_defaults(self):
        from odia_ai.configs import load_config
        cfg = load_config(None)
        self.assertTrue(cfg.training.base_model)
        self.assertEqual(cfg.dataset.holdout_validation_jurisdiction, "TCSO")
        self.assertEqual(cfg.dataset.holdout_test_jurisdiction, "Exeter")


if __name__ == "__main__":
    unittest.main(argv=sys.argv, verbosity=2)
