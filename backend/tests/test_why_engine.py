"""Tests for LangGraph WHY Engine, diagnosis graph execution, and mark recovery flow."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.seed_demo_data import seed_demo_data


@pytest.fixture(autouse=True)
def seed_test_database(db_session: Session):
    seed_demo_data(db_session)


def test_why_engine_diagnosis_and_mark_recovery_flow(
    client: TestClient, learner_auth_headers: dict
):
    """Test full core loop: Incorrect Attempt -> Diagnose -> Report -> Verify Recovery."""
    # 1. Create an incorrect attempt via start & submit
    start_resp = client.post(
        "/api/v1/attempts",
        json={"question_id": "q_c10_rxn_01"},
        headers=learner_auth_headers,
    )
    assert start_resp.status_code == 201
    attempt_id = start_resp.json()["id"]

    submit_resp = client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={"submitted_response": {"selected_option": "B"}, "time_taken_seconds": 35},
        headers=learner_auth_headers,
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["is_correct"] is False

    # 2. Run WHY Engine diagnosis on the incorrect attempt
    diag_resp = client.post(
        f"/api/v1/diagnosis/run/{attempt_id}",
        headers=learner_auth_headers,
    )
    assert diag_resp.status_code == 200
    diag_data = diag_resp.json()

    assert diag_data["status"] == "COMPLETED"
    assert diag_data["primary_hypothesis"] in [
        "MISCONCEPTION",
        "PREREQUISITE_GAP",
        "CARELESS_EXECUTION",
    ]
    # Invariant: At most 2 probes
    assert len(diag_data["selected_probes"]) <= 2
    assert diag_data["recovery_report_id"] is not None

    report_id = diag_data["recovery_report_id"]

    # 3. Fetch Mark Recovery Report
    rep_resp = client.get(
        f"/api/v1/diagnosis/reports/{report_id}",
        headers=learner_auth_headers,
    )
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["is_verified"] is False
    assert "targeted_repair" in rep_data

    # 4. Verify Mark Recovery via follow-up mastery check
    verify_resp = client.post(
        f"/api/v1/diagnosis/reports/{report_id}/verify",
        json={"is_mastery_correct": True},
        headers=learner_auth_headers,
    )
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_verified"] is True
    assert verify_data["status"] == "RECOVERED"
