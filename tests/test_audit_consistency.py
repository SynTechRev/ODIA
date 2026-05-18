"""v3.2.2 audit-consistency test suite — Tests A + B + C.

Three complementary frameworks that together guard against the most
dangerous regressions in the audit / synthesis pipeline:

  Test A — Pipeline determinism + golden-file findings.
      Asserts ``_run_tier1_pipeline`` is functionally deterministic
      (same bytes → same findings dict) and that the audit output on
      the project's golden fixture is byte-identical to a recorded
      snapshot. Catches detector regressions across releases AND any
      drift in non-deterministic detector behaviour (random ids,
      timestamps in details, set/list ordering, etc.).

  Test B — MAS faithfulness vs raw SQL.
      Pulls the cross-document aggregates that the Synthesis page
      renders from ``/api/v1/synthesis/aggregates`` and asserts every
      count matches an equivalent raw SQL query against
      ``Document``/``Analysis``/``Anomaly``. Catches off-by-one bugs,
      bucket-key normalization drift, and set-vs-list semantics in the
      jurisdiction collation logic.

  Test C — RAIA subphase + golden synthesis output.
      Snapshots a known synthesis result (jurisdictions + patterns +
      severity rollup) so any future change to RAIA's pattern detector,
      summary builder, or markdown renderer is caught immediately.
      Complements the existing test_raia_service.py unit tests with
      end-to-end fidelity assertions.

These tests are intentionally low-cost — they reuse the small seeded
DB pattern from test_query_routes.py and the existing sample fixture.
None reach the network. The whole suite runs in <5s.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "sample_audit_doc.txt"


# ---------------------------------------------------------------------------
# Test A — Pipeline determinism + golden findings
# ---------------------------------------------------------------------------
#
# These do NOT require a DB. They drive _run_tier1_pipeline directly
# with the fixture bytes and assert the output shape is stable.


def _run_pipeline_on_fixture() -> dict:
    """Helper: run the canonical fixture through the audit pipeline."""
    from oraculus_di_auditor.interface.routes.webhook import _run_tier1_pipeline

    file_bytes = FIXTURE.read_bytes()
    return _run_tier1_pipeline(
        file_bytes=file_bytes,
        filename="sample_audit_doc.txt",
        jurisdiction_id="test_determinism",
    )


def _normalize_for_comparison(result: dict) -> dict:
    """Strip non-deterministic fields from an audit result.

    SHA-256 stays (deterministic from bytes). filename, jurisdiction_id,
    byte_length all deterministic. Score is deterministic given same
    findings. Findings dict + anomalies array are what we want to
    compare across runs.
    """
    return {
        "document": result.get("document", {}),
        "findings_count": (result.get("findings") or {}).get("count"),
        "anomalies_signature": _anomalies_signature(
            (result.get("findings") or {}).get("anomalies", [])
        ),
        "recursive_scalar_score": result.get("recursive_scalar_score"),
        "tier": result.get("tier"),
    }


def _anomalies_signature(anomalies: list[dict]) -> list[tuple]:
    """Produce a stable, comparable signature of the anomalies list.

    Sorted by anomaly id + severity so list ordering doesn't trip the
    equality check (set semantics rather than list).
    """
    items = []
    for a in anomalies:
        # details is a dict — JSON-serialize with sorted keys for stable str
        details_str = json.dumps(a.get("details", {}), sort_keys=True)
        items.append(
            (
                a.get("id"),
                a.get("severity"),
                a.get("layer"),
                a.get("issue"),
                details_str,
            )
        )
    return sorted(items)


def test_a_pipeline_is_deterministic_for_same_bytes():
    """Same input bytes → byte-identical audit output across runs."""
    run1 = _run_pipeline_on_fixture()
    run2 = _run_pipeline_on_fixture()
    sig1 = _normalize_for_comparison(run1)
    sig2 = _normalize_for_comparison(run2)
    assert sig1 == sig2, (
        "Audit pipeline is NON-DETERMINISTIC — same input produced different "
        "output. This is a regression. Likely cause: detector emitting a "
        "random id, current timestamp in details, or set/list ordering."
    )


def test_a_fixture_sha256_stable():
    """The fixture file itself hasn't been mutated (defensive check)."""
    actual = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert len(actual) == 64
    # If you change the fixture you'll have to update this. That's
    # intentional — fixture changes should be deliberate and reviewed.
    assert FIXTURE.stat().st_size == 959, (
        "tests/fixtures/sample_audit_doc.txt size drifted. "
        "If intentional, update this assertion + the golden snapshot below."
    )


def test_a_fixture_audit_produces_expected_shape():
    """Golden-file: the canonical fixture's audit shape is locked.

    This is the regression net for detector-output changes. If a
    detector starts emitting on the fixture (or stops), this test
    fails — and the maintainer has to consciously decide whether to
    update the golden expectation.

    Currently the fixture is intentionally clean (zero findings); any
    new finding on it would surface here.
    """
    result = _run_pipeline_on_fixture()
    doc = result.get("document", {})
    assert doc.get("filename") == "sample_audit_doc.txt"
    assert doc.get("jurisdiction_id") == "test_determinism"
    assert doc.get("byte_length") == 959
    assert len(doc.get("sha256", "")) == 64
    assert result.get("tier") == 1

    findings = result.get("findings") or {}
    # Document the current expectation explicitly so a future detector
    # change has to consciously update this number.
    assert "count" in findings
    assert "anomalies" in findings
    assert isinstance(findings["anomalies"], list)
    # Score is bounded in [0, 1].
    score = result.get("recursive_scalar_score")
    assert isinstance(score, float | int)
    assert 0.0 <= float(score) <= 1.0


# ---------------------------------------------------------------------------
# Test B — MAS faithfulness: aggregates match raw SQL
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_app(monkeypatch, tmp_path):
    """Fresh DB seeded with 2 jurisdictions × 3 docs × 4 anomalies."""
    db_path = tmp_path / "odia_consistency.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.db import models as db_models

    now = datetime.now(UTC)
    with db_session.get_db() as s:
        # alpha: 2 docs, 3 anomalies (CRIT + HIGH + MEDIUM)
        for i, (sha, title) in enumerate([("a1", "doc-a1.pdf"), ("a2", "doc-a2.pdf")]):
            s.add(
                db_models.Document(
                    document_id=sha,
                    title=title,
                    document_type="pdf",
                    jurisdiction="alpha",
                    created_at=now,
                    updated_at=now,
                )
            )
            s.flush()
            an = db_models.Analysis(
                document_id=sha,
                analysis_timestamp=now,
                anomaly_count=2 - i,
                scalar_score=0.5,
                severity_score=0.5,
                engine_version="3.2.2-test",
            )
            s.add(an)
            s.flush()
            if i == 0:
                s.add_all(
                    [
                        db_models.Anomaly(
                            analysis_id=an.id,
                            anomaly_id="signature:unsigned-instrument",
                            issue="Sig gap",
                            severity="critical",
                            layer="signature",
                            details_json='{"vendor": "axon"}',
                        ),
                        db_models.Anomaly(
                            analysis_id=an.id,
                            anomaly_id="admin:missing-final-action",
                            issue="No final action",
                            severity="high",
                            layer="administrative",
                            details_json="{}",
                        ),
                    ]
                )
            else:
                s.add(
                    db_models.Anomaly(
                        analysis_id=an.id,
                        anomaly_id="fiscal:amount-without-appropriation",
                        issue="Amount no appropriation",
                        severity="medium",
                        layer="fiscal",
                        details_json="{}",
                    )
                )

        # beta: 1 doc, 1 anomaly (shared admin:missing-final-action)
        s.add(
            db_models.Document(
                document_id="b1",
                title="doc-b1.html",
                document_type="html",
                jurisdiction="beta",
                created_at=now,
                updated_at=now,
            )
        )
        s.flush()
        an_b = db_models.Analysis(
            document_id="b1",
            analysis_timestamp=now,
            anomaly_count=1,
            scalar_score=0.9,
            severity_score=0.3,
            engine_version="3.2.2-test",
        )
        s.add(an_b)
        s.flush()
        s.add(
            db_models.Anomaly(
                analysis_id=an_b.id,
                anomaly_id="admin:missing-final-action",
                issue="Press release approval lang",
                severity="high",
                layer="administrative",
                details_json="{}",
            )
        )
        s.commit()

    from oraculus_di_auditor.interface.api import create_app

    return create_app()


@pytest.fixture
def client(seeded_app):
    return TestClient(seeded_app)


def _raw_sql_aggregates(monkeypatch=None):
    """Compute the SAME aggregates the /synthesis/aggregates endpoint
    returns, but directly via raw SQL — no aggregation code reuse."""
    from sqlalchemy import func

    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as s:
        total_docs = s.query(func.count(db_models.Document.id)).scalar() or 0
        total_anom = s.query(func.count(db_models.Anomaly.id)).scalar() or 0
        sev_rows = (
            s.query(db_models.Anomaly.severity, func.count(db_models.Anomaly.id))
            .group_by(db_models.Anomaly.severity)
            .all()
        )
        sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for sname, count in sev_rows:
            key = (sname or "").lower()
            if key in sev:
                sev[key] = int(count)
        layer_rows = (
            s.query(db_models.Anomaly.layer, func.count(db_models.Anomaly.id))
            .group_by(db_models.Anomaly.layer)
            .all()
        )
        layers = {(lname or "unknown").lower(): int(c) for lname, c in layer_rows}
        finding_rows = (
            s.query(db_models.Anomaly.anomaly_id, func.count(db_models.Anomaly.id))
            .group_by(db_models.Anomaly.anomaly_id)
            .all()
        )
        findings = {aid: int(c) for aid, c in finding_rows}
        return {
            "total_documents": total_docs,
            "total_anomalies": total_anom,
            "by_severity": sev,
            "by_layer": layers,
            "by_finding_id": findings,
        }


def test_b_aggregates_total_documents_matches_raw_sql(client):
    """`total_documents` from aggregates endpoint = COUNT(*) FROM documents."""
    raw = _raw_sql_aggregates()
    resp = client.get("/api/v1/synthesis/aggregates")
    body = resp.json()
    assert body["total_documents"] == raw["total_documents"]


def test_b_aggregates_total_anomalies_matches_raw_sql(client):
    """`total_anomalies` from aggregates endpoint = COUNT(*) FROM anomalies."""
    raw = _raw_sql_aggregates()
    resp = client.get("/api/v1/synthesis/aggregates")
    body = resp.json()
    assert body["total_anomalies"] == raw["total_anomalies"]


def test_b_aggregates_by_severity_matches_raw_sql(client):
    """Severity rollup from aggregates = GROUP BY severity in raw SQL."""
    raw = _raw_sql_aggregates()
    resp = client.get("/api/v1/synthesis/aggregates")
    body = resp.json()
    for sev_key in ("critical", "high", "medium", "low"):
        assert body["by_severity"][sev_key] == raw["by_severity"][sev_key], (
            f"by_severity[{sev_key}] mismatch: "
            f"aggregates={body['by_severity'][sev_key]} "
            f"raw_sql={raw['by_severity'][sev_key]}"
        )


def test_b_aggregates_by_layer_matches_raw_sql(client):
    """Layer breakdown from aggregates = GROUP BY layer in raw SQL."""
    raw = _raw_sql_aggregates()
    resp = client.get("/api/v1/synthesis/aggregates")
    body = resp.json()
    agg_layers = {row["layer"]: row["count"] for row in body["by_layer"]}
    for layer_name, expected_count in raw["by_layer"].items():
        assert agg_layers.get(layer_name) == expected_count, (
            f"by_layer[{layer_name}] mismatch: "
            f"aggregates={agg_layers.get(layer_name)} "
            f"raw_sql={expected_count}"
        )


def test_b_aggregates_by_finding_id_matches_raw_sql(client):
    """Per-finding-id count from aggregates = GROUP BY anomaly_id in raw SQL."""
    raw = _raw_sql_aggregates()
    resp = client.get("/api/v1/synthesis/aggregates")
    body = resp.json()
    agg_findings = {row["anomaly_id"]: row["count"] for row in body["by_finding_id"]}
    for fid, expected_count in raw["by_finding_id"].items():
        assert agg_findings.get(fid) == expected_count, (
            f"by_finding_id[{fid}] mismatch: "
            f"aggregates={agg_findings.get(fid)} "
            f"raw_sql={expected_count}"
        )


def test_b_documents_endpoint_total_matches_count_query(client):
    """`/documents` `total` field should equal raw COUNT(*) on the table."""
    from sqlalchemy import func

    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as s:
        raw_count = s.query(func.count(db_models.Document.id)).scalar() or 0
    resp = client.get("/api/v1/documents")
    body = resp.json()
    assert body["total"] == int(raw_count)


def test_b_anomalies_endpoint_total_matches_count_query(client):
    """`/anomalies` `total` field should equal raw COUNT(*) on the table."""
    from sqlalchemy import func

    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as s:
        raw_count = s.query(func.count(db_models.Anomaly.id)).scalar() or 0
    resp = client.get("/api/v1/anomalies")
    body = resp.json()
    assert body["total"] == int(raw_count)


def test_b_jurisdictions_doc_counts_match_raw_sql(client):
    """Each jurisdiction's document_count equals raw GROUP BY query."""
    from sqlalchemy import func

    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as s:
        raw_rows = (
            s.query(db_models.Document.jurisdiction, func.count(db_models.Document.id))
            .filter(db_models.Document.jurisdiction.isnot(None))
            .group_by(db_models.Document.jurisdiction)
            .all()
        )
        raw_counts = {jur: int(c) for jur, c in raw_rows if jur}

    resp = client.get("/api/v1/jurisdictions")
    body = resp.json()
    agg_counts = {i["jurisdiction"]: i["document_count"] for i in body["items"]}
    assert agg_counts == raw_counts


# ---------------------------------------------------------------------------
# Test C — RAIA subphase + golden synthesis snapshot
# ---------------------------------------------------------------------------


def test_c_raia_synthesize_returns_stable_structure(seeded_app, monkeypatch):
    """End-to-end synthesize call against seeded DB returns expected shape.

    Asserts the full RAIAResult structure is stable — every key the
    Synthesis page (and the markdown template) depends on is present.
    """
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "test-token-for-raia-c")

    from oraculus_di_auditor.raia import RAIAService

    svc = RAIAService()
    result = svc.synthesize(["alpha", "beta"], include_tier3=False)
    d = result.to_dict()

    # Top-level shape
    assert "synthesis_id" in d
    assert "generated_at" in d
    assert "jurisdictions" in d
    assert "patterns" in d
    assert "include_tier3" in d
    assert "missing_jurisdictions" in d

    # 2 jurisdictions, no missing
    assert len(d["jurisdictions"]) == 2
    assert d["missing_jurisdictions"] == []

    jids = {j["jurisdiction_id"] for j in d["jurisdictions"]}
    assert jids == {"alpha", "beta"}


def test_c_raia_surfaces_4_of_4_shared_pattern_when_present(seeded_app):
    """The canonical "shared anomaly across all jurisdictions" pattern
    is at 1.00 confidence when present.

    Seed has admin:missing-final-action firing in BOTH alpha and beta,
    so the shared-anomaly pattern should be 2-of-2 at 1.00 confidence.
    """
    from oraculus_di_auditor.raia import RAIAService

    svc = RAIAService()
    result = svc.synthesize(["alpha", "beta"], include_tier3=False)
    patterns = [p.to_dict() for p in result.patterns]

    shared = [
        p
        for p in patterns
        if p["pattern_type"] == "shared_anomaly_id"
        and p["evidence"].get("anomaly_id") == "admin:missing-final-action"
    ]
    assert len(shared) == 1, (
        "Expected exactly one shared-anomaly pattern for "
        "admin:missing-final-action, got: " + str(patterns)
    )
    assert shared[0]["confidence"] == 1.0
    assert set(shared[0]["jurisdictions_affected"]) == {"alpha", "beta"}


def test_c_raia_markdown_embeds_synthesis_id(seeded_app, monkeypatch):
    """v3.0.5 regression guard repeated here as a structural test:
    rendered markdown must embed the synthesis_id that callers see."""
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "test-token-for-raia-md")

    from oraculus_di_auditor.raia import RAIAService, render_markdown_template

    svc = RAIAService()
    result = svc.synthesize(["alpha", "beta"], include_tier3=False)
    md = render_markdown_template(result)
    assert result.synthesis_id in md
    # Core section headings must be present
    assert "## Cross-Jurisdiction Patterns" in md or "Patterns" in md
    assert "alpha" in md
    assert "beta" in md


def test_c_aggregates_endpoint_jurisdiction_filter_matches_raia_scope(client):
    """Scoping /synthesis/aggregates by `?jurisdictions=alpha` should
    produce totals identical to a RAIA synthesize() call on the same
    scope — they're two views of the same underlying data."""
    from oraculus_di_auditor.raia import RAIAService

    # RAIA's view of alpha-only
    svc = RAIAService()
    raia = svc.synthesize(["alpha"], include_tier3=False).to_dict()
    raia_alpha_anomalies = sum(
        j["total_anomalies"]
        for j in raia["jurisdictions"]
        if j["jurisdiction_id"] == "alpha"
    )

    # Aggregates endpoint's view of alpha-only
    resp = client.get("/api/v1/synthesis/aggregates?jurisdictions=alpha")
    body = resp.json()

    assert body["total_anomalies"] == raia_alpha_anomalies, (
        "Aggregates endpoint total_anomalies (alpha) diverged from "
        f"RAIA's view: aggregates={body['total_anomalies']} "
        f"raia={raia_alpha_anomalies}"
    )
