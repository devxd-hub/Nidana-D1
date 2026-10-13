"""Tests for ChromaDB index initialization, re-indexing, curriculum query filters, and health."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.seed_demo_data import seed_demo_data
from app.rag.chroma_client import ChromaVectorIndex


@pytest.fixture(autouse=True)
def seed_test_database(db_session: Session):
    seed_demo_data(db_session)


def test_rag_health_endpoint(client: TestClient):
    """Verify RAG health check returns healthy status without leaking internal filesystem paths."""
    resp = client.get("/api/v1/rag/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "collection" in data
    assert "dimensions" in data
    assert "error" not in data


def test_rag_reindex_and_curriculum_query(
    client: TestClient, db_session: Session, admin_auth_headers: dict
):
    """Verify that ChromaDB can be rebuilt from SQLite ContentChunks and queried with filters."""
    # 1. Rebuild index from SQLite
    reindex_resp = client.post("/api/v1/rag/reindex", headers=admin_auth_headers)
    assert reindex_resp.status_code == 200
    reindex_data = reindex_resp.json()
    assert reindex_data["status"] == "rebuilt"
    assert reindex_data["indexed_chunks"] >= 4

    # 2. Query with Class 10 filters
    query_resp = client.post(
        "/api/v1/rag/query",
        json={
            "query_text": "oxidation reduction oxygen loss",
            "class_level": 10,
            "subject_id": "sub_science",
            "top_k": 3,
        },
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["has_sufficient_evidence"] is True
    assert len(query_data["citations"]) > 0
    assert len(query_data["chunks"]) > 0

    # Ensure all returned chunks have Class 10 metadata
    for chunk in query_data["chunks"]:
        assert chunk["metadata"]["class_level"] == 10
