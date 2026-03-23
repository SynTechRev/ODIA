"""Tests for WorkspaceService."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.workspace.workspace_service import WorkspaceService


@pytest.fixture
def service():
    return WorkspaceService()  # in-memory mode


USER_A = "user-a-id"
USER_B = "user-b-id"


class TestCreateWorkspace:
    def test_returns_workspace_dict(self, service):
        ws = service.create_workspace("Audit 2024", created_by=USER_A)
        assert ws["name"] == "Audit 2024"
        assert "id" in ws
        assert ws["created_by"] == USER_A

    def test_creator_is_admin_member(self, service):
        ws = service.create_workspace("Audit 2024", created_by=USER_A)
        members = service.get_members(ws["id"])
        creator_member = next((m for m in members if m["user_id"] == USER_A), None)
        assert creator_member is not None
        assert creator_member["role"] == "admin"

    def test_jurisdiction_stored(self, service):
        ws = service.create_workspace("Audit", created_by=USER_A, jurisdiction="Visalia, CA")
        assert ws["jurisdiction"] == "Visalia, CA"

    def test_unique_ids(self, service):
        ws1 = service.create_workspace("WS1", created_by=USER_A)
        ws2 = service.create_workspace("WS2", created_by=USER_A)
        assert ws1["id"] != ws2["id"]


class TestGetWorkspace:
    def test_returns_workspace(self, service):
        ws = service.create_workspace("Test", created_by=USER_A)
        retrieved = service.get_workspace(ws["id"])
        assert retrieved is not None
        assert retrieved["id"] == ws["id"]

    def test_nonexistent_returns_none(self, service):
        assert service.get_workspace("nonexistent-id") is None


class TestListWorkspaces:
    def test_returns_workspaces_for_member(self, service):
        ws = service.create_workspace("WS", created_by=USER_A)
        result = service.list_workspaces(USER_A)
        ids = [w["id"] for w in result]
        assert ws["id"] in ids

    def test_not_member_not_listed(self, service):
        service.create_workspace("WS", created_by=USER_A)
        result = service.list_workspaces(USER_B)
        assert len(result) == 0


class TestAddMember:
    def test_add_member_returns_dict(self, service):
        ws = service.create_workspace("WS", created_by=USER_A)
        member = service.add_member(ws["id"], USER_B, "auditor")
        assert member["user_id"] == USER_B
        assert member["role"] == "auditor"

    def test_member_appears_in_list(self, service):
        ws = service.create_workspace("WS", created_by=USER_A)
        service.add_member(ws["id"], USER_B, "viewer")
        members = service.get_members(ws["id"])
        user_ids = [m["user_id"] for m in members]
        assert USER_B in user_ids


class TestAuditLog:
    def test_log_action_creates_entry(self, service):
        ws = service.create_workspace("WS", created_by=USER_A)
        service.log_action(ws["id"], USER_A, "test.action", detail="Test detail")
        log = service.get_audit_log(ws["id"])
        assert len(log) >= 1

    def test_log_entry_has_required_fields(self, service):
        ws = service.create_workspace("WS", created_by=USER_A)
        service.log_action(ws["id"], USER_A, "upload.file", detail="doc.pdf")
        log = service.get_audit_log(ws["id"])
        entry = log[0]
        assert "id" in entry
        assert "action" in entry
        assert "timestamp" in entry
        assert "user_id" in entry

    def test_log_ordered_most_recent_first(self, service):
        ws = service.create_workspace("WS", created_by=USER_A)
        service.log_action(ws["id"], USER_A, "action.first")
        service.log_action(ws["id"], USER_A, "action.second")
        log = service.get_audit_log(ws["id"])
        actions = [e["action"] for e in log]
        assert actions.index("action.second") < actions.index("action.first")

    def test_log_filtered_by_workspace(self, service):
        ws1 = service.create_workspace("WS1", created_by=USER_A)
        ws2 = service.create_workspace("WS2", created_by=USER_A)
        service.log_action(ws1["id"], USER_A, "action.ws1")
        service.log_action(ws2["id"], USER_A, "action.ws2")
        log1 = service.get_audit_log(ws1["id"])
        # The workspace creation auto-logs nothing in memory mode, only explicit log_action calls
        actions1 = [e["action"] for e in log1]
        assert "action.ws1" in actions1
        assert "action.ws2" not in actions1

    def test_log_limit_respected(self, service):
        ws = service.create_workspace("WS", created_by=USER_A)
        for i in range(10):
            service.log_action(ws["id"], USER_A, f"action.{i}")
        log = service.get_audit_log(ws["id"], limit=5)
        assert len(log) <= 5
