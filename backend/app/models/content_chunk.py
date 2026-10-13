"""ContentChunk domain model for approved curriculum content storage and provenance."""

from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ApprovalState
from app.db.base import Base, TimestampMixin


class ContentChunk(Base, TimestampMixin):
    """Approved educational content chunks for RAG grounding and pedagogical bridges.

    Serves as the canonical source of truth in SQLite for rebuildable ChromaDB indices.
    """

    __tablename__ = "content_chunks"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    chapter_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("chapters.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("concepts.id", ondelete="SET NULL"), index=True, nullable=True
    )
    subject_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("subjects.id", ondelete="SET NULL"), index=True, nullable=True
    )
    class_level: Mapped[int] = mapped_column(Integer, default=10, nullable=False, index=True)
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_locator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # e.g., "TB-CH02-SEC3"
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="bilingual", nullable=False, index=True)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)  # SHA-256
    content_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    approval_state: Mapped[str] = mapped_column(
        String(20), default=ApprovalState.APPROVED.value, index=True, nullable=False
    )

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="content_chunks")
