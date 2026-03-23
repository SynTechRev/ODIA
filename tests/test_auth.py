"""Tests for the authentication service."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.auth.auth_service import AuthError, AuthService


@pytest.fixture
def service():
    return AuthService()  # in-memory mode


class TestAuthEnabled:
    def test_no_users_auth_disabled(self, service):
        assert not service.auth_enabled()

    def test_after_register_auth_enabled(self, service):
        service.register("user@example.com", "password123", "User")
        assert service.auth_enabled()


class TestRegister:
    def test_register_returns_user_dict(self, service):
        user = service.register("a@example.com", "password123", "Alice")
        assert user["email"] == "a@example.com"
        assert user["name"] == "Alice"
        assert "id" in user
        assert "hashed_password" not in user

    def test_first_user_becomes_admin(self, service):
        user = service.register("admin@example.com", "password123", "Admin")
        assert user["role"] == "admin"

    def test_second_user_is_auditor_by_default(self, service):
        service.register("admin@example.com", "password123", "Admin")
        user2 = service.register("user@example.com", "password123", "User")
        assert user2["role"] == "auditor"

    def test_duplicate_email_raises_error(self, service):
        service.register("a@example.com", "password123", "Alice")
        with pytest.raises(AuthError):
            service.register("a@example.com", "password456", "Alice2")

    def test_short_password_raises_error(self, service):
        with pytest.raises(AuthError):
            service.register("a@example.com", "short", "Alice")


class TestLogin:
    def test_valid_login_returns_token(self, service):
        service.register("a@example.com", "password123", "Alice")
        result = service.login("a@example.com", "password123")
        assert "token" in result
        assert result["token_type"] == "bearer"

    def test_invalid_password_raises_error(self, service):
        service.register("a@example.com", "password123", "Alice")
        with pytest.raises(AuthError):
            service.login("a@example.com", "wrongpassword")

    def test_unknown_email_raises_error(self, service):
        with pytest.raises(AuthError):
            service.login("unknown@example.com", "password123")

    def test_login_returns_user_info(self, service):
        service.register("a@example.com", "password123", "Alice")
        result = service.login("a@example.com", "password123")
        assert result["user"]["email"] == "a@example.com"


class TestVerifyToken:
    def test_valid_token_returns_user(self, service):
        service.register("a@example.com", "password123", "Alice")
        login_result = service.login("a@example.com", "password123")
        user = service.verify_token(login_result["token"])
        assert user["email"] == "a@example.com"

    def test_invalid_token_raises_error(self, service):
        with pytest.raises(AuthError):
            service.verify_token("not.a.valid.token")

    def test_token_contains_role(self, service):
        service.register("a@example.com", "password123", "Alice")
        login_result = service.login("a@example.com", "password123")
        user = service.verify_token(login_result["token"])
        assert "role" in user


class TestLogout:
    def test_logout_does_not_raise(self, service):
        service.register("a@example.com", "password123", "Alice")
        result = service.login("a@example.com", "password123")
        service.logout(result["token"])  # should not raise

    def test_logout_invalid_token_does_not_raise(self, service):
        service.logout("invalid-token")  # should not raise


class TestUserCount:
    def test_zero_initially(self, service):
        assert service.user_count() == 0

    def test_increments_on_register(self, service):
        service.register("a@example.com", "pass12345", "A")
        assert service.user_count() == 1
        service.register("b@example.com", "pass12345", "B")
        assert service.user_count() == 2
