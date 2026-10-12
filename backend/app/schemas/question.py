"""Question and QuestionVariant schemas.

CRITICAL INVARIANT: Answer keys and complete explanations are strictly excluded
from public active-test schemas to prevent test compromise.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ApprovalState, QuestionDifficulty, QuestionType, VariantPurpose


class QuestionOption(BaseModel):
    id: str = Field(description="Option identifier, e.g. 'A', 'B', 'C', 'D'")
    text_en: str = Field(description="English option text")
    text_or: Optional[str] = Field(default=None, description="Odia option text")


# -------------------------------------------------------------
# Active-Test Public Schemas (NO correct_answer or explanations)
# -------------------------------------------------------------
class QuestionPublic(BaseModel):
    """Safe question presentation for active test takers.

    Answer keys, full explanations, and distractor reasoning are omitted.
    """

    id: str
    chapter_id: str
    concept_id: str
    type: QuestionType
    difficulty: QuestionDifficulty
    marks: float
    negative_marks: float
    expected_time_seconds: int
    language: str
    stem_en: str
    stem_or: Optional[str] = None
    options: List[QuestionOption]

    model_config = ConfigDict(from_attributes=True)


class QuestionVariantPublic(BaseModel):
    """Safe pedagogical variant for active learner probes."""

    id: str
    base_question_id: str
    variant_purpose: VariantPurpose
    stem_en: Optional[str] = None
    stem_or: Optional[str] = None
    options: Optional[List[QuestionOption]] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Authorized / Administrative Schemas (Include Answer Keys)
# -------------------------------------------------------------
class QuestionWithAnswer(QuestionPublic):
    """Full question record including authoritative answer key and distractor analysis.

    Restricted to educators, administrators, and post-submission autopsy reviews.
    """

    correct_answer: Any = Field(description="Authoritative correct answer (e.g. 'A')")
    explanation_en: Optional[str] = None
    explanation_or: Optional[str] = None
    distractor_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Misconception analysis per option"
    )
    approval_state: ApprovalState
    version: str
    created_at: datetime


class QuestionVariantWithAnswer(QuestionVariantPublic):
    """Variant record with authoritative answer key for grading."""

    correct_answer: Any
    explanation_en: Optional[str] = None
    explanation_or: Optional[str] = None
    changes_summary: Optional[str] = None
    approval_state: ApprovalState
    created_at: datetime


class QuestionCreate(BaseModel):
    id: str
    chapter_id: str
    concept_id: str
    type: QuestionType = QuestionType.SINGLE_CHOICE
    difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM
    marks: float = 4.0
    negative_marks: float = 1.0
    expected_time_seconds: int = 120
    language: str = "bilingual"
    stem_en: str
    stem_or: Optional[str] = None
    options: List[QuestionOption]
    correct_answer: Any
    explanation_en: Optional[str] = None
    explanation_or: Optional[str] = None
    distractor_metadata: Dict[str, Any] = Field(default_factory=dict)
    approval_state: ApprovalState = ApprovalState.APPROVED
    version: str = "1.0.0"


class QuestionVariantCreate(BaseModel):
    id: str
    base_question_id: str
    variant_purpose: VariantPurpose
    stem_en: Optional[str] = None
    stem_or: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: Any
    explanation_en: Optional[str] = None
    explanation_or: Optional[str] = None
    changes_summary: Optional[str] = None
    approval_state: ApprovalState = ApprovalState.APPROVED
