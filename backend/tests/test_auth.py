"""Tests for Supabase JWT verification, role enforcement, and ownership checks."""

from fastapi.testclient import TestClient
from app.core.errors import APIErrorCode
from tests.conftest import make_test_jwt


def test_auth_missing_header_fails(client: TestClient):
    """Calling protected endpoint without Authorization header yields 401."""
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == APIErrorCode.AUTHENTICATION_REQUIRED.value


def test_auth_invalid_token_fails(client: TestClient):
    """Calling with malformed or invalidly signed token yields 401."""
    invalid_token = make_test_jwt(invalid_secret=True)
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == APIErrorCode.INVALID_TOKEN.value


def test_auth_expired_token_fails(client: TestClient):
    """Expired token yields 401 with TOKEN_EXPIRED code."""
    expired_token = make_test_jwt(expired=True)
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == APIErrorCode.TOKEN_EXPIRED.value


def test_auth_valid_token_succeeds(client: TestClient, learner_token: str):
    """Valid JWT grants access to /api/v1/me and synchronizes profile."""
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "learner-123"
    assert data["email"] == "learner@test.com"
    assert data["role"] == "learner"


def test_role_enforcement_prevents_unauthorized_actions(
    client: TestClient, learner_token: str, admin_token: str
):
    """Learners are forbidden from creating curriculum subjects; Admins are permitted."""
    subject_payload = {
        "id": "physics-test",
        "code": "PHYSTEST",
        "name_en": "Physics Test",
        "name_or": "ପଦାର୍ଥ ବିଜ୍ଞାନ",
        "is_active": True,
    }

    # Learner should be rejected with 403 FORBIDDEN
    learner_resp = client.post(
        "/api/v1/subjects",
        json=subject_payload,
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert learner_resp.status_code == 403
    assert learner_resp.json()["error"]["code"] == APIErrorCode.FORBIDDEN.value

    # Admin should succeed
    admin_resp = client.post(
        "/api/v1/subjects",
        json=subject_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 201
    assert admin_resp.json()["id"] == "physics-test"
