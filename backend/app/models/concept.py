"""Concept domain model with prerequisite tracking and Odia-English terminology mappings."""

from typing import Dict, List, Optional
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Concept(Base, TimestampMixin):
    """Atomic curriculum concepts with terminology bridges and prerequisite dependencies."""

    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    subject_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chapter_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("chapters.id", ondelete="SET NULL"), index=True, nullable=True
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_or: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Prerequisite concept relationships stored as stable identifiers list
    prerequisite_concept_ids: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Odia–English bilingual terminology mappings
    # Example: {"acceleration": "ତ୍ୱରଣ (twaraṇa)", "displacement": "ବିସ୍ଥାପନ (bisthāpana)"}
    terminology_mapping: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="concepts")
    chapter: Mapped[Optional["Chapter"]] = relationship("Chapter", back_populates="concepts")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="concept")
