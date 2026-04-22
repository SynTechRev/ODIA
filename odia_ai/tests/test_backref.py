"""Tests for the back-reference extractor."""

from __future__ import annotations

import tempfile
from pathlib import Path

from odia_ai.backref import (
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


def test_detect_severity():
    assert detect_severity("This is a CRITICAL finding") == "CRITICAL"
    assert detect_severity("this is a high alert") == "HIGH"
    assert detect_severity("no severity here") is None


def test_detect_finding_category():
    assert detect_finding_category("relates to F-11 analysis") == "F-11"
    assert detect_finding_category("see F-3 below") == "F-3"
    assert detect_finding_category("F-99 is invalid") is None  # out of range
    assert detect_finding_category("no finding here") is None


def test_extract_vendors():
    text = "The Flock Safety and Axon Enterprise deployment was not authorized."
    vendors = extract_vendors(text)
    assert "Flock Safety" in vendors
    assert "Axon Enterprise" in vendors


def test_extract_statutes():
    text = "Universal noncompliance with SB 524 since January 1, 2026. CJIS missing."
    statutes = extract_statutes(text)
    assert "SB 524" in statutes
    assert "CJIS" in statutes


def test_extract_resolutions():
    text = "Resolution 2023-12 and Agreement 31448 were executed."
    resolutions = extract_resolutions(text)
    assert "2023-12" in resolutions
    assert "31448" in resolutions


def test_extract_dollars():
    text = "The contract totaled $18,824,577 plus $2,113,660.76 amendment."
    dollars = extract_dollars(text)
    assert any("$18,824,577" in d for d in dollars)


def test_extract_alerts_from_file():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_MAS)
        path = Path(f.name)

    try:
        alerts = extract_alerts_from_file(path)
        assert len(alerts) == 2

        ids = [a.alert_id for a in alerts]
        assert "EXE-138" in ids
        assert "EXE-139" in ids

        critical = next(a for a in alerts if a.alert_id == "EXE-138")
        assert critical.jurisdiction == "Exeter"
        assert critical.severity == "CRITICAL"
        assert critical.finding_category == "F-11"
        assert "Flock Safety" in critical.vendors_mentioned
        assert "SB 524" in critical.statutes_mentioned
        assert any("40,690" in d for d in critical.dollar_amounts)
    finally:
        path.unlink(missing_ok=True)


def test_compute_corpus_stats():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_MAS)
        path = Path(f.name)

    try:
        alerts = extract_alerts_from_file(path)
        stats = compute_corpus_stats(alerts)
        assert stats["total_alerts"] == 2
        assert stats["by_jurisdiction"]["Exeter"] == 2
        assert stats["by_severity"]["CRITICAL"] >= 1
    finally:
        path.unlink(missing_ok=True)


def test_write_jsonl(tmp_path: Path):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_MAS)
        path = Path(f.name)

    try:
        alerts = extract_alerts_from_file(path)
        out = tmp_path / "alerts.jsonl"
        count = write_jsonl(alerts, out)
        assert count == len(alerts)
        assert out.exists()
        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == count
    finally:
        path.unlink(missing_ok=True)
