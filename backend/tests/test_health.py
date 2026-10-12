"""Tests for health endpoint safety and behavior."""

from fastapi.testclient import TestClient


def test_health_check_returns_ok_and_no_secrets(client: TestClient):
    """Ensure /api/v1/health provides liveness without leaking secrets or internals."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data
    assert "timestamp" in data
    assert "database_connected" in data

    # Verify absence of secrets or sensitive connection strings
    raw_text = response.text.lower()
    forbidden_terms = ["secret", "password", "token", "sqlite:", "postgres:", "supabase.co"]
    for term in forbidden_terms:
        assert term not in raw_text, f"Health endpoint leaked sensitive term: {term}"
