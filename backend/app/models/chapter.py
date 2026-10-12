"""Chapter domain model with class-level constraints."""

from typing import List
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ApprovalState
from app.db.base import Base, TimestampMixin


class Chapter(Base, TimestampMixin):
    """Syllabus chapters constrained to supported Class levels (9, 10, 12)."""

    __tablename__ = "chapters"
    __table_args__ = (
        CheckConstraint("class_level IN (9, 10, 12)", name="ck_chapters_class_level"),
        Index("ix_chapters_subject_class", "subject_id", "class_level"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    subject_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    class_level: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    title_or: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language_availability: Mapped[list] = mapped_column(
        JSON, default=lambda: ["en", "or"], nullable=False
    )
    content_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    approval_state: Mapped[str] = mapped_column(
        String(20), default=ApprovalState.APPROVED.value, index=True, nullable=False
    )

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="chapters")
    concepts: Mapped[List["Concept"]] = relationship(
        "Concept", back_populates="chapter", cascade="all, delete-orphan"
    )
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="chapter")
    content_chunks: Mapped[List["ContentChunk"]] = relationship(
        "ContentChunk", back_populates="chapter", cascade="all, delete-orphan"
    )
