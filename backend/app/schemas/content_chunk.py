"""ContentChunk schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ApprovalState


class ContentChunkBase(BaseModel):
    id: str = Field(min_length=2, max_length=50)
    chapter_id: str = Field(max_length=50)
    concept_id: Optional[str] = Field(default=None, max_length=50)
    source_title: str = Field(max_length=255)
    section_title: Optional[str] = Field(default=None, max_length=255)
    page_number: Optional[int] = None
    language: str = Field(default="bilingual")
    text_content: str
    content_version: str = Field(default="1.0.0")
    approval_state: ApprovalState = Field(default=ApprovalState.APPROVED)


class ContentChunkCreate(ContentChunkBase):
    pass


class ContentChunkRead(ContentChunkBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
