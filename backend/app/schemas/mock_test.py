"""Pydantic schemas for the 5-Question Mini-Mock workflow."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.question import QuestionPublic


class MockStartRequest(BaseModel):
    """Parameters to generate a mini-mock assessment."""

    class_level: int = Field(default=10, description="Target Class level (9, 10, or 12)")
    subject_id: Optional[str] = Field(default=None, description="Optional subject filter")
    language: str = Field(default="bilingual", description="Target language ('odia', 'english', or 'bilingual')")


class MockSessionResponse(BaseModel):
    """Active mini-mock session with 5 questions (answer keys strictly concealed)."""

    session_id: str = Field(description="Unique session identifier")
    class_level: int
    questions: List[QuestionPublic] = Field(description="The 5 active test questions without answer keys")
    total_questions: int = Field(default=5)
    total_marks: float = Field(description="Sum of maximum obtainable marks")


class MockAnswerSubmission(BaseModel):
    """Learner answer payload for a single question."""

    question_id: str
    selected_option: Optional[str] = Field(default=None, description="Selected option ('A', 'B', 'C', 'D' or None)")
    time_taken_seconds: Optional[int] = Field(default=0, ge=0)
    learning_signals: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MockSubmitRequest(BaseModel):
    """Submission payload for completing the mini-mock."""

    answers: List[MockAnswerSubmission]


class QuestionResultOutcome(BaseModel):
    """Post-submission question evaluation with server-side answers and explanations."""

    question_id: str
    attempt_id: str
    selected_option: Optional[str]
    is_correct: bool
    marks_obtained: float
    correct_option: str
    explanation_en: Optional[str] = None
    explanation_or: Optional[str] = None


class MockResultResponse(BaseModel):
    """Authoritative result summary for the completed mini-mock."""

    session_id: str
    total_score: float
    max_possible_score: float
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    results: List[QuestionResultOutcome]
    diagnostic_runs_triggered: List[str] = Field(
        default_factory=list,
        description="IDs of diagnostic runs initiated for incorrect answers",
    )
