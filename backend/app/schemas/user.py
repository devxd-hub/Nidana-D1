"""User request and response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import ExamTarget, PreferredLanguage, UserRole


class UserBase(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=100)
    preferred_language: PreferredLanguage = Field(default=PreferredLanguage.ODIA)
    exam_target: ExamTarget = Field(default=ExamTarget.CHSE_CLASS_12)


class UserCreate(UserBase):
    id: str = Field(description="Supabase Auth UUID")
    email: EmailStr
    role: UserRole = Field(default=UserRole.LEARNER)


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=100)
    preferred_language: Optional[PreferredLanguage] = None
    exam_target: Optional[ExamTarget] = None


class UserPublic(UserBase):
    id: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
