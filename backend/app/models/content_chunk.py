"""ContentChunk domain model for approved curriculum content storage."""

from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ApprovalState
from app.db.base import Base, TimestampMixin


class ContentChunk(Base, TimestampMixin):
    """Approved educational content chunks for RAG grounding and pedagogical bridges.

    Vector embeddings can be attached via pgvector migration when semantic search is provisioned.
    """

    __tablename__ = "content_chunks"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    chapter_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("chapters.id", ondelete="CASCADE"), index=True, nullable=False
    )
    concept_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("concepts.id", ondelete="SET NULL"), index=True, nullable=True
    )
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="bilingual", nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    approval_state: Mapped[str] = mapped_column(
        String(20), default=ApprovalState.APPROVED.value, index=True, nullable=False
    )

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="content_chunks")
