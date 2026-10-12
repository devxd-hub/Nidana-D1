"""Tests for authoritative grading and learner ownership boundaries on attempts."""

from fastapi.testclient import TestClient
from app.core.errors import APIErrorCode


def setup_question(client: TestClient, admin_token: str):
    """Seed test syllabus and question for attempts."""
    client.post(
        "/api/v1/subjects",
        json={"id": "chem-att", "code": "CHEMA", "name_en": "Chemistry", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    client.post(
        "/api/v1/chapters",
        json={
            "id": "ch-chem-12-01",
            "subject_id": "chem-att",
            "class_level": 12,
            "chapter_number": 1,
            "title_en": "Solid State",
            "language_availability": ["en", "or"],
            "content_version": "1.0.0",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    client.post(
        "/api/v1/concepts",
        json={
            "id": "con-chem-c01",
            "subject_id": "chem-att",
            "chapter_id": "ch-chem-12-01",
            "code": "C-CHEM-01",
            "name_en": "Unit Cells",
            "prerequisite_concept_ids": [],
            "terminology_mapping": {},
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    client.post(
        "/api/v1/questions",
        json={
            "id": "q-chem-unitcell-1",
            "chapter_id": "ch-chem-12-01",
            "concept_id": "con-chem-c01",
            "type": "single_choice",
            "difficulty": "easy",
            "marks": 4.0,
            "negative_marks": 1.0,
            "expected_time_seconds": 60,
            "language": "bilingual",
            "stem_en": "How many atoms are in an FCC unit cell?",
            "options": [
                {"id": "A", "text_en": "4", "text_or": "୪"},
                {"id": "B", "text_en": "2", "text_or": "୨"},
            ],
            "correct_answer": "A",
            "explanation_en": "FCC has 8*(1/8) + 6*(1/2) = 4 atoms.",
            "distractor_metadata": {"B": "BCC atom count confusion"},
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )


def test_attempt_lifecycle_authoritative_grading(
    client: TestClient, admin_token: str, learner_token: str
):
    """Verify backend authoritative scoring for correct answer."""
    setup_question(client, admin_token)

    # 1. Learner starts attempt
    start_resp = client.post(
        "/api/v1/attempts",
        json={"question_id": "q-chem-unitcell-1"},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert start_resp.status_code == 201
    attempt_id = start_resp.json()["id"]
    assert start_resp.json()["lifecycle_state"] == "in_progress"
    assert start_resp.json()["is_correct"] is None

    # 2. Learner submits correct answer "A"
    submit_resp = client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={
            "submitted_response": {"selected_option": "A"},
            "time_taken_seconds": 35,
            "learning_signals": {"answer_changes": 0, "confidence_rating": 5},
        },
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()
    assert res["lifecycle_state"] == "submitted"
    assert res["is_correct"] is True
    assert res["marks_obtained"] == 4.0
    assert res["time_taken_seconds"] == 35


def test_attempt_scoring_negative_marks_on_incorrect(
    client: TestClient, admin_token: str, learner_token: str
):
    """Verify backend authoritatively applies negative marks on incorrect answer."""
    setup_question(client, admin_token)

    start_resp = client.post(
        "/api/v1/attempts",
        json={"question_id": "q-chem-unitcell-1"},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    attempt_id = start_resp.json()["id"]

    # Submit wrong option "B"
    submit_resp = client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={"submitted_response": {"selected_option": "B"}},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert submit_resp.status_code == 200
    res = submit_resp.json()
    assert res["is_correct"] is False
    assert res["marks_obtained"] == -1.0


def test_attempt_cannot_be_resubmitted(
    client: TestClient, admin_token: str, learner_token: str
):
    """Verify closed attempts reject additional submission attempts."""
    setup_question(client, admin_token)

    start_resp = client.post(
        "/api/v1/attempts",
        json={"question_id": "q-chem-unitcell-1"},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    attempt_id = start_resp.json()["id"]

    # First submit
    client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={"submitted_response": {"selected_option": "A"}},
        headers={"Authorization": f"Bearer {learner_token}"},
    )

    # Second submit should fail
    resubmit_resp = client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={"submitted_response": {"selected_option": "B"}},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert resubmit_resp.status_code == 400
    assert resubmit_resp.json()["error"]["code"] == APIErrorCode.ATTEMPT_ALREADY_SUBMITTED.value


def test_attempt_ownership_enforcement(
    client: TestClient, admin_token: str, learner_token: str, other_learner_token: str
):
    """Verify Learner B is forbidden from reading or mutating Learner A's attempt."""
    setup_question(client, admin_token)

    # Learner A starts attempt
    start_resp = client.post(
        "/api/v1/attempts",
        json={"question_id": "q-chem-unitcell-1"},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    attempt_id = start_resp.json()["id"]

    # Learner B tries to view Learner A's attempt -> 403 OWNERSHIP_VIOLATION
    get_resp = client.get(
        f"/api/v1/attempts/{attempt_id}",
        headers={"Authorization": f"Bearer {other_learner_token}"},
    )
    assert get_resp.status_code == 403
    assert get_resp.json()["error"]["code"] == APIErrorCode.OWNERSHIP_VIOLATION.value

    # Learner B tries to submit Learner A's attempt -> 403 OWNERSHIP_VIOLATION
    submit_resp = client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        json={"submitted_response": {"selected_option": "A"}},
        headers={"Authorization": f"Bearer {other_learner_token}"},
    )
    assert submit_resp.status_code == 403
    assert submit_resp.json()["error"]["code"] == APIErrorCode.OWNERSHIP_VIOLATION.value
