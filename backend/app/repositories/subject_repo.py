"""Subject repository."""

from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.repositories.base import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    def __init__(self, db: Session):
        super().__init__(Subject, db)

    def list_active(self) -> List[Subject]:
        stmt = select(Subject).where(Subject.is_active == True).order_by(Subject.code)
        return list(self.db.scalars(stmt).all())
