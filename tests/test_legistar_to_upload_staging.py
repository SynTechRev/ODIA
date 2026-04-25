"""Tests for the v2.7.6 X3 Legistar → upload-staging bridge.

Pre-X3 the LegistarPanel button was structurally non-functional on the
desktop install: retrieved files landed in a CWD-relative dir, were
never registered into the upload store, and the success banner showed
"0 documents" or nothing at all. These tests pin the new behavior:
``register_uploaded_path`` puts retrieved files exactly where the
Upload page reads from, and the retrieval background thread now calls
that helper for every successful download.
"""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# register_uploaded_path() — direct unit tests
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_upload_store(monkeypatch, tmp_path):
    """Reset the routes/upload module's globals to a per-test temp dir
    + empty file dict so tests don't leak through ``_FILES``."""
    from oraculus_di_auditor.interface.routes import upload as upload_routes

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(upload_routes, "_UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(upload_routes, "_FILES", {})
    return upload_routes, upload_dir


def test_register_moves_file_into_upload_dir(fresh_upload_store, tmp_path):
    upload_routes, upload_dir = fresh_upload_store
    src = tmp_path / "agenda.pdf"
    src.write_bytes(b"%PDF-1.4 fake pdf bytes")

    meta = upload_routes.register_uploaded_path(src, source="https://x.legistar/y")

    assert not src.exists(), "default move=True should remove the source"
    assert meta["name"] == "agenda.pdf"
    assert meta["format"] == "pdf"
    assert meta["sha256"]
    assert meta["source"] == "https://x.legistar/y"
    assert meta["file_id"] in upload_routes._FILES
    # File now lives under _UPLOAD_DIR with the file_id-prefixed name.
    files_in_upload_dir = list(upload_dir.iterdir())
    assert len(files_in_upload_dir) == 1
    assert files_in_upload_dir[0].name.endswith("_agenda.pdf")


def test_register_with_move_false_copies(fresh_upload_store, tmp_path):
    upload_routes, _upload_dir = fresh_upload_store
    src = tmp_path / "resolution.txt"
    src.write_bytes(b"text-payload")

    meta = upload_routes.register_uploaded_path(src, move=False)

    assert src.exists(), "move=False should preserve the source file"
    assert meta["file_id"] in upload_routes._FILES
    assert upload_routes._FILES[meta["file_id"]]["size"] == len(b"text-payload")


def test_register_rejects_unknown_extension(fresh_upload_store, tmp_path):
    upload_routes, _upload_dir = fresh_upload_store
    src = tmp_path / "weird.docx"
    src.write_bytes(b"docx bytes")

    with pytest.raises(ValueError, match="Unsupported file type"):
        upload_routes.register_uploaded_path(src)


def test_register_missing_file_raises(fresh_upload_store, tmp_path):
    upload_routes, _upload_dir = fresh_upload_store
    with pytest.raises(FileNotFoundError):
        upload_routes.register_uploaded_path(tmp_path / "nope.pdf")


# ---------------------------------------------------------------------------
# Retrieval background thread — manifest registration
# ---------------------------------------------------------------------------


@pytest.fixture
def client_with_fake_legistar(monkeypatch, tmp_path):
    """Spin up create_app() with a faked LegistarAdapter that writes
    two stub PDFs into the staging dir + returns a manifest pointing
    at them."""
    db_path = tmp_path / "legistar.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.interface.api import create_app
    from oraculus_di_auditor.interface.routes import upload as upload_routes

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(upload_routes, "_UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(upload_routes, "_FILES", {})

    # Steer the retrieval default into a sandboxed temp dir.
    retrieval_root = tmp_path / "retrieval-staging"

    from oraculus_di_auditor.interface.routes import retrieval as retrieval_routes

    monkeypatch.setattr(
        retrieval_routes, "_default_retrieval_dir", lambda: retrieval_root
    )

    # Fake adapter — writes two stub PDFs into output_dir and returns a
    # manifest pointing at them. Keeps the test offline.
    from oraculus_di_auditor.adapters import legistar_adapter

    class _FakeAdapter:
        def __init__(self, client_id):
            self.client_id = client_id

        def retrieve_corpus(self, *, start_date, end_date, output_dir, matter_types):
            from pathlib import Path as _P

            outdir = _P(output_dir)
            outdir.mkdir(parents=True, exist_ok=True)
            files = []
            for name in ("agenda_2024_01.pdf", "resolution_2024_02.pdf"):
                local = outdir / name
                local.write_bytes(b"%PDF stub bytes for " + name.encode())
                files.append(
                    {
                        "matter_id": 100 + len(files),
                        "matter_title": f"Stub matter {len(files)}",
                        "attachment_name": name,
                        "local_path": str(local),
                        "sha256": "deadbeef",
                        "source_url": f"https://example.legistar/{name}",
                    }
                )
            return {
                "client_id": self.client_id,
                "start_date": start_date,
                "end_date": end_date,
                "matter_count": 2,
                "attachment_count": 2,
                "downloaded_count": 2,
                "failed_count": 0,
                "files": files,
            }

    monkeypatch.setattr(legistar_adapter, "LegistarAdapter", _FakeAdapter)

    app = create_app()
    return TestClient(app), upload_routes


def test_retrieval_registers_files_into_upload_store(client_with_fake_legistar):
    """End-to-end: POST /retrieve/legistar → poll until complete →
    /upload/files lists the retrieved PDFs."""
    import time

    client, upload_routes = client_with_fake_legistar

    resp = client.post(
        "/api/v1/retrieve/legistar",
        json={
            "client_id": "stubville",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        },
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Wait for the background thread (cap at 5s).
    deadline = time.time() + 5.0
    while time.time() < deadline:
        body = client.get(f"/api/v1/retrieve/status/{job_id}").json()
        if body["status"] in ("complete", "error"):
            break
        time.sleep(0.05)
    assert body["status"] == "complete", body
    manifest = body["manifest"]
    assert manifest["downloaded_count"] == 2
    assert manifest["registered_count"] == 2
    assert manifest["registration_errors"] == []

    # The Upload page polls /upload/files — the retrieved PDFs must be there.
    files_resp = client.get("/api/v1/upload/files")
    assert files_resp.status_code == 200
    listed = files_resp.json()
    assert listed["count"] == 2
    names = sorted(f["name"] for f in listed["files"])
    assert names == ["agenda_2024_01.pdf", "resolution_2024_02.pdf"]
    # Source URL must be preserved on the metadata.
    sources = sorted(f.get("source", "") for f in listed["files"])
    assert all(s.startswith("https://example.legistar/") for s in sources)
