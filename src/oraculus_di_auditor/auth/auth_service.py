"""Authentication service — registration, login, token management.

Auth is OPTIONAL: when no users exist, all callers are treated as anonymous
admin (single-user mode). Auth is enforced only after the first user registers.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

_TOKEN_EXPIRE_HOURS = 24 * 7  # 1 week
_ALGORITHM = "HS256"

# Secret key — in production, set via AUTH_SECRET_KEY env var
_DEFAULT_SECRET = "odia-dev-secret-change-in-production"


def _get_secret() -> str:
    import os

    return os.environ.get("AUTH_SECRET_KEY", _DEFAULT_SECRET)


class AuthError(Exception):
    """Raised for authentication/authorization failures."""


class AuthService:
    """Manages user registration, login, and JWT token lifecycle.

    Parameters
    ----------
    db_session:
        SQLAlchemy session. If ``None``, operates in memory-only mode for testing.
    """

    def __init__(self, db_session: Any = None) -> None:
        self._db = db_session
        self._memory_users: dict[str, dict] = {}  # fallback for testing

    # ------------------------------------------------------------------
    # Password hashing
    # ------------------------------------------------------------------

    def _hash_password(self, password: str) -> str:
        # Prefer bcrypt directly (avoids passlib/bcrypt 4.x version-check bug)
        try:
            import bcrypt as _bcrypt  # type: ignore[import]

            salt = _bcrypt.gensalt()
            return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        except ImportError:
            pass
        except Exception:
            pass
        # Fallback: SHA-256 hex (not production-safe, but functional for dev)
        import hashlib

        return "sha256:" + hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, plain: str, hashed: str) -> bool:
        if hashed.startswith("sha256:"):
            import hashlib

            return "sha256:" + hashlib.sha256(plain.encode()).hexdigest() == hashed
        try:
            import bcrypt as _bcrypt  # type: ignore[import]

            return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except ImportError:
            pass
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------
    # JWT helpers
    # ------------------------------------------------------------------

    def _create_token(self, user_id: str, role: str) -> tuple[str, str, datetime]:
        """Create a signed JWT. Returns (token, jti, expires_at)."""
        jti = secrets.token_hex(32)
        expires_at = datetime.now(UTC) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
        try:
            from jose import jwt  # type: ignore[import]

            payload = {
                "sub": user_id,
                "role": role,
                "jti": jti,
                "exp": expires_at,
                "iat": datetime.now(UTC),
            }
            token = jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)
        except ImportError:
            # Fallback: base64-encoded JSON (not production-safe)
            import base64
            import json

            payload_str = json.dumps({"sub": user_id, "role": role, "jti": jti})
            token = base64.urlsafe_b64encode(payload_str.encode()).decode()
        return token, jti, expires_at

    def _decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT. Raises AuthError on failure."""
        try:
            from jose import JWTError, jwt  # type: ignore[import]

            try:
                payload = jwt.decode(token, _get_secret(), algorithms=[_ALGORITHM])
                return payload
            except JWTError as exc:
                raise AuthError(f"Invalid token: {exc}") from exc
        except ImportError:
            import base64
            import json

            try:
                data = json.loads(base64.urlsafe_b64decode(token.encode()))
                return data
            except Exception as exc:
                raise AuthError(f"Invalid token: {exc}") from exc

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------

    def user_count(self) -> int:
        """Return number of registered users (0 = single-user mode)."""
        if self._db is not None:
            try:
                from .auth_models import User

                return self._db.query(User).count()
            except Exception:
                pass
        return len(self._memory_users)

    def auth_enabled(self) -> bool:
        """Return True if at least one user exists (auth is enforced)."""
        return self.user_count() > 0

    def register(self, email: str, password: str, name: str, role: str = "auditor") -> dict[str, Any]:
        """Create a new user.

        The first registered user is automatically made an admin.

        Returns the user dict (without password hash).
        Raises AuthError if email already exists.
        """
        if len(password) < 8:
            raise AuthError("Password must be at least 8 characters")

        hashed = self._hash_password(password)
        is_first = self.user_count() == 0
        effective_role = "admin" if is_first else role

        user_id = str(uuid.uuid4())

        if self._db is not None:
            from .auth_models import User, UserRole

            existing = self._db.query(User).filter(User.email == email).first()
            if existing:
                raise AuthError(f"Email already registered: {email}")

            user = User(
                id=user_id,
                email=email,
                name=name,
                hashed_password=hashed,
                role=UserRole(effective_role),
            )
            self._db.add(user)
            self._db.commit()
        else:
            if email in {u["email"] for u in self._memory_users.values()}:
                raise AuthError(f"Email already registered: {email}")
            self._memory_users[user_id] = {
                "id": user_id,
                "email": email,
                "name": name,
                "hashed_password": hashed,
                "role": effective_role,
            }

        return {"id": user_id, "email": email, "name": name, "role": effective_role}

    def login(self, email: str, password: str) -> dict[str, Any]:
        """Validate credentials and return auth token info.

        Returns
        -------
        dict with keys: ``token``, ``token_type``, ``user``
        Raises AuthError on invalid credentials.
        """
        user_data = self._find_user_by_email(email)
        if user_data is None:
            raise AuthError("Invalid email or password")
        if not self._verify_password(password, user_data["hashed_password"]):
            raise AuthError("Invalid email or password")

        token, jti, expires_at = self._create_token(user_data["id"], user_data["role"])

        # Record session
        self._create_session(user_data["id"], jti, expires_at)

        return {
            "token": token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat(),
            "user": {
                "id": user_data["id"],
                "email": user_data["email"],
                "name": user_data["name"],
                "role": user_data["role"],
            },
        }

    def verify_token(self, token: str) -> dict[str, Any]:
        """Validate JWT and return user info dict.

        Raises AuthError if token is invalid or session revoked.
        """
        payload = self._decode_token(token)
        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id:
            raise AuthError("Token missing subject claim")

        # Check session is still active
        if jti and not self._session_active(jti):
            raise AuthError("Session has been revoked")

        user_data = self._find_user_by_id(user_id)
        if user_data is None:
            raise AuthError("User not found")

        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data.get("role", "viewer"),
        }

    def logout(self, token: str) -> None:
        """Invalidate a session token."""
        try:
            payload = self._decode_token(token)
            jti = payload.get("jti")
            if jti:
                self._revoke_session(jti)
        except AuthError:
            pass  # Already invalid

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_user_by_email(self, email: str) -> dict | None:
        if self._db is not None:
            from .auth_models import User

            u = self._db.query(User).filter(User.email == email).first()
            if u:
                return {
                    "id": u.id, "email": u.email, "name": u.name,
                    "hashed_password": u.hashed_password, "role": str(u.role.value),
                }
        for u in self._memory_users.values():
            if u["email"] == email:
                return u
        return None

    def _find_user_by_id(self, user_id: str) -> dict | None:
        if self._db is not None:
            from .auth_models import User

            u = self._db.query(User).filter(User.id == user_id).first()
            if u:
                return {"id": u.id, "email": u.email, "name": u.name, "role": str(u.role.value)}
        return self._memory_users.get(user_id)

    def _create_session(self, user_id: str, jti: str, expires_at: datetime) -> None:
        if self._db is not None:
            from .auth_models import Session

            session = Session(user_id=user_id, token_jti=jti, expires_at=expires_at)
            self._db.add(session)
            self._db.commit()

    def _session_active(self, jti: str) -> bool:
        if self._db is not None:
            from .auth_models import Session

            session = self._db.query(Session).filter(
                Session.token_jti == jti, Session.is_active == True  # noqa: E712
            ).first()
            return session is not None
        return True  # In-memory: always active

    def _revoke_session(self, jti: str) -> None:
        if self._db is not None:
            from .auth_models import Session

            session = self._db.query(Session).filter(Session.token_jti == jti).first()
            if session:
                session.is_active = False
                self._db.commit()
