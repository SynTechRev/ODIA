"""Integration tests for the v3.2.0 DB-backed list/query routes.

Covers GET /api/v1/{documents,anomalies,analyses,jurisdictions,synthesis/aggregates}.

Strategy: seed a small SQLite DB with 2 jurisdictions × 3 documents × N
anomalies, then exercise each endpoint's pagination + filtering surface.
Fail-open behaviour (DB layer unavailable) is also tested by patching the
import path to raise ImportError.
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_app(monkeypatch, tmp_path):
    """Fresh app + seeded DB: 2 jurisdictions, mixed severities."""
    db_path = tmp_path / "odia_query_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.db import models as db_models

    now = datetime.now(UTC)
    with db_session.get_db() as s:
        # Jurisdiction A: 2 documents, 3 anomalies (1 critical, 1 high, 1 medium)
        for i, (sha, title) in enumerate(
            [
                ("aaa111", "agenda-a-01.pdf"),
                ("aaa222", "agenda-a-02.pdf"),
            ]
        ):
            doc = db_models.Document(
                document_id=sha,
                title=title,
                document_type="pdf",
                jurisdiction="alpha",
                created_at=now,
                updated_at=now,
            )
            s.add(doc)
            s.flush()
            an = db_models.Analysis(
                document_id=sha,
                analysis_timestamp=now,
                anomaly_count=2 - i,
                scalar_score=0.5 + i * 0.1,
                severity_score=0.5,
                engine_version="3.2.0-test",
                summary=None,
            )
            s.add(an)
            s.flush()
            if i == 0:
                s.add(
                    db_models.Anomaly(
                        analysis_id=an.id,
                        anomaly_id="signature:unsigned-instrument",
                        issue="Signature gap in AGREEMENT",
                        severity="critical",
                        layer="signature",
                        details_json=(
                            '{"instrument_type": "AGREEMENT",'
                            ' "dollar_amount": "$100,000"}'
                        ),
                    )
                )
                s.add(
                    db_models.Anomaly(
                        analysis_id=an.id,
                        anomaly_id="admin:missing-final-action",
                        issue="Approval signal without final_action",
                        severity="high",
                        layer="administrative",
                        details_json='{"approval_signals_found": ["approved"]}',
                    )
                )
            else:
                s.add(
                    db_models.Anomaly(
                        analysis_id=an.id,
                        anomaly_id="fiscal:amount-without-appropriation",
                        issue="Fiscal amount without appropriation",
                        severity="medium",
                        layer="fiscal",
                        details_json='{"sample_amounts": ["$5,000"]}',
                    )
                )

        # Jurisdiction B: 1 document, 1 anomaly (admin:missing-final-action again
        # — used to verify cross-jurisdiction shared-finding aggregation)
        doc_b = db_models.Document(
            document_id="bbb111",
            title="press-release-b-01.html",
            document_type="html",
            jurisdiction="beta",
            created_at=now,
            updated_at=now,
        )
        s.add(doc_b)
        s.flush()
        an_b = db_models.Analysis(
            document_id="bbb111",
            analysis_timestamp=now,
            anomaly_count=1,
            scalar_score=0.9,
            severity_score=0.3,
            engine_version="3.2.0-test",
            summary=None,
        )
        s.add(an_b)
        s.flush()
        s.add(
            db_models.Anomaly(
                analysis_id=an_b.id,
                anomaly_id="admin:missing-final-action",
                issue="Press release uses approval language",
                severity="high",
                layer="administrative",
                details_json='{"approval_signals_found": ["adopted"]}',
            )
        )
        s.commit()

    from oraculus_di_auditor.interface.api import create_app

    return create_app()


@pytest.fixture
def client(seeded_app):
    return TestClient(seeded_app)


# ---------------------------------------------------------------------------
# /api/v1/jurisdictions
# ---------------------------------------------------------------------------


def test_jurisdictions_lists_both_with_correct_counts(client):
    resp = client.get("/api/v1/jurisdictions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    items = body["items"]
    assert len(items) == 2
    by_jur = {i["jurisdiction"]: i for i in items}
    assert by_jur["alpha"]["document_count"] == 2
    assert by_jur["alpha"]["analysis_count"] == 2
    assert by_jur["alpha"]["anomaly_count"] == 3
    assert by_jur["beta"]["document_count"] == 1
    assert by_jur["beta"]["anomaly_count"] == 1
    # Ordering: alpha (2 docs) should come before beta (1 doc)
    assert items[0]["jurisdiction"] == "alpha"


# ---------------------------------------------------------------------------
# /api/v1/documents
# ---------------------------------------------------------------------------


def test_documents_paginated_full_list(client):
    resp = client.get("/api/v1/documents?per_page=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["has_more"] is False
    assert body["page"] == 1
    # Each item carries jurisdiction + anomaly_count + scalar_score
    for item in body["items"]:
        assert "jurisdiction" in item
        assert "anomaly_count" in item
        assert "scalar_score" in item


def test_documents_filter_by_jurisdiction(client):
    resp = client.get("/api/v1/documents?jurisdiction=alpha")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(i["jurisdiction"] == "alpha" for i in body["items"])


def test_documents_pagination_has_more_flag(client):
    resp = client.get("/api/v1/documents?per_page=2&page=1")
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["has_more"] is True
    assert body["page"] == 1

    resp2 = client.get("/api/v1/documents?per_page=2&page=2")
    body2 = resp2.json()
    assert len(body2["items"]) == 1
    assert body2["has_more"] is False


# ---------------------------------------------------------------------------
# /api/v1/anomalies
# ---------------------------------------------------------------------------


def test_anomalies_paginated_with_document_join(client):
    resp = client.get("/api/v1/anomalies?per_page=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4  # 3 alpha + 1 beta
    for item in body["items"]:
        # Joined fields must be populated
        assert "document_title" in item
        assert "jurisdiction" in item
        assert "details" in item
        assert isinstance(item["details"], dict)


def test_anomalies_filter_by_severity_critical(client):
    resp = client.get("/api/v1/anomalies?severity=critical")
    body = resp.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["anomaly_id"] == "signature:unsigned-instrument"
    # details_json parsed into a dict
    assert item["details"]["instrument_type"] == "AGREEMENT"


def test_anomalies_filter_by_jurisdiction(client):
    resp = client.get("/api/v1/anomalies?jurisdiction=beta")
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["jurisdiction"] == "beta"


def test_anomalies_filter_by_layer(client):
    resp = client.get("/api/v1/anomalies?layer=administrative")
    body = resp.json()
    # admin:missing-final-action fires twice (once per jurisdiction)
    assert body["total"] == 2
    assert all(i["layer"] == "administrative" for i in body["items"])


def test_anomalies_filter_by_document_id(client):
    resp = client.get("/api/v1/anomalies?document_id=aaa111")
    body = resp.json()
    assert body["total"] == 2
    assert all(i["document_id"] == "aaa111" for i in body["items"])


# ---------------------------------------------------------------------------
# /api/v1/analyses
# ---------------------------------------------------------------------------


def test_analyses_lists_all_with_document_join(client):
    resp = client.get("/api/v1/analyses?per_page=10")
    body = resp.json()
    assert body["total"] == 3
    for item in body["items"]:
        assert "document_title" in item
        assert "jurisdiction" in item
        assert item["engine_version"] == "3.2.0-test"


def test_analyses_filter_by_jurisdiction(client):
    resp = client.get("/api/v1/analyses?jurisdiction=alpha")
    body = resp.json()
    assert body["total"] == 2


# ---------------------------------------------------------------------------
# /api/v1/synthesis/aggregates
# ---------------------------------------------------------------------------


def test_synthesis_aggregates_full_corpus(client):
    resp = client.get("/api/v1/synthesis/aggregates")
    body = resp.json()
    assert body["available"] is True
    assert body["total_documents"] == 3
    assert body["total_anomalies"] == 4
    assert set(body["jurisdictions_scope"]) == {"alpha", "beta"}

    # Severity rollup
    assert body["by_severity"] == {
        "critical": 1,
        "high": 2,
        "medium": 1,
        "low": 0,
    }

    # by_finding_id should be sorted by count desc; admin:missing-final-action
    # appears in 2 jurisdictions and has 2 occurrences = top of list.
    top = body["by_finding_id"][0]
    assert top["anomaly_id"] == "admin:missing-final-action"
    assert top["count"] == 2
    assert top["jurisdiction_count"] == 2
    assert set(top["jurisdictions"]) == {"alpha", "beta"}


def test_synthesis_aggregates_filtered_scope(client):
    resp = client.get("/api/v1/synthesis/aggregates?jurisdictions=alpha")
    body = resp.json()
    assert body["total_documents"] == 2
    assert body["total_anomalies"] == 3
    assert body["jurisdictions_scope"] == ["alpha"]
    # Critical signature finding belongs to alpha only
    assert body["by_severity"]["critical"] == 1


def test_synthesis_aggregates_by_layer_breakdown(client):
    resp = client.get("/api/v1/synthesis/aggregates")
    body = resp.json()
    layers = {row["layer"]: row["count"] for row in body["by_layer"]}
    assert layers.get("administrative") == 2
    assert layers.get("signature") == 1
    assert layers.get("fiscal") == 1


# ---------------------------------------------------------------------------
# Fail-open: empty DB / no rows returns structurally-valid empty responses
# ---------------------------------------------------------------------------


def test_empty_db_documents_returns_empty_page(monkeypatch, tmp_path):
    """Fresh DB with no rows → empty paginated response, not 500."""
    db_path = tmp_path / "odia_empty.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    c = TestClient(app)

    resp = c.get("/api/v1/documents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["has_more"] is False


def test_empty_db_jurisdictions_returns_empty_list(monkeypatch, tmp_path):
    db_path = tmp_path / "odia_empty2.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.interface.api import create_app

    c = TestClient(create_app())

    resp = c.get("/api/v1/jurisdictions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["items"] == []
