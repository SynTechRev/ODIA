"""Tests for src/oraculus_di_auditor/interface/routes/upload.py.

Uses FastAPI TestClient for HTTP-level testing. Audit execution is patched
to avoid running the full analysis pipeline in unit tests.
"""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

# Skip all tests if FastAPI / httpx are not installed
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from oraculus_di_auditor.interface.api import create_app
from oraculus_di_auditor.interface.routes import upload as upload_module

# ---------------------------------------------------------------------------
# Test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a fresh TestClient with an isolated file/job store."""
    # Clear in-memory state between tests
    upload_module._FILES.clear()
    upload_module._JOBS.clear()
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _txt_file(name: str = "test.txt", content: str = "Sample document text.") -> tuple:
    return (name, io.BytesIO(content.encode()), "text/plain")


def _json_file(name: str = "test.json", data: dict | None = None) -> tuple:
    payload = data or {"raw_text": "Sample JSON document.", "title": "Test"}
    return (name, io.BytesIO(json.dumps(payload).encode()), "application/json")


# ---------------------------------------------------------------------------
# POST /api/v1/upload — single file
# ---------------------------------------------------------------------------


class TestUploadSingle:
    def test_upload_txt_returns_200(self, client):
        response = client.post(
            "/api/v1/upload",
            files={"file": _txt_file()},
        )
        assert response.status_code == 200

    def test_upload_returns_file_metadata(self, client):
        response = client.post("/api/v1/upload", files={"file": _txt_file()})
        data = response.json()
        assert "file_id" in data
        assert "name" in data
        assert "size" in data
        assert "sha256" in data
        assert "format" in data

    def test_upload_txt_format_detected(self, client):
        response = client.post("/api/v1/upload", files={"file": _txt_file("doc.txt")})
        assert response.json()["format"] == "txt"

    def test_upload_json_format_detected(self, client):
        response = client.post("/api/v1/upload", files={"file": _json_file("doc.json")})
        assert response.json()["format"] == "json"

    def test_upload_size_correct(self, client):
        content = b"Hello world"
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
        )
        assert response.json()["size"] == len(content)

    def test_upload_sha256_correct(self, client):
        import hashlib

        content = b"Known content for hashing"
        expected = hashlib.sha256(content).hexdigest()
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
        )
        assert response.json()["sha256"] == expected

    def test_upload_unsupported_extension_returns_400(self, client):
        response = client.post(
            "/api/v1/upload",
            files={
                "file": ("test.exe", io.BytesIO(b"binary"), "application/octet-stream")
            },
        )
        assert response.status_code == 400

    def test_upload_csv_rejected(self, client):
        response = client.post(
            "/api/v1/upload",
            files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/csv")},
        )
        assert response.status_code == 400

    def test_upload_file_id_is_string(self, client):
        response = client.post("/api/v1/upload", files={"file": _txt_file()})
        assert isinstance(response.json()["file_id"], str)

    def test_two_uploads_get_different_ids(self, client):
        r1 = client.post("/api/v1/upload", files={"file": _txt_file("a.txt")})
        r2 = client.post("/api/v1/upload", files={"file": _txt_file("b.txt")})
        assert r1.json()["file_id"] != r2.json()["file_id"]


# ---------------------------------------------------------------------------
# POST /api/v1/upload/batch
# ---------------------------------------------------------------------------


class TestUploadBatch:
    def test_batch_upload_two_files(self, client):
        response = client.post(
            "/api/v1/upload/batch",
            files=[
                ("files", _txt_file("a.txt")),
                ("files", _txt_file("b.txt")),
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["uploaded"]) == 2
        assert data["errors"] == []

    def test_batch_mixed_valid_invalid(self, client):
        response = client.post(
            "/api/v1/upload/batch",
            files=[
                ("files", _txt_file("good.txt")),
                ("files", ("bad.exe", io.BytesIO(b"x"), "application/octet-stream")),
            ],
        )
        data = response.json()
        assert len(data["uploaded"]) == 1
        assert len(data["errors"]) == 1

    def test_batch_error_includes_filename(self, client):
        response = client.post(
            "/api/v1/upload/batch",
            files=[
                ("files", ("bad.exe", io.BytesIO(b"x"), "application/octet-stream"))
            ],
        )
        errors = response.json()["errors"]
        assert errors[0]["name"] == "bad.exe"


# ---------------------------------------------------------------------------
# GET /api/v1/upload/files
# ---------------------------------------------------------------------------


class TestListFiles:
    def test_empty_list_on_fresh_session(self, client):
        response = client.get("/api/v1/upload/files")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["files"] == []

    def test_uploaded_file_appears_in_list(self, client):
        client.post("/api/v1/upload", files={"file": _txt_file("doc.txt")})
        response = client.get("/api/v1/upload/files")
        assert response.json()["count"] == 1

    def test_multiple_files_all_listed(self, client):
        for i in range(3):
            client.post("/api/v1/upload", files={"file": _txt_file(f"doc_{i}.txt")})
        response = client.get("/api/v1/upload/files")
        assert response.json()["count"] == 3


# ---------------------------------------------------------------------------
# DELETE /api/v1/upload/files/{file_id}
# ---------------------------------------------------------------------------


class TestDeleteFile:
    def test_delete_existing_file(self, client):
        upload = client.post("/api/v1/upload", files={"file": _txt_file()}).json()
        file_id = upload["file_id"]
        response = client.delete(f"/api/v1/upload/files/{file_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_deleted_file_not_in_list(self, client):
        upload = client.post("/api/v1/upload", files={"file": _txt_file()}).json()
        file_id = upload["file_id"]
        client.delete(f"/api/v1/upload/files/{file_id}")
        files = client.get("/api/v1/upload/files").json()["files"]
        assert not any(f["file_id"] == file_id for f in files)

    def test_delete_nonexistent_file_returns_404(self, client):
        response = client.delete("/api/v1/upload/files/nonexistent123")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/audit/run
# ---------------------------------------------------------------------------


class TestAuditRun:
    def _upload_txt(self, client, content: str = "test") -> str:
        r = client.post(
            "/api/v1/upload",
            files={"file": ("doc.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        return r.json()["file_id"]

    def test_run_returns_job_id(self, client):
        fid = self._upload_txt(client)
        response = client.post("/api/v1/audit/run", json={"file_ids": [fid]})
        assert response.status_code == 200
        assert "job_id" in response.json()

    def test_run_returns_pending_status(self, client):
        fid = self._upload_txt(client)
        response = client.post("/api/v1/audit/run", json={"file_ids": [fid]})
        assert response.json()["status"] == "pending"

    def test_run_with_no_file_ids_uses_all_uploaded(self, client):
        self._upload_txt(client)
        self._upload_txt(client)
        response = client.post("/api/v1/audit/run", json={})
        assert response.status_code == 200
        assert response.json()["file_count"] == 2

    def test_run_with_no_files_returns_400(self, client):
        response = client.post("/api/v1/audit/run", json={"file_ids": []})
        assert response.status_code == 400

    def test_run_with_unknown_file_id_returns_404(self, client):
        response = client.post("/api/v1/audit/run", json={"file_ids": ["nonexistent"]})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/audit/status/{job_id}
# ---------------------------------------------------------------------------


class TestAuditStatus:
    def _start_job(self, client) -> str:
        r = client.post(
            "/api/v1/upload",
            files={"file": ("doc.txt", io.BytesIO(b"test"), "text/plain")},
        )
        fid = r.json()["file_id"]
        r2 = client.post("/api/v1/audit/run", json={"file_ids": [fid]})
        return r2.json()["job_id"]

    def test_status_returns_200(self, client):
        job_id = self._start_job(client)
        response = client.get(f"/api/v1/audit/status/{job_id}")
        assert response.status_code == 200

    def test_status_has_required_fields(self, client):
        job_id = self._start_job(client)
        data = client.get(f"/api/v1/audit/status/{job_id}").json()
        assert "job_id" in data
        assert "status" in data
        assert "progress" in data

    def test_status_for_unknown_job_returns_404(self, client):
        response = client.get("/api/v1/audit/status/nonexistent-job")
        assert response.status_code == 404

    def test_status_is_valid_state(self, client):
        job_id = self._start_job(client)
        data = client.get(f"/api/v1/audit/status/{job_id}").json()
        assert data["status"] in ("pending", "running", "complete", "error")


# ---------------------------------------------------------------------------
# GET /api/v1/audit/results/{job_id} — uses a pre-set completed job
# ---------------------------------------------------------------------------


class TestAuditResults:
    def _inject_complete_job(self) -> str:
        """Directly inject a completed job into the store for testing."""
        job_id = "test-complete-job"
        upload_module._JOBS[job_id] = {
            "job_id": job_id,
            "status": "complete",
            "file_ids": [],
            "progress": {
                "phase": "Complete",
                "docs_processed": 1,
                "findings_count": 2,
                "total_docs": 1,
            },
            "results": {
                "job_id": job_id,
                "document_count": 1,
                "finding_count": 2,
                "severity_summary": {"critical": 0, "high": 1, "medium": 1, "low": 0},
                "findings": [
                    {
                        "id": "fiscal:amount",
                        "issue": "Missing appropriation",
                        "severity": "high",
                        "layer": "fiscal",
                        "document_id": "doc_001",
                        "details": {},
                    },
                    {
                        "id": "constitutional:broad_delegation",
                        "issue": "Broad delegation",
                        "severity": "medium",
                        "layer": "constitutional",
                        "document_id": "doc_001",
                        "details": {},
                    },
                ],
                "document_manifest": [],
                "generated_at": "2026-01-01T00:00:00+00:00",
            },
            "error": None,
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        return job_id

    def test_results_for_complete_job(self, client):
        job_id = self._inject_complete_job()
        response = client.get(f"/api/v1/audit/results/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["results"] is not None

    def test_results_contain_findings(self, client):
        job_id = self._inject_complete_job()
        data = client.get(f"/api/v1/audit/results/{job_id}").json()
        assert len(data["results"]["findings"]) == 2

    def test_results_for_unknown_job_returns_404(self, client):
        response = client.get("/api/v1/audit/results/nonexistent")
        assert response.status_code == 404

    def test_results_for_pending_job_returns_status_only(self, client):
        upload_module._JOBS["pending-job"] = {
            "job_id": "pending-job",
            "status": "pending",
            "progress": {},
            "results": None,
            "error": None,
        }
        response = client.get("/api/v1/audit/results/pending-job")
        data = response.json()
        assert data["status"] == "pending"
        assert data["results"] is None


# ---------------------------------------------------------------------------
# GET /api/v1/audit/export/{job_id}
# ---------------------------------------------------------------------------


class TestAuditExport:
    def _inject_job(self) -> str:
        return TestAuditResults()._inject_complete_job()

    def test_export_markdown_returns_200(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/export/{job_id}?format=markdown")
        assert response.status_code == 200

    def test_export_markdown_content_type(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/export/{job_id}?format=markdown")
        assert "markdown" in response.headers.get("content-type", "").lower()

    def test_export_html_returns_200(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/export/{job_id}?format=html")
        assert response.status_code == 200

    def test_export_html_contains_html_tags(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/export/{job_id}?format=html")
        assert b"<html" in response.content or b"<pre" in response.content

    def test_export_default_format_is_markdown(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/export/{job_id}")
        assert response.status_code == 200

    def test_export_unknown_format_returns_400(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/export/{job_id}?format=xlxs")
        assert response.status_code == 400

    def test_export_pending_job_returns_409(self, client):
        upload_module._JOBS["pending-export"] = {
            "job_id": "pending-export",
            "status": "pending",
            "results": None,
            "error": None,
            "progress": {},
        }
        response = client.get("/api/v1/audit/export/pending-export")
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/v1/audit/evidence-packet/{job_id}
# ---------------------------------------------------------------------------


class TestEvidencePacket:
    def _inject_job(self) -> str:
        return TestAuditResults()._inject_complete_job()

    def test_evidence_packet_returns_200(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/evidence-packet/{job_id}")
        assert response.status_code == 200

    def test_evidence_packet_content_type_zip(self, client):
        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/evidence-packet/{job_id}")
        assert "zip" in response.headers.get("content-type", "").lower()

    def test_evidence_packet_is_valid_zip(self, client):
        import zipfile as zf

        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/evidence-packet/{job_id}")
        assert zf.is_zipfile(io.BytesIO(response.content))

    def test_evidence_packet_contains_readme(self, client):
        import zipfile as zf

        job_id = self._inject_job()
        response = client.get(f"/api/v1/audit/evidence-packet/{job_id}")
        with zf.ZipFile(io.BytesIO(response.content)) as z:
            assert "README.md" in z.namelist()

    def test_evidence_packet_pending_job_returns_409(self, client):
        upload_module._JOBS["pending-zip"] = {
            "job_id": "pending-zip",
            "status": "pending",
            "results": None,
            "error": None,
            "progress": {},
        }
        response = client.get("/api/v1/audit/evidence-packet/pending-zip")
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/upload/image — OCR endpoint
# ---------------------------------------------------------------------------


def _png_bytes() -> bytes:
    """Return a minimal 1x1 white PNG."""
    import base64

    # 1x1 white PNG encoded as base64
    b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+h"
        "HgAHggJ/PchI6QAAAABJRU5ErkJggg=="
    )
    return base64.b64decode(b64)


class TestUploadImage:
    def test_upload_jpeg_returns_200(self, client):
        # Use PNG with .jpg extension — the server accepts based on extension
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("photo.jpg", io.BytesIO(_png_bytes()), "image/jpeg")},
        )
        assert response.status_code == 200

    def test_upload_png_returns_200(self, client):
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("scan.png", io.BytesIO(_png_bytes()), "image/png")},
        )
        assert response.status_code == 200

    def test_upload_image_returns_file_id(self, client):
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("scan.png", io.BytesIO(_png_bytes()), "image/png")},
        )
        data = response.json()
        assert "file_id" in data

    def test_upload_image_returns_raw_text_field(self, client):
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("scan.png", io.BytesIO(_png_bytes()), "image/png")},
        )
        data = response.json()
        assert "raw_text" in data
        assert isinstance(data["raw_text"], str)

    def test_upload_image_returns_ocr_method(self, client):
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("scan.png", io.BytesIO(_png_bytes()), "image/png")},
        )
        data = response.json()
        assert "ocr_method" in data
        assert data["ocr_method"] in ("tesseract", "unavailable", "pillow_stub")

    def test_upload_image_file_registered_in_store(self, client):
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("scan.png", io.BytesIO(_png_bytes()), "image/png")},
        )
        file_id = response.json()["file_id"]
        files_resp = client.get("/api/v1/upload/files")
        ids = [f["file_id"] for f in files_resp.json()["files"]]
        assert file_id in ids

    def test_upload_image_rejects_pdf(self, client):
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        )
        assert response.status_code == 400

    def test_upload_image_rejects_txt(self, client):
        response = client.post(
            "/api/v1/upload/image",
            files={"file": ("doc.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_image_can_be_used_in_audit(self, client):
        """File registered via image upload should be usable in audit/run."""
        resp = client.post(
            "/api/v1/upload/image",
            files={"file": ("scan.png", io.BytesIO(_png_bytes()), "image/png")},
        )
        file_id = resp.json()["file_id"]
        with patch.object(
            upload_module,
            "_execute_audit_job",
            lambda job_id, file_ids, cfg: upload_module._JOBS.__setitem__(
                job_id,
                {**upload_module._JOBS[job_id], "status": "complete", "results": {}},
            ),
        ):
            run_resp = client.post("/api/v1/audit/run", json={"file_ids": [file_id]})
        assert run_resp.status_code == 200


# ---------------------------------------------------------------------------
# _ocr_image helper — unit tests
# ---------------------------------------------------------------------------


class TestOCRHelper:
    def test_ocr_unavailable_returns_stub(self, tmp_path):
        """When pytesseract is not installed, returns a stub message."""
        from oraculus_di_auditor.interface.routes.upload import _ocr_image

        png = tmp_path / "img.png"
        png.write_bytes(_png_bytes())
        with patch.dict("sys.modules", {"pytesseract": None}):
            text, method = _ocr_image(png)
        # Either tesseract ran or we got the unavailable stub
        assert isinstance(text, str)
        assert method in ("tesseract", "unavailable")

    def test_ocr_returns_tuple(self, tmp_path):
        from oraculus_di_auditor.interface.routes.upload import _ocr_image

        png = tmp_path / "img.png"
        png.write_bytes(_png_bytes())
        result = _ocr_image(png)
        assert isinstance(result, tuple)
        assert len(result) == 2
