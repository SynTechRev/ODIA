"""Authentication and authorization for O.D.I.A.

Optional module — only enforced when at least one user exists in the database.
Single-user mode (no users registered) passes all requests without auth.
"""

from .auth_models import Session, User, UserRole
from .auth_service import AuthService

__all__ = ["AuthService", "Session", "User", "UserRole"]
