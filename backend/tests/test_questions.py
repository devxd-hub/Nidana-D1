"""Tests verifying answer keys are strictly concealed in active-test endpoints."""

from fastapi.testclient import TestClient


def test_question_answer_key_concealment(client: TestClient, admin_token: str):
    """Seed a question and verify public endpoints do NOT expose answer keys."""
    # 1. Admin creates subject
    client.post(
        "/api/v1/subjects",
        json={"id": "phys-q", "code": "PHYQ", "name_en": "Physics", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 2. Admin creates chapter
    client.post(
        "/api/v1/chapters",
        json={
            "id": "ch-phys-12-01",
            "subject_id": "phys-q",
            "class_level": 12,
            "chapter_number": 1,
            "title_en": "Electrostatics",
            "language_availability": ["en", "or"],
            "content_version": "1.0.0",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 3. Admin creates concept
    client.post(
        "/api/v1/concepts",
        json={
            "id": "con-phys-c01",
            "subject_id": "phys-q",
            "chapter_id": "ch-phys-12-01",
            "code": "C-ELEC-01",
            "name_en": "Coulomb Law",
            "prerequisite_concept_ids": [],
            "terminology_mapping": {"force": "ବଳ (bala)"},
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # 4. Admin creates question with answer key and explanation
    create_payload = {
        "id": "q-secret-test-1",
        "chapter_id": "ch-phys-12-01",
        "concept_id": "con-phys-c01",
        "type": "single_choice",
        "difficulty": "medium",
        "marks": 4.0,
        "negative_marks": 1.0,
        "expected_time_seconds": 90,
        "language": "bilingual",
        "stem_en": "What happens to the force when distance is doubled?",
        "options": [
            {"id": "A", "text_en": "Quartered", "text_or": "ଚାରି ଭାଗରୁ ଏକ ଭାଗ"},
            {"id": "B", "text_en": "Doubled", "text_or": "ଦୁଇଗୁଣ"},
        ],
        "correct_answer": "A",
        "explanation_en": "Force varies inversely with square of distance: F ~ 1/r^2.",
        "distractor_metadata": {"B": "Direct proportionality misconception"},
    }

    create_resp = client.post(
        "/api/v1/questions",
        json=create_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201

    # 5. Query via public list endpoint
    list_resp = client.get("/api/v1/questions?chapter_id=ch-phys-12-01")
    assert list_resp.status_code == 200
    questions = list_resp.json()
    assert len(questions) >= 1

    item = next(q for q in questions if q["id"] == "q-secret-test-1")
    assert "correct_answer" not in item
    assert "explanation_en" not in item
    assert "distractor_metadata" not in item

    # 6. Query via public get endpoint
    detail_resp = client.get("/api/v1/questions/q-secret-test-1")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "correct_answer" not in detail
    assert "explanation_en" not in detail
    assert "distractor_metadata" not in detail
    assert detail["stem_en"] == "What happens to the force when distance is doubled?"
    assert len(detail["options"]) == 2
