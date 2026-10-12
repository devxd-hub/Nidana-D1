"""Concept repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.repositories.base import BaseRepository


class ConceptRepository(BaseRepository[Concept]):
    def __init__(self, db: Session):
        super().__init__(Concept, db)

    def list_by_filter(
        self,
        subject_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
    ) -> List[Concept]:
        stmt = select(Concept)
        if subject_id:
            stmt = stmt.where(Concept.subject_id == subject_id)
        if chapter_id:
            stmt = stmt.where(Concept.chapter_id == chapter_id)
        stmt = stmt.order_by(Concept.code)
        return list(self.db.scalars(stmt).all())

    def get_by_code(self, code: str) -> Optional[Concept]:
        stmt = select(Concept).where(Concept.code == code)
        return self.db.scalars(stmt).first()
