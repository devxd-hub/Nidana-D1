"""Attempt domain model for learner answer submissions and authoritative scoring."""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AttemptLifecycle
from app.db.base import Base, TimestampMixin


class Attempt(Base, TimestampMixin):
    """Learner attempt records. Correctness and marks are computed authoritatively by backend logic."""

    __tablename__ = "attempts"
    __table_args__ = (
        Index("ix_attempts_user_lifecycle", "user_id", "lifecycle_state"),
        Index("ix_attempts_question", "question_id"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # stable UUID
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    variant_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("question_variants.id", ondelete="SET NULL"), nullable=True
    )

    lifecycle_state: Mapped[str] = mapped_column(
        String(30), default=AttemptLifecycle.IN_PROGRESS.value, index=True, nullable=False
    )

    # Client-submitted answer payload (e.g., {"selected_option": "A"})
    submitted_response: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Authoritative scoring computed ONLY on trusted backend
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    marks_obtained: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Permitted diagnostic learning signals (never includes secrets or raw sensitive text)
    # Example: {"answer_changes": 1, "confidence_rating": 4, "time_on_stem_seconds": 45}
    learning_signals: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="attempts")
    question: Mapped[Optional["Question"]] = relationship("Question", back_populates="attempts")
    variant: Mapped[Optional["QuestionVariant"]] = relationship("QuestionVariant", back_populates="attempts")
