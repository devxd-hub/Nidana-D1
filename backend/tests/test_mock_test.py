"""Tests for 5-Question Mini-Mock workflow, answer concealment, scoring, and diagnosis triggering."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.seed_demo_data import seed_demo_data


@pytest.fixture(autouse=True)
def seed_test_database(db_session: Session):
    """Seed demo questions before each mock test."""
    seed_demo_data(db_session)


def test_start_mini_mock_conceals_answer_keys(client: TestClient, learner_auth_headers: dict):
    """Verify that start mini-mock returns 5 questions with options but conceals correct_answer and explanations."""
    response = client.post(
        "/api/v1/mock/start",
        json={"class_level": 10, "language": "bilingual"},
        headers=learner_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["total_questions"] == 5
    assert len(data["questions"]) == 5

    for q in data["questions"]:
        assert "correct_answer" not in q
        assert "explanation_en" not in q
        assert "explanation_or" not in q
        assert "distractor_metadata" not in q
        assert len(q["options"]) > 0


def test_submit_mini_mock_grades_authoritatively_and_triggers_diagnosis(
    client: TestClient, learner_auth_headers: dict
):
    """Verify authoritative scoring (+4 for correct, -1 for incorrect) and diagnosis run triggering."""
    # 1. Start mock
    start_resp = client.post(
        "/api/v1/mock/start",
        json={"class_level": 10, "language": "bilingual"},
        headers=learner_auth_headers,
    )
    mock_data = start_resp.json()
    session_id = mock_data["session_id"]
    questions = mock_data["questions"]

    # 2. Submit answers: 1 correct (A for q_c10_rxn_01), 1 incorrect (B for q_c10_rxn_02), rest unanswered
    answers = [
        {
            "question_id": questions[0]["id"],
            "selected_option": "A",
            "time_taken_seconds": 30,
        },
        {
            "question_id": questions[1]["id"],
            "selected_option": "B",  # Incorrect (correct is C)
            "time_taken_seconds": 40,
        },
    ]

    submit_resp = client.post(
        f"/api/v1/mock/{session_id}/submit",
        json={"answers": answers},
        headers=learner_auth_headers,
    )
    assert submit_resp.status_code == 200
    result = submit_resp.json()

    assert result["session_id"] == session_id
    assert len(result["results"]) == 2

    # Verify scores: +4.0 and -1.0
    res_map = {r["question_id"]: r for r in result["results"]}
    assert res_map[questions[0]["id"]]["is_correct"] is True
    assert res_map[questions[0]["id"]]["marks_obtained"] == 4.0

    assert res_map[questions[1]["id"]]["is_correct"] is False
    assert res_map[questions[1]["id"]]["marks_obtained"] == -1.0

    # Verify diagnostic run was triggered for the incorrect answer
    assert len(result["diagnostic_runs_triggered"]) >= 1
