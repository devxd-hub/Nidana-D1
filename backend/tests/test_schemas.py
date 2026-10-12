"""Tests for domain schema validation and invariant enforcement."""

import pytest
from pydantic import ValidationError

from app.core.constants import ApprovalState, ClassLevel, QuestionDifficulty, QuestionType
from app.schemas.chapter import ChapterBase
from app.schemas.question import QuestionOption, QuestionPublic, QuestionWithAnswer


def test_chapter_class_level_validation():
    """Verify supported ClassLevels (9, 10, 12) succeed and invalid ones fail."""
    # Valid class levels
    for level in [9, 10, 12]:
        ch = ChapterBase(
            id=f"ch-{level}",
            subject_id="physics",
            class_level=level,
            chapter_number=1,
            title_en="Electric Charges",
        )
        assert ch.class_level == level

    # Invalid class levels
    for invalid_level in [8, 11, 7, 13]:
        with pytest.raises(ValidationError) as exc:
            ChapterBase(
                id="ch-invalid",
                subject_id="physics",
                class_level=invalid_level,
                chapter_number=1,
                title_en="Invalid Class",
            )
        assert "unsupported" in str(exc.value).lower()


def test_question_public_conceals_answer_key():
    """Verify QuestionPublic schema strips correct_answer and explanations."""
    raw_question = {
        "id": "q-001",
        "chapter_id": "ch-12",
        "concept_id": "c-01",
        "type": QuestionType.SINGLE_CHOICE,
        "difficulty": QuestionDifficulty.MEDIUM,
        "marks": 4.0,
        "negative_marks": 1.0,
        "expected_time_seconds": 120,
        "language": "bilingual",
        "stem_en": "What is the SI unit of electric charge?",
        "stem_or": "ବିଦ୍ୟୁତ ଆଧାନର SI ଏକକ କ’ଣ?",
        "options": [
            {"id": "A", "text_en": "Coulomb", "text_or": "କୁଲମ୍ବ"},
            {"id": "B", "text_en": "Ampere", "text_or": "ଆମ୍ପିୟର"},
        ],
        "correct_answer": "A",
        "explanation_en": "The SI unit is Coulomb (C).",
        "explanation_or": "ଏସଆଇ ଏକକ ହେଉଛି କୁଲମ୍ବ (C)।",
        "distractor_metadata": {"B": "Confusion with current"},
        "approval_state": ApprovalState.APPROVED,
        "version": "1.0.0",
    }

    # Validate against public schema
    public_q = QuestionPublic.model_validate(raw_question)
    dumped = public_q.model_dump()

    # Crucial security checks: answer key and explanations must NOT exist in dumped public representation
    assert "correct_answer" not in dumped
    assert "explanation_en" not in dumped
    assert "explanation_or" not in dumped
    assert "distractor_metadata" not in dumped
    assert dumped["id"] == "q-001"
    assert len(dumped["options"]) == 2
