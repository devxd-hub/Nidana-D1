"""Concept schemas with prerequisite tracking and Odia-English terminology mappings."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConceptBase(BaseModel):
    id: str = Field(min_length=2, max_length=50)
    subject_id: str = Field(max_length=50)
    chapter_id: Optional[str] = Field(default=None, max_length=50)
    code: str = Field(min_length=2, max_length=50)
    name_en: str = Field(max_length=255)
    name_or: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    prerequisite_concept_ids: List[str] = Field(default_factory=list)
    terminology_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Bilingual English to Odia glossary mapping with transliterations",
    )


class ConceptCreate(ConceptBase):
    pass


class ConceptRead(ConceptBase):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
