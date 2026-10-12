"""StudyPlan and StudyPlanTask domain models for post-autopsy repair scheduling."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ExamTarget, StudyPlanStatus, TaskStatus
from app.db.base import Base, TimestampMixin


class StudyPlan(Base, TimestampMixin):
    """Personalized study plan container for targeted learner interventions."""

    __tablename__ = "study_plans"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=StudyPlanStatus.ACTIVE.value, index=True, nullable=False
    )
    target_exam: Mapped[str] = mapped_column(
        String(50), default=ExamTarget.CHSE_CLASS_12.value, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="study_plans")
    tasks: Mapped[List["StudyPlanTask"]] = relationship(
        "StudyPlanTask", back_populates="study_plan", cascade="all, delete-orphan"
    )


class StudyPlanTask(Base, TimestampMixin):
    """Individual repair tasks targeting verified or provisional diagnostic gaps."""

    __tablename__ = "study_plan_tasks"
    __table_args__ = (
        Index("ix_tasks_plan_status", "study_plan_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    study_plan_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("study_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("concepts.id", ondelete="SET NULL"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_weakness: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.PENDING.value, index=True, nullable=False
    )
    follow_up_question_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    study_plan: Mapped["StudyPlan"] = relationship("StudyPlan", back_populates="tasks")
