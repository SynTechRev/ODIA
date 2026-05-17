"""Tests for the R.A.I.A. synthesis service (v2.7.1 C5.2).

Three scopes:
  1. schemas — dataclass round-trip (``to_dict`` contract).
  2. patterns — pure-function cross-jurisdiction detection on
     hand-built ``JurisdictionSummary`` fixtures (no DB).
  3. service — end-to-end synthesize() against a fresh SQLite DB with
     seeded Document/Analysis/Anomaly rows; also covers the graceful-
     degrade paths (no data / uninitialised DB).
"""

from __future__ import annotations

import importlib
import json

import pytest

pytest.importorskip("sqlalchemy")

from oraculus_di_auditor.raia.patterns import detect_patterns  # noqa: E402
from oraculus_di_auditor.raia.raia_service import RAIAService  # noqa: E402
from oraculus_di_auditor.raia.schemas import (  # noqa: E402
    AnomalyRow,
    CrossJurisdictionPattern,
    JurisdictionSummary,
    RAIAResult,
)
from oraculus_di_auditor.raia.synthesis_report import render_markdown  # noqa: E402

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def test_anomaly_row_roundtrip():
    a = AnomalyRow(
        anomaly_id="fiscal:missing-provenance-hash",
        issue="No SHA-256 found",
        severity="high",
        layer="fiscal",
        details={"vendor": "Axon"},
    )
    d = a.to_dict()
    assert d["anomaly_id"] == "fiscal:missing-provenance-hash"
    assert d["severity"] == "high"
    assert d["details"] == {"vendor": "Axon"}


def test_jurisdiction_summary_empty_has_sensible_defaults():
    s = JurisdictionSummary(jurisdiction_id="x")
    d = s.to_dict()
    assert d["jurisdiction_id"] == "x"
    assert d["document_count"] == 0
    assert d["scalar_score_avg"] == 0.0
    assert d["severity_counts"] == {}
    assert d["top_anomalies"] == []


def test_raia_result_to_dict_shape():
    result = RAIAResult(
        synthesis_id="abc123",
        generated_at="2026-04-22T00:00:00+00:00",
        jurisdictions=[JurisdictionSummary(jurisdiction_id="a", document_count=1)],
        patterns=[
            CrossJurisdictionPattern(
                pattern_id="shared-anomaly:foo",
                pattern_type="shared_anomaly_id",
                jurisdictions_affected=["a", "b"],
                confidence=0.5,
                description="example",
            )
        ],
        include_tier3=False,
        missing_jurisdictions=["z"],
    )
    d = result.to_dict()
    assert d["synthesis_id"] == "abc123"
    assert d["missing_jurisdictions"] == ["z"]
    assert d["patterns"][0]["confidence"] == 0.5
    assert d["jurisdictions"][0]["document_count"] == 1


# ---------------------------------------------------------------------------
# Patterns (no DB)
# ---------------------------------------------------------------------------


def _summary(
    jid: str,
    *,
    docs: int = 1,
    layer_counts: dict[str, int] | None = None,
    anomalies: list[AnomalyRow] | None = None,
) -> JurisdictionSummary:
    return JurisdictionSummary(
        jurisdiction_id=jid,
        document_count=docs,
        analysis_count=docs,
        total_anomalies=sum((layer_counts or {}).values()),
        layer_counts=layer_counts or {},
        top_anomalies=anomalies or [],
    )


def test_detect_patterns_requires_two_populated_jurisdictions():
    assert detect_patterns([_summary("a", docs=1)]) == []
    # Two jurisdictions but only one has any documents
    assert (
        detect_patterns(
            [
                _summary("a", docs=1, layer_counts={"fiscal": 1}),
                JurisdictionSummary(jurisdiction_id="b"),
            ]
        )
        == []
    )


def test_shared_anomaly_id_pattern():
    a1 = AnomalyRow(
        anomaly_id="surveillance:alpr-no-council-approval",
        issue="Flock ALPR deployed without council vote",
        severity="high",
        layer="surveillance",
    )
    a2 = AnomalyRow(
        anomaly_id="surveillance:alpr-no-council-approval",
        issue="Flock ALPR installed with no open hearing",
        severity="high",
        layer="surveillance",
    )
    summaries = [
        _summary("woodlake", anomalies=[a1], layer_counts={"surveillance": 1}),
        _summary("lindsay", anomalies=[a2], layer_counts={"surveillance": 1}),
    ]
    patterns = detect_patterns(summaries)
    shared = [p for p in patterns if p.pattern_type == "shared_anomaly_id"]
    assert len(shared) == 1
    assert shared[0].jurisdictions_affected == ["lindsay", "woodlake"]
    assert shared[0].confidence == 1.0


def test_vendor_convergence_pattern():
    a1 = AnomalyRow(
        anomaly_id="x:foo",
        issue="Flock Safety camera deployed",
        severity="medium",
        layer="surveillance",
    )
    a2 = AnomalyRow(
        anomaly_id="x:bar",
        issue="Pole-mounted flock unit documented",
        severity="low",
        layer="governance_gap",
    )
    a3 = AnomalyRow(
        anomaly_id="x:baz",
        issue="Routine traffic study — no vendor equipment",
        severity="low",
        layer="fiscal",
    )
    summaries = [
        _summary("a", anomalies=[a1], layer_counts={"surveillance": 1}),
        _summary("b", anomalies=[a2], layer_counts={"governance_gap": 1}),
        _summary("c", anomalies=[a3], layer_counts={"fiscal": 1}),
    ]
    patterns = detect_patterns(summaries)
    vendor = [p for p in patterns if p.pattern_type == "vendor_convergence"]
    flock = [p for p in vendor if "flock" in p.pattern_id]
    assert flock, "Expected a Flock vendor convergence pattern across a + b"
    assert set(flock[0].jurisdictions_affected) == {"a", "b"}


def test_shared_layer_spike_pattern():
    summaries = [
        _summary("a", docs=5, layer_counts={"surveillance": 5, "fiscal": 1}),
        _summary("b", docs=5, layer_counts={"surveillance": 4, "governance_gap": 1}),
        _summary("c", docs=5, layer_counts={"fiscal": 3, "surveillance": 1}),
    ]
    patterns = detect_patterns(summaries)
    layer_spikes = [p for p in patterns if p.pattern_type == "shared_layer_spike"]
    surv = [p for p in layer_spikes if p.pattern_id.endswith("surveillance")]
    assert surv, "Expected surveillance layer spike across a + b"
    assert set(surv[0].jurisdictions_affected) == {"a", "b"}


# ---------------------------------------------------------------------------
# v3.0.5 — pattern detection over full anomaly set (not just top-N)
# ---------------------------------------------------------------------------


def test_shared_anomaly_surfaces_outside_top_n_via_all_anomalies():
    """v3.0.5 regression guard.

    Pre-v3.0.5, ``_shared_anomaly_ids`` iterated only ``top_anomalies``.
    If a shared finding ID lived past each jurisdiction's display cap
    (top_anomalies defaulted to 10 in RAIAService), it was invisible to
    cross-jurisdiction pattern detection. Observed live against
    Visalia+Porterville: 6 of 8 actually-shared finding IDs were missed
    because Visalia's top-10 was dominated by CRITICAL signature finds
    and high-frequency admin:missing-final-action. v3.0.5 makes the
    pattern detectors consume ``all_anomalies`` instead.
    """
    top_only_high = AnomalyRow(
        anomaly_id="signature:unsigned-instrument",
        issue="Signature gap detected",
        severity="critical",
        layer="signature",
    )
    buried_in_all = AnomalyRow(
        anomaly_id="procurement:auto-renewal-clause",
        issue="Vendor contract auto-renews",
        severity="high",
        layer="procurement",
    )
    s1 = JurisdictionSummary(
        jurisdiction_id="visalia",
        document_count=10,
        analysis_count=10,
        total_anomalies=2,
        layer_counts={"signature": 1, "procurement": 1},
        # top_anomalies cap simulated — only the CRITICAL one made the cut
        top_anomalies=[top_only_high],
        # but all_anomalies has both (the buried one too)
        all_anomalies=[top_only_high, buried_in_all],
    )
    s2 = JurisdictionSummary(
        jurisdiction_id="porterville",
        document_count=8,
        analysis_count=8,
        total_anomalies=2,
        layer_counts={"signature": 1, "procurement": 1},
        top_anomalies=[top_only_high],
        all_anomalies=[top_only_high, buried_in_all],
    )
    patterns = detect_patterns([s1, s2])
    shared = [p for p in patterns if p.pattern_type == "shared_anomaly_id"]
    shared_ids = {p.evidence.get("anomaly_id") for p in shared}
    # The CRITICAL one was always going to surface (it's in top_anomalies).
    # The HIGH `procurement:auto-renewal-clause` would have been missed
    # pre-v3.0.5; now it must appear too.
    assert "signature:unsigned-instrument" in shared_ids
    assert "procurement:auto-renewal-clause" in shared_ids, (
        "v3.0.5 regression: shared anomaly outside top_anomalies must "
        "still surface via all_anomalies"
    )


def test_vendor_convergence_surfaces_outside_top_n_via_all_anomalies():
    """v3.0.5 regression guard for vendor convergence.

    Vendor mentions (Axon, Flock, etc.) typically appear in lower-
    severity findings that sit below CRITICAL/HIGH structural defects.
    Pre-v3.0.5, those mentions were invisible to vendor-convergence
    detection because they didn't make the top_anomalies cut.
    """
    structural_only = AnomalyRow(
        anomaly_id="admin:missing-final-action",
        issue="Final action field is blank",
        severity="high",
        layer="administrative",
    )
    axon_buried = AnomalyRow(
        anomaly_id="surveillance:vendor-detected:axon-enterprise",
        issue="Axon Enterprise vendor mention detected",
        severity="low",
        layer="surveillance",
    )
    s1 = JurisdictionSummary(
        jurisdiction_id="a",
        document_count=1,
        analysis_count=1,
        layer_counts={"administrative": 1, "surveillance": 1},
        top_anomalies=[structural_only],
        all_anomalies=[structural_only, axon_buried],
    )
    s2 = JurisdictionSummary(
        jurisdiction_id="b",
        document_count=1,
        analysis_count=1,
        layer_counts={"administrative": 1, "surveillance": 1},
        top_anomalies=[structural_only],
        all_anomalies=[structural_only, axon_buried],
    )
    patterns = detect_patterns([s1, s2])
    vendor = [p for p in patterns if p.pattern_type == "vendor_convergence"]
    axon = [p for p in vendor if "axon" in p.pattern_id]
    assert axon, (
        "v3.0.5 regression: vendor mention outside top_anomalies must "
        "still surface via all_anomalies"
    )
    assert set(axon[0].jurisdictions_affected) == {"a", "b"}


def test_pattern_detection_falls_back_to_top_anomalies_when_all_empty():
    """Backward-compat: legacy callers building summaries without
    ``all_anomalies`` (e.g. hand-built fixtures from pre-v3.0.5 tests)
    still get pattern detection over ``top_anomalies``.
    """
    a = AnomalyRow(
        anomaly_id="surveillance:alpr-no-council-approval",
        issue="ALPR no council vote",
        severity="high",
        layer="surveillance",
    )
    # NOTE: only top_anomalies populated; all_anomalies left as default []
    s1 = JurisdictionSummary(
        jurisdiction_id="a",
        document_count=1,
        analysis_count=1,
        layer_counts={"surveillance": 1},
        top_anomalies=[a],
    )
    s2 = JurisdictionSummary(
        jurisdiction_id="b",
        document_count=1,
        analysis_count=1,
        layer_counts={"surveillance": 1},
        top_anomalies=[a],
    )
    patterns = detect_patterns([s1, s2])
    shared = [p for p in patterns if p.pattern_type == "shared_anomaly_id"]
    assert len(shared) == 1
    assert shared[0].evidence["anomaly_id"] == "surveillance:alpr-no-council-approval"


# ---------------------------------------------------------------------------
# Service (DB-backed)
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_db(monkeypatch, tmp_path):
    """Fresh SQLite DB + seeded rows across three jurisdictions.

    Seeds:
      - woodlake: 2 docs, 2 analyses, 3 anomalies (surveillance + fiscal)
      - lindsay:  1 doc,  1 analysis, 2 anomalies (surveillance + fiscal)
      - porterville: 1 doc, 1 analysis, 1 anomaly (governance_gap)

    Shared anomaly id `surveillance:alpr-flock` across woodlake + lindsay
    → should surface as a shared_anomaly_id pattern.
    """
    db_path = tmp_path / "odia_raia_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.db import models as db_models

    def _doc(sha: str, jurisdiction: str, title: str) -> db_models.Document:
        return db_models.Document(
            document_id=sha,
            title=title,
            document_type="txt",
            jurisdiction=jurisdiction,
        )

    def _analysis(sha: str, score: float, count: int) -> db_models.Analysis:
        return db_models.Analysis(
            document_id=sha,
            anomaly_count=count,
            scalar_score=score,
            engine_version="2.7.1",
        )

    def _anomaly(
        aid: int,
        anomaly_id: str,
        issue: str,
        severity: str,
        layer: str,
        details: dict | None = None,
    ) -> db_models.Anomaly:
        return db_models.Anomaly(
            analysis_id=aid,
            anomaly_id=anomaly_id,
            issue=issue,
            severity=severity,
            layer=layer,
            details_json=json.dumps(details or {}),
        )

    with db_session.get_db() as session:
        session.add_all(
            [
                _doc("a" * 64, "woodlake", "staff-report-001.pdf"),
                _doc("b" * 64, "woodlake", "staff-report-002.pdf"),
                _doc("c" * 64, "lindsay", "staff-report-003.pdf"),
                _doc("d" * 64, "porterville", "staff-report-004.pdf"),
            ]
        )
        session.flush()

        wa1 = _analysis("a" * 64, 0.72, 2)
        wa2 = _analysis("b" * 64, 0.66, 1)
        la1 = _analysis("c" * 64, 0.81, 2)
        pa1 = _analysis("d" * 64, 0.50, 1)
        session.add_all([wa1, wa2, la1, pa1])
        session.flush()

        session.add_all(
            [
                _anomaly(
                    wa1.id,
                    "surveillance:alpr-flock",
                    "Flock Safety ALPR deployed without council vote",
                    "high",
                    "surveillance",
                ),
                _anomaly(
                    wa1.id,
                    "fiscal:missing-provenance-hash",
                    "Staff report lacks SHA-256 provenance",
                    "medium",
                    "fiscal",
                ),
                _anomaly(
                    wa2.id,
                    "surveillance:alpr-flock",
                    "Flock duplicate finding",
                    "high",
                    "surveillance",
                ),
                _anomaly(
                    la1.id,
                    "surveillance:alpr-flock",
                    "Flock ALPR without public hearing in Lindsay",
                    "high",
                    "surveillance",
                ),
                _anomaly(
                    la1.id,
                    "fiscal:amendment-chain-broken",
                    "Amendment 3 references missing amendment 2",
                    "medium",
                    "fiscal",
                ),
                _anomaly(
                    pa1.id,
                    "governance_gap:retention-missing",
                    "No data retention schedule attached",
                    "medium",
                    "governance_gap",
                ),
            ]
        )

    yield db_session


def test_synthesize_rejects_empty_jurisdictions(seeded_db):
    svc = RAIAService()
    with pytest.raises(ValueError):
        svc.synthesize([])


def test_synthesize_builds_per_jurisdiction_summaries(seeded_db):
    svc = RAIAService()
    result = svc.synthesize(["woodlake", "lindsay", "porterville"])

    assert len(result.jurisdictions) == 3
    by_id = {s.jurisdiction_id: s for s in result.jurisdictions}
    assert by_id["woodlake"].document_count == 2
    assert by_id["woodlake"].analysis_count == 2
    assert by_id["woodlake"].total_anomalies == 3
    # Average of 0.72 + 0.66 = 0.69
    assert 0.68 < by_id["woodlake"].scalar_score_avg < 0.70
    assert by_id["lindsay"].total_anomalies == 2
    assert by_id["porterville"].total_anomalies == 1
    # Top anomaly for porterville is its governance_gap row
    assert by_id["porterville"].top_anomalies[0].layer == "governance_gap"


def test_synthesize_flags_shared_anomaly_across_jurisdictions(seeded_db):
    svc = RAIAService()
    result = svc.synthesize(["woodlake", "lindsay", "porterville"])

    shared = [p for p in result.patterns if p.pattern_type == "shared_anomaly_id"]
    alpr = [p for p in shared if "alpr-flock" in p.pattern_id]
    assert alpr, "Expected surveillance:alpr-flock to be flagged across jurisdictions"
    assert set(alpr[0].jurisdictions_affected) == {"woodlake", "lindsay"}
    assert alpr[0].confidence == pytest.approx(2 / 3, rel=0.01)


def test_synthesize_flags_vendor_convergence(seeded_db):
    svc = RAIAService()
    result = svc.synthesize(["woodlake", "lindsay", "porterville"])

    vendor = [p for p in result.patterns if p.pattern_type == "vendor_convergence"]
    flock = [p for p in vendor if "flock" in p.pattern_id]
    assert flock, "Expected Flock vendor convergence"
    assert set(flock[0].jurisdictions_affected) == {"woodlake", "lindsay"}


def test_synthesize_tracks_missing_jurisdictions(seeded_db):
    svc = RAIAService()
    result = svc.synthesize(["woodlake", "never_heard_of_this_city"])

    assert "never_heard_of_this_city" in result.missing_jurisdictions
    # Summaries still includes the missing one, with zero counts
    by_id = {s.jurisdiction_id: s for s in result.jurisdictions}
    assert by_id["never_heard_of_this_city"].document_count == 0


def test_synthesize_include_tier3_emits_stub_notes(seeded_db):
    svc = RAIAService()
    result = svc.synthesize(["woodlake", "lindsay"], include_tier3=True)
    assert result.include_tier3 is True
    assert result.tier3_notes is not None
    assert result.tier3_notes["status"] == "stub"
    assert "engines_planned" in result.tier3_notes


def test_synthesize_caps_top_anomalies(seeded_db):
    svc = RAIAService(top_anomalies_per_jurisdiction=1)
    result = svc.synthesize(["woodlake"])
    summary = next(s for s in result.jurisdictions if s.jurisdiction_id == "woodlake")
    # Still counts all three in total, but only keeps 1 in top_anomalies
    assert summary.total_anomalies == 3
    assert len(summary.top_anomalies) == 1
    assert summary.top_anomalies[0].severity == "high"


def test_render_markdown_contains_key_sections(seeded_db):
    svc = RAIAService()
    result = svc.synthesize(["woodlake", "lindsay"])
    md = render_markdown(result)

    assert "R.A.I.A." in md
    assert "woodlake" in md
    assert "lindsay" in md
    assert "Per-Jurisdiction Summary" in md
    assert "Cross-Jurisdiction Patterns" in md
    # Shared anomaly pattern should appear in the rendered body
    assert "shared_anomaly_id" in md or "alpr" in md
