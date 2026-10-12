"""Tests for centralized API error envelopes and machine-readable error codes."""

from fastapi import APIRouter
from fastapi.testclient import TestClient
from app.core.errors import APIErrorCode, APIException
from app.main import create_app


def test_resource_not_found_error_structure(client: TestClient):
    """Verify 404 generates uniform error envelope."""
    response = client.get("/api/v1/subjects/non-existent-subject-id")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == APIErrorCode.RESOURCE_NOT_FOUND.value
    assert "not found" in body["error"]["message"].lower()


def test_validation_error_structure(client: TestClient):
    """Verify request validation failures return standardized VALIDATION_ERROR code."""
    # Attempting to fetch questions with invalid limit
    response = client.get("/api/v1/questions?limit=9999")
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == APIErrorCode.VALIDATION_ERROR.value
    assert isinstance(body["error"]["details"], list)


def test_unhandled_exception_returns_safe_message():
    """Verify uncaught exceptions do not leak tracebacks or credentials."""
    app = create_app()
    test_router = APIRouter()

    @test_router.get("/api/v1/crash-test")
    def crash_route():
        # Raise unexpected internal error with sensitive token string
        raise RuntimeError("Sensitive token leak attempt: secret_token_abc_123")

    app.include_router(test_router)
    custom_client = TestClient(app, raise_server_exceptions=False)

    response = custom_client.get("/api/v1/crash-test")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == APIErrorCode.INTERNAL_SERVER_ERROR.value
    assert "secret_token_abc_123" not in response.text
    assert body["error"]["details"] is None
