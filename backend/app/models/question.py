"""Question and QuestionVariant domain models."""

from typing import Any, Dict, List, Optional
from sqlalchemy import Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ApprovalState, QuestionDifficulty, QuestionType, VariantPurpose
from app.db.base import Base, TimestampMixin


class Question(Base, TimestampMixin):
    """Core question bank item.

    Answer keys and full explanations are strictly stored server-side
    and never exposed to active test-taking clients.
    """

    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_chapter_concept", "chapter_id", "concept_id"),
        Index("ix_questions_difficulty_approval", "difficulty", "approval_state"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # stable ID e.g. 'q-phy12-c01-001'
    chapter_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("chapters.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("concepts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(30), default=QuestionType.SINGLE_CHOICE.value, nullable=False
    )
    difficulty: Mapped[str] = mapped_column(
        String(20), default=QuestionDifficulty.MEDIUM.value, index=True, nullable=False
    )
    marks: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    negative_marks: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    expected_time_seconds: Mapped[int] = mapped_column(Integer, default=120, nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="bilingual", nullable=False)

    stem_en: Mapped[str] = mapped_column(Text, nullable=False)
    stem_or: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Options structure: [{"id": "A", "text_en": "...", "text_or": "..."}, ...]
    options: Mapped[list] = mapped_column(JSON, nullable=False)

    # Authoritative answer representation: e.g. "A" or ["A", "C"]
    # SERVER-SIDE ONLY during active tests!
    correct_answer: Mapped[Any] = mapped_column(JSON, nullable=False)

    explanation_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_or: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Diagnostic distractor metadata mapping options to misconceptions
    # Example: {"B": {"misconception": "inverted sign", "probe_target": "vector_direction"}}
    distractor_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    approval_state: Mapped[str] = mapped_column(
        String(20), default=ApprovalState.APPROVED.value, index=True, nullable=False
    )
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="questions")
    concept: Mapped["Concept"] = relationship("Concept", back_populates="questions")
    variants: Mapped[List["QuestionVariant"]] = relationship(
        "QuestionVariant", back_populates="base_question", cascade="all, delete-orphan"
    )
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="question")


class QuestionVariant(Base, TimestampMixin):
    """Targeted pedagogical variants designed for discrimination probes and mark autopsies."""

    __tablename__ = "question_variants"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    base_question_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    variant_purpose: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )  # e.g. odia, simplified, untimed, prerequisite, transfer, terminology_bridge

    stem_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stem_or: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Authoritative answer representation for this specific variant
    correct_answer: Mapped[Any] = mapped_column(JSON, nullable=False)

    explanation_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_or: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changes_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approval_state: Mapped[str] = mapped_column(
        String(20), default=ApprovalState.APPROVED.value, index=True, nullable=False
    )

    # Relationships
    base_question: Mapped["Question"] = relationship("Question", back_populates="variants")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="variant")
