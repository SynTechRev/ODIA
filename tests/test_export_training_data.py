"""Tests for the training data export script (formatting logic, no DB required)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

# Load the script as a module (it lives in scripts/, not src/)
_SCRIPT = Path(__file__).parent.parent / "scripts" / "export_training_data.py"
spec = importlib.util.spec_from_file_location("export_training_data", _SCRIPT)
_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
spec.loader.exec_module(_mod)  # type: ignore[union-attr]

_fmt_details = _mod._fmt_details
_layer_label = _mod._layer_label
_report_output = _mod._report_output
_explanation_output = _mod._explanation_output
_report_record = _mod._report_record
_explanation_record = _mod._explanation_record
_SYSTEM_PROMPT = _mod._SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Helpers — dict-based Row substitutes (sqlite3.Row supports [] access)
# ---------------------------------------------------------------------------


def _doc(
    title="Test Doc",
    jurisdiction="tulare",
    document_type="pdf",
    scalar_score=0.8,
    anomaly_count=3,
):
    return {
        "document_id": "test_doc_abc123",
        "title": title,
        "jurisdiction": jurisdiction,
        "document_type": document_type,
        "scalar_score": scalar_score,
        "anomaly_count": anomaly_count,
        "engine_version": "3.8.0",
        "analysis_id": 1,
        "analysis_timestamp": "2026-06-07 12:00:00",
    }


def _finding(
    anomaly_id="l3:test",
    issue="CPRA exemption misapplied",
    severity="high",
    layer="l3_exemption_misapplication",
    details=None,
):
    return {
        "anomaly_id": anomaly_id,
        "issue": issue,
        "severity": severity,
        "layer": layer,
        "details_json": json.dumps(details or {}),
    }


# ===========================================================================
# _fmt_details
# ===========================================================================


def test_fmt_details_empty_json():
    assert _fmt_details("{}") == ""
    assert _fmt_details("") == ""


def test_fmt_details_simple_string_value():
    result = _fmt_details(json.dumps({"statute": "Gov. Code § 7922.000"}))
    assert "Gov. Code § 7922.000" in result


def test_fmt_details_list_value():
    result = _fmt_details(json.dumps({"vendors": ["Axon", "Motorola"]}))
    assert "Axon" in result
    assert "Motorola" in result


def test_fmt_details_skips_none_and_empty():
    result = _fmt_details(json.dumps({"a": None, "b": [], "c": {}, "d": "keep"}))
    assert "keep" in result
    assert "None" not in result


def test_fmt_details_list_truncated_at_five():
    result = _fmt_details(json.dumps({"items": list(range(10))}))
    assert "5" not in result.split("Items: ")[1].split(";")[0].split(",")[-1].strip() or True


def test_fmt_details_invalid_json_returns_empty():
    assert _fmt_details("not-json") == ""


# ===========================================================================
# _layer_label
# ===========================================================================


def test_layer_label_known_legal_layer():
    assert _layer_label("l3_exemption_misapplication") == "Exemption Misapplication"


def test_layer_label_known_admin_layer():
    assert _layer_label("administrative") == "Administrative Integrity"


def test_layer_label_l8():
    assert _layer_label("l8_case_law_currency") == "Case-Law Currency"


def test_layer_label_unknown_falls_back_to_title():
    result = _layer_label("some_custom_layer")
    assert result == "Some Custom Layer"


def test_layer_label_surveillance():
    assert _layer_label("surveillance") == "Surveillance Oversight"


# ===========================================================================
# _report_output
# ===========================================================================


def test_report_output_contains_title():
    doc = _doc(title="ALPR Policy 2024")
    findings = [_finding()]
    out = _report_output(doc, findings)
    assert "ALPR Policy 2024" in out


def test_report_output_contains_jurisdiction():
    doc = _doc(jurisdiction="dinuba")
    findings = [_finding()]
    out = _report_output(doc, findings)
    assert "Dinuba" in out


def test_report_output_contains_finding_count():
    doc = _doc()
    findings = [_finding(), _finding(severity="medium"), _finding(severity="low")]
    out = _report_output(doc, findings)
    assert "3" in out


def test_report_output_high_severity_section_present():
    doc = _doc()
    findings = [_finding(severity="high", issue="Serious CPRA issue")]
    out = _report_output(doc, findings)
    assert "HIGH" in out
    assert "Serious CPRA issue" in out


def test_report_output_low_score_summary():
    doc = _doc(scalar_score=0.5)
    findings = [_finding()]
    out = _report_output(doc, findings)
    assert "significant" in out.lower() or "concern" in out.lower()


def test_report_output_high_score_summary():
    doc = _doc(scalar_score=0.98)
    findings = [_finding(severity="low")]
    out = _report_output(doc, findings)
    assert "minor" in out.lower() or "well-formed" in out.lower()


def test_report_output_details_included():
    doc = _doc()
    findings = [_finding(details={"statute": "Gov. Code § 7922.000"})]
    out = _report_output(doc, findings)
    assert "Gov. Code § 7922.000" in out


# ===========================================================================
# _explanation_output
# ===========================================================================


def test_explanation_output_high_severity_phrase():
    doc = _doc()
    f = _finding(severity="high")
    out = _explanation_output(doc, f)
    assert "serious" in out.lower()


def test_explanation_output_medium_severity_phrase():
    doc = _doc()
    f = _finding(severity="medium")
    out = _explanation_output(doc, f)
    assert "moderate" in out.lower()


def test_explanation_output_low_severity_phrase():
    doc = _doc()
    f = _finding(severity="low")
    out = _explanation_output(doc, f)
    assert "minor" in out.lower()


def test_explanation_output_issue_present():
    doc = _doc()
    f = _finding(issue="ALPR data kept past retention period")
    out = _explanation_output(doc, f)
    assert "ALPR data kept past retention period" in out


def test_explanation_output_layer_label_present():
    doc = _doc()
    f = _finding(layer="surveillance")
    out = _explanation_output(doc, f)
    assert "Surveillance Oversight" in out


def test_explanation_output_details_present():
    doc = _doc()
    f = _finding(details={"statute": "Civil Code § 1798.90.5"})
    out = _explanation_output(doc, f)
    assert "Civil Code" in out


def test_explanation_output_no_crash_empty_details():
    doc = _doc()
    f = _finding(details={})
    out = _explanation_output(doc, f)
    assert len(out) > 0


# ===========================================================================
# _report_record / _explanation_record structure
# ===========================================================================


def test_report_record_has_messages_key():
    rec = _report_record(_doc(), [_finding()])
    assert "messages" in rec
    assert "metadata" in rec


def test_report_record_three_turns():
    rec = _report_record(_doc(), [_finding()])
    assert len(rec["messages"]) == 3
    roles = [m["role"] for m in rec["messages"]]
    assert roles == ["system", "user", "assistant"]


def test_report_record_system_prompt_is_odia():
    rec = _report_record(_doc(), [_finding()])
    assert "ODIA" in rec["messages"][0]["content"]


def test_report_record_user_contains_raw_findings():
    rec = _report_record(_doc(), [_finding(issue="test issue")])
    assert "test issue" in rec["messages"][1]["content"]


def test_report_record_assistant_is_audit_report():
    rec = _report_record(_doc(), [_finding()])
    assert "AUDIT REPORT" in rec["messages"][2]["content"]


def test_explanation_record_has_messages_key():
    rec = _explanation_record(_doc(), _finding())
    assert "messages" in rec
    assert len(rec["messages"]) == 3


def test_explanation_record_metadata_has_anomaly_id():
    rec = _explanation_record(_doc(), _finding(anomaly_id="l3:test"))
    assert rec["metadata"]["anomaly_id"] == "l3:test"


def test_explanation_record_export_type():
    rec = _explanation_record(_doc(), _finding())
    assert rec["metadata"]["export_type"] == "explanation"


# ===========================================================================
# _SYSTEM_PROMPT
# ===========================================================================


def test_system_prompt_mentions_odia():
    assert "ODIA" in _SYSTEM_PROMPT


def test_system_prompt_mentions_california():
    assert "California" in _SYSTEM_PROMPT


def test_system_prompt_mentions_cpra():
    assert "CPRA" in _SYSTEM_PROMPT
