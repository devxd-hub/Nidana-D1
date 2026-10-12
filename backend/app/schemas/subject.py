"""Subject schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SubjectBase(BaseModel):
    id: str = Field(min_length=2, max_length=50, description="Stable subject slug, e.g. 'physics'")
    code: str = Field(min_length=2, max_length=20, description="Short code, e.g. 'PHYS'")
    name_en: str = Field(max_length=100)
    name_or: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class SubjectCreate(SubjectBase):
    pass


class SubjectRead(SubjectBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
