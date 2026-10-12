"""Tests for offline content packs download and idempotent batch event synchronization."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.seed_demo_data import seed_demo_data


@pytest.fixture(autouse=True)
def seed_test_database(db_session: Session):
    seed_demo_data(db_session)


def test_list_and_download_offline_pack(client: TestClient):
    """Verify pack manifest listing and full bundle download with concealed answer keys."""
    # 1. List packs
    list_resp = client.get("/api/v1/sync/packs")
    assert list_resp.status_code == 200
    packs = list_resp.json()
    assert len(packs) >= 3

    # 2. Download Class 10 bundle
    bundle_resp = client.get(f"/api/v1/sync/packs/{packs[0]['pack_id']}")
    assert bundle_resp.status_code == 200
    bundle = bundle_resp.json()

    assert "manifest" in bundle
    assert "chapters" in bundle
    assert "questions" in bundle
    assert "learning_chunks" in bundle

    # Ensure no answer keys in downloaded questions
    for q in bundle["questions"]:
        assert "correct_answer" not in q
        assert "explanation_en" not in q


def test_sync_batch_idempotency_and_duplicate_handling(
    client: TestClient, learner_auth_headers: dict
):
    """Verify that submitting an event batch authoritatively grades and replaying the same event returns DUPLICATE."""
    client_event_id = "evt_unique_test_101"
    now_iso = datetime.now(timezone.utc).isoformat()

    batch_payload = {
        "events": [
            {
                "client_event_id": client_event_id,
                "event_type": "ATTEMPT_SUBMIT",
                "payload_schema_version": "1.0.0",
                "client_timestamp": now_iso,
                "payload": {
                    "question_id": "q_c10_rxn_01",
                    "selected_option": "A",
                    "time_taken_seconds": 25,
                },
            }
        ]
    }

    # 1. First submission -> ACCEPTED
    resp1 = client.post(
        "/api/v1/sync/batch",
        json=batch_payload,
        headers=learner_auth_headers,
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["accepted_count"] == 1
    assert data1["duplicate_count"] == 0
    assert data1["event_results"][0]["status"] == "ACCEPTED"
    assert data1["event_results"][0]["processed_data"]["is_correct"] is True

    # 2. Replay duplicate submission -> DUPLICATE (idempotent)
    resp2 = client.post(
        "/api/v1/sync/batch",
        json=batch_payload,
        headers=learner_auth_headers,
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["accepted_count"] == 0
    assert data2["duplicate_count"] == 1
    assert data2["event_results"][0]["status"] == "DUPLICATE"
