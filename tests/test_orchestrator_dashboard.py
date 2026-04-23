"""Tests for the v2.7.3 D4 orchestrator dashboard endpoints.

Covers the three new GET routes that feed the frontend Orchestrator
page: ``/task-graph``, ``/executions``, ``/status``. Static task graph
is asserted shape-only; the two DB-backed endpoints are tested under
both populated and empty (never-initialised) conditions.
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "orchestrator_dashboard.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# /api/v1/orchestrator/task-graph — static structure, no DB
# ---------------------------------------------------------------------------


def test_task_graph_returns_six_agents(client):
    resp = client.get("/api/v1/orchestrator/task-graph")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["nodes"]) == 6
    node_ids = {n["id"] for n in body["nodes"]}
    assert node_ids == {
        "ingest",
        "analysis",
        "anomaly",
        "synthesis",
        "database",
        "interface",
    }


def test_task_graph_edges_connect_real_nodes(client):
    resp = client.get("/api/v1/orchestrator/task-graph")
    body = resp.json()
    node_ids = {n["id"] for n in body["nodes"]}
    assert len(body["edges"]) > 0
    for edge in body["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids


def test_task_graph_nodes_have_svg_coordinates(client):
    resp = client.get("/api/v1/orchestrator/task-graph")
    for n in resp.json()["nodes"]:
        # viewBox "0 0 800 400" — coords must be in range.
        assert 0 <= n["x"] <= 800
        assert 0 <= n["y"] <= 400
        assert n["label"]
        assert n["phase"]


# ---------------------------------------------------------------------------
# /api/v1/orchestrator/executions
# ---------------------------------------------------------------------------


def test_executions_returns_empty_list_on_fresh_db(client):
    resp = client.get("/api/v1/orchestrator/executions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["count"] == 0
    assert body["items"] == []


def test_executions_returns_seeded_rows_newest_first(client):
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    now = datetime.now(UTC).replace(tzinfo=None)
    with get_db() as session:
        for i in range(5):
            session.add(
                db_models.MeshExecutionJob(
                    job_id=f"job-{i}",
                    job_type="analysis",
                    status="completed",
                    created_at=now - timedelta(minutes=i * 5),
                    started_at=now - timedelta(minutes=i * 5),
                    completed_at=now - timedelta(minutes=(i * 5) - 1),
                    agent_count=3,
                    task_count=6,
                    gcn_validated=True,
                    governor_approved=True,
                )
            )

    resp = client.get("/api/v1/orchestrator/executions?limit=3")
    body = resp.json()
    assert body["available"] is True
    assert body["count"] == 3
    # Newest first — job-0 has the latest created_at
    assert body["items"][0]["job_id"] == "job-0"
    assert body["items"][0]["agent_count"] == 3
    assert body["items"][0]["gcn_validated"] is True


def test_executions_clamps_limit_to_valid_range(client):
    resp = client.get("/api/v1/orchestrator/executions?limit=0")
    assert resp.status_code == 200
    # 0 clamps to min 1; empty DB still returns 0 items
    resp = client.get("/api/v1/orchestrator/executions?limit=500")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/v1/orchestrator/status
# ---------------------------------------------------------------------------


def test_status_returns_static_agent_count_on_empty_db(client):
    resp = client.get("/api/v1/orchestrator/status")
    assert resp.status_code == 200
    body = resp.json()
    # No AgentNode rows → fall back to the static six-agent pipeline
    assert body["agents_online"] == 6
    assert body["tasks_queued"] == 0
    assert body["tasks_completed_today"] == 0
    assert body["available"] is True


def test_status_counts_active_agents(client):
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as session:
        session.add(
            db_models.AgentNode(
                agent_id="agent-1",
                agent_name="Ingestion",
                agent_type="specialist",
                status="active",
                version="1.0",
            )
        )
        session.add(
            db_models.AgentNode(
                agent_id="agent-2",
                agent_name="Analysis",
                agent_type="specialist",
                status="inactive",  # should NOT count
                version="1.0",
            )
        )
        session.add(
            db_models.AgentNode(
                agent_id="agent-3",
                agent_name="Anomaly",
                agent_type="specialist",
                status="active",
                version="1.0",
            )
        )

    resp = client.get("/api/v1/orchestrator/status")
    body = resp.json()
    assert body["agents_online"] == 2


def test_status_counts_queued_and_completed_today(client):
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    now = datetime.now(UTC).replace(tzinfo=None)
    yesterday = now - timedelta(hours=48)
    with get_db() as session:
        # 2 queued
        for i in range(2):
            session.add(
                db_models.MeshExecutionJob(
                    job_id=f"queued-{i}",
                    job_type="analysis",
                    status="queued",
                    agent_count=1,
                    task_count=1,
                )
            )
        # 1 executing (also counts as queued in the active sense)
        session.add(
            db_models.MeshExecutionJob(
                job_id="running-0",
                job_type="analysis",
                status="executing",
                agent_count=1,
                task_count=1,
            )
        )
        # 3 completed today
        for i in range(3):
            session.add(
                db_models.MeshExecutionJob(
                    job_id=f"done-today-{i}",
                    job_type="analysis",
                    status="completed",
                    completed_at=now - timedelta(hours=i),
                    agent_count=1,
                    task_count=1,
                )
            )
        # 1 completed yesterday — must NOT count
        session.add(
            db_models.MeshExecutionJob(
                job_id="done-yesterday",
                job_type="analysis",
                status="completed",
                completed_at=yesterday,
                agent_count=1,
                task_count=1,
            )
        )

    resp = client.get("/api/v1/orchestrator/status")
    body = resp.json()
    assert body["tasks_queued"] == 3
    assert body["tasks_completed_today"] == 3
