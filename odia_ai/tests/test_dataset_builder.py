"""Tests for the training dataset builder."""

from __future__ import annotations

from pathlib import Path

from odia_ai.backref import ExtractedAlert
from odia_ai.training import (
    alert_to_training_example,
    assign_split,
    build_dataset,
    split_summary,
    write_dataset_splits,
)
from odia_ai.training.dataset_builder import (
    jurisdiction_transfer,
    negative_example,
)


def make_alert(alert_id: str, jurisdiction: str, severity: str = "HIGH") -> ExtractedAlert:
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


def test_alert_to_training_example():
    alert = make_alert("TUL-055", "Tulare", "CRITICAL")
    ex = alert_to_training_example(alert)

    assert ex.source_alert_id == "TUL-055"
    assert ex.jurisdiction == "Tulare"
    assert not ex.is_synthetic
    assert ex.input_text == alert.body
    assert "Flock Safety" in ex.output_json["vendors"]
    assert any(
        c["category"] == "F-2" for c in ex.output_json["anomaly_candidates"]
    )


def test_assign_split_holds_out_tcso_and_exeter():
    alert_tcso = make_alert("TCSO-010", "TCSO")
    alert_exeter = make_alert("EXE-100", "Exeter")
    alert_visalia = make_alert("VPD-200", "Visalia")

    ex_tcso = alert_to_training_example(alert_tcso)
    ex_exeter = alert_to_training_example(alert_exeter)
    ex_visalia = alert_to_training_example(alert_visalia)

    assert assign_split(ex_tcso) == "validation"
    assert assign_split(ex_exeter) == "test"
    assert assign_split(ex_visalia) == "train"


def test_jurisdiction_transfer_substitutes_names():
    alert = make_alert("VPD-100", "Visalia")
    ex = alert_to_training_example(alert)
    transferred = jurisdiction_transfer(ex, ("Visalia", "Ridgecrest"))

    assert transferred is not None
    assert transferred.is_synthetic
    assert transferred.jurisdiction == "Ridgecrest"
    assert "Visalia" not in transferred.input_text
    assert "Ridgecrest" in transferred.input_text


def test_jurisdiction_transfer_returns_none_when_no_match():
    alert = make_alert("VPD-100", "Visalia")
    ex = alert_to_training_example(alert)
    # Transfer pair where source doesn't appear in example text
    result = jurisdiction_transfer(ex, ("Porterville", "Lemoore"))
    assert result is None


def test_negative_example_has_empty_extractions():
    neg = negative_example("Routine council meeting minutes, no vendors.", "test_id")
    assert neg.is_synthetic
    assert neg.synthesis_method == "negative"
    assert neg.output_json["vendors"] == []
    assert neg.output_json["anomaly_candidates"] == []


def test_build_dataset_with_synthesis():
    alerts = [
        make_alert("VPD-001", "Visalia"),
        make_alert("PPD-002", "Porterville"),
        make_alert("TCSO-003", "TCSO"),
        make_alert("EXE-004", "Exeter"),
    ]
    examples = build_dataset(alerts, enable_jurisdiction_transfer=True)

    # We expect at least the 4 originals; synthetic transfers may add more
    assert len(examples) >= len(alerts)

    # Verify held-out split assignment
    by_j = {}
    for e in examples:
        by_j.setdefault(e.jurisdiction, []).append(e.split)

    assert "test" in by_j.get("Exeter", [])
    assert "validation" in by_j.get("TCSO", [])


def test_split_summary_structure():
    alerts = [make_alert(f"VPD-{i:03d}", "Visalia") for i in range(5)]
    examples = build_dataset(alerts, enable_jurisdiction_transfer=False)
    summary = split_summary(examples)

    assert "total" in summary
    assert "by_split" in summary
    assert "by_jurisdiction_split" in summary
    assert summary["total"] == len(examples)


def test_write_dataset_splits_alpaca(tmp_path: Path):
    alerts = [
        make_alert("VPD-001", "Visalia"),
        make_alert("TCSO-002", "TCSO"),
        make_alert("EXE-003", "Exeter"),
    ]
    examples = build_dataset(alerts, enable_jurisdiction_transfer=False)
    counts = write_dataset_splits(examples, tmp_path, format="alpaca")

    assert (tmp_path / "train.jsonl").exists()
    # validation + test hold-outs should also exist
    total_written = sum(counts.values())
    assert total_written == len(examples)

    # Each written line should be valid JSON with alpaca fields
    import json
    for split_file in tmp_path.glob("*.jsonl"):
        for line in split_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                assert "instruction" in rec
                assert "input" in rec
                assert "output" in rec
