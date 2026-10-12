"""Subject domain model."""

from typing import List
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Subject(Base, TimestampMixin):
    """Academic subjects (e.g., Physics, Chemistry, Mathematics, Biology)."""

    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # stable slug, e.g. 'physics'
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_or: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter", back_populates="subject", cascade="all, delete-orphan"
    )
    concepts: Mapped[List["Concept"]] = relationship(
        "Concept", back_populates="subject", cascade="all, delete-orphan"
    )
