"""Tests for FastAPI app startup, routing, and OpenAPI schema generation."""

from fastapi.testclient import TestClient
from app.main import create_app


def test_app_startup_and_docs():
    """Verify application boots, docs are mounted, and OpenAPI schema is valid."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/docs")
    assert response.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert schema["info"]["title"] == "NIDANA API"
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/questions" in schema["paths"]
    assert "/api/v1/attempts" in schema["paths"]
