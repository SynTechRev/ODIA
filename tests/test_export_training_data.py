"""Tests for the training data export script (formatting logic, no DB required)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

# Load the script as a module (it lives in scripts/, not src/)
_SCRIPT = Path(__file__).parent.parent / "scripts" / "export_training_data.py"
spec = importlib.util.spec_from_file_location("export_training_data", _SCRIPT)
_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
spec.loader.exec_module(_mod)  # type: ignore[union-attr]

_finding_output = _mod._finding_output
_explanation_output = _mod._explanation_output
_memorandum_output = _mod._memorandum_output
_truncate = _mod._truncate
_INSTR_FINDINGS = _mod._INSTR_FINDINGS
_INSTR_EXPLANATION = _mod._INSTR_EXPLANATION
_INSTR_MEMORANDUM = _mod._INSTR_MEMORANDUM


# ===========================================================================
# _finding_output
# ===========================================================================


def test_finding_output_contains_issue():
    out = _finding_output(
        "legal:l3:x",
        "CPRA catch-all without balancing",
        "high",
        "l3_exemption_misapplication",
        {},
    )
    assert "CPRA catch-all without balancing" in out


def test_finding_output_severity_uppercased():
    out = _finding_output("id", "issue", "medium", "l1", {})
    assert "SEVERITY: MEDIUM" in out


def test_finding_output_statute_present():
    out = _finding_output(
        "id", "issue", "high", "l3", {"statute": "Gov. Code § 7922.000"}
    )
    assert "Gov. Code § 7922.000" in out


def test_finding_output_regulation_present():
    out = _finding_output(
        "id", "issue", "high", "l5", {"regulation": "2 C.F.R. § 200.303"}
    )
    assert "2 C.F.R. § 200.303" in out


def test_finding_output_framework_present():
    out = _finding_output(
        "id",
        "issue",
        "medium",
        "l10",
        {"framework": "Mathews v. Eldridge (1976) 424 U.S. 319"},
    )
    assert "Mathews v. Eldridge" in out


def test_finding_output_explanation_present():
    out = _finding_output(
        "id", "issue", "low", "l1", {"detail": "SB 34 limits retention."}
    )
    assert "SB 34 limits retention" in out


def test_finding_output_missing_optional_fields():
    out = _finding_output("id", "issue", "low", "l1", {})
    assert "FINDING: issue" in out
    assert "STATUTE" not in out


# ===========================================================================
# _explanation_output
# ===========================================================================


def test_explanation_high_urgency():
    out = _explanation_output("ALPR data kept indefinitely", "high", {})
    assert "serious concern" in out.lower()


def test_explanation_medium_urgency():
    out = _explanation_output("AB 481 missing", "medium", {})
    assert "worth investigating" in out.lower()


def test_explanation_low_urgency():
    out = _explanation_output("Statute applies", "low", {})
    assert "informational" in out.lower()


def test_explanation_includes_detail():
    out = _explanation_output(
        "issue", "medium", {"detail": "SB 34 imposes 60-day limit."}
    )
    assert "SB 34" in out


def test_explanation_uses_relevance_fallback():
    out = _explanation_output("issue", "low", {"relevance": "Vehicle Code applies."})
    assert "Vehicle Code" in out


def test_explanation_no_detail_no_crash():
    out = _explanation_output("Some issue", "high", {})
    assert len(out) > 0


# ===========================================================================
# _memorandum_output
# ===========================================================================


def _mock_anomaly(issue, severity, details_json=None):
    a = MagicMock()
    a.issue = issue
    a.severity = severity
    return a


def test_memorandum_output_contains_re_line():
    anomaly = _mock_anomaly("CPRA issue", "high")
    out = _memorandum_output("ALPR Policy 2024", "Anytown PD", [(anomaly, {})])
    assert "ALPR Policy 2024" in out
    assert "Anytown PD" in out


def test_memorandum_output_overview_counts():
    high = _mock_anomaly("high issue", "high")
    medium = _mock_anomaly("medium issue", "medium")
    low = _mock_anomaly("low issue", "low")
    out = _memorandum_output("Doc", "Agency", [(high, {}), (medium, {}), (low, {})])
    assert "3" in out
    assert "1 high" in out


def test_memorandum_output_conclusion_urgent_for_high():
    a = _mock_anomaly("serious issue", "high")
    out = _memorandum_output("Doc", "Agency", [(a, {})])
    assert "legal counsel" in out.lower() or "immediate" in out.lower()


def test_memorandum_output_conclusion_soft_for_low_only():
    a = _mock_anomaly("informational", "low")
    out = _memorandum_output("Doc", "Agency", [(a, {})])
    assert "immediate" not in out.lower() or "no immediate" in out.lower()


def test_memorandum_statute_in_output():
    a = _mock_anomaly("issue", "high")
    out = _memorandum_output(
        "Doc", "Agency", [(a, {"statute": "Gov. Code § 7922.000"})]
    )
    assert "Gov. Code § 7922.000" in out


# ===========================================================================
# _truncate
# ===========================================================================


def test_truncate_short_text_unchanged():
    text = "Short text"
    assert _truncate(text, 100) == text


def test_truncate_long_text_truncated():
    text = "word " * 1000
    result = _truncate(text, 50)
    assert len(result) <= 55  # small buffer for "[...]"


def test_truncate_appends_marker():
    text = "word " * 100
    result = _truncate(text, 20)
    assert "[...]" in result


def test_truncate_exact_length_not_truncated():
    text = "a" * 100
    assert _truncate(text, 100) == text


# ===========================================================================
# Instruction constants
# ===========================================================================


def test_findings_instruction_mentions_legal():
    assert "legal" in _INSTR_FINDINGS.lower()


def test_explanation_instruction_mentions_plain_language():
    assert "plain" in _INSTR_EXPLANATION.lower()


def test_memorandum_instruction_mentions_memorandum():
    assert "memorandum" in _INSTR_MEMORANDUM.lower()
