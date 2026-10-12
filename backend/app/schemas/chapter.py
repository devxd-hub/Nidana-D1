"""Chapter schemas with class-level validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import ApprovalState, ClassLevel


class ChapterBase(BaseModel):
    id: str = Field(min_length=2, max_length=50)
    subject_id: str = Field(max_length=50)
    class_level: int = Field(description="Supported educational class level: must be 9, 10, or 12")
    chapter_number: int = Field(ge=1)
    title_en: str = Field(max_length=255)
    title_or: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    language_availability: List[str] = Field(default=["en", "or"])
    content_version: str = Field(default="1.0.0")
    approval_state: ApprovalState = Field(default=ApprovalState.APPROVED)

    @field_validator("class_level")
    @classmethod
    def validate_class_level(cls, v: int) -> int:
        supported = ClassLevel.values()
        if v not in supported:
            raise ValueError(f"Class level {v} is unsupported. Allowed class levels are: {supported}")
        return v


class ChapterCreate(ChapterBase):
    pass


class ChapterRead(ChapterBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
