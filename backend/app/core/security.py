"""Authentication and authorization utilities with server-side Supabase JWT verification."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.constants import UserRole
from app.core.errors import APIErrorCode, APIException

logger = logging.getLogger(__name__)

# HTTP Bearer scheme with automatic 401 handling
http_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    """Verified identity extracted from a cryptographically validated JWT."""

    id: str
    email: Optional[str]
    role: str
    raw_payload: Dict[str, Any]

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    @property
    def is_educator(self) -> bool:
        return self.role in (UserRole.EDUCATOR.value, UserRole.ADMIN.value)


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """Verify and decode Supabase Auth JWT server-side using the project secret.

    Guarantees:
    - Verifies signature using SUPABASE_JWT_SECRET
    - Enforces expiration time (exp)
    - Validates audience (aud == 'authenticated')
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            key=settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.SUPABASE_JWT_ALGORITHM],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            options={"require": ["exp", "sub"]},
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        logger.warning("Token expired signature")
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=APIErrorCode.TOKEN_EXPIRED,
            message="Authentication token has expired. Please log in again.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.warning("Invalid token received: %s", str(exc))
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=APIErrorCode.INVALID_TOKEN,
            message="Invalid authentication token provided.",
        ) from exc


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> AuthenticatedUser:
    """FastAPI dependency to extract and verify the authenticated caller from the Bearer token."""
    if not credentials or not credentials.credentials:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=APIErrorCode.AUTHENTICATION_REQUIRED,
            message="Authentication required. Provide a valid Bearer token in the Authorization header.",
        )

    token = credentials.credentials
    payload = decode_supabase_jwt(token)

    user_id = payload.get("sub")
    if not user_id:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=APIErrorCode.INVALID_TOKEN,
            message="Token payload is missing subject identifier ('sub').",
        )

    # Supabase attaches role either in app_metadata or top-level role
    role = payload.get("app_metadata", {}).get("role") or payload.get("role") or UserRole.LEARNER.value
    email = payload.get("email")

    return AuthenticatedUser(
        id=user_id,
        email=email,
        role=role,
        raw_payload=payload,
    )


def enforce_ownership(resource_owner_id: str, current_user: AuthenticatedUser) -> None:
    """Enforce learner ownership boundary on personal records (attempts, study plans, etc.).

    Rejects requests where the authenticated caller attempts to access or mutate
    another learner's resource, unless the caller holds educator/admin privilege.
    """
    if current_user.is_admin:
        return

    if str(resource_owner_id) != str(current_user.id):
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=APIErrorCode.OWNERSHIP_VIOLATION,
            message="Forbidden: You do not have permission to access or modify this resource.",
        )


def require_role(*allowed_roles: UserRole):
    """Dependency factory enforcing specific roles on protected routes."""

    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        allowed_values = [r.value for r in allowed_roles]
        if current_user.role not in allowed_values and not current_user.is_admin:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code=APIErrorCode.FORBIDDEN,
                message=f"Access requires one of the following roles: {allowed_values}",
            )
        return current_user

    return role_checker
