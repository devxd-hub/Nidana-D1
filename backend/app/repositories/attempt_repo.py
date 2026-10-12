"""Attempt repository for learner submissions."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attempt import Attempt
from app.repositories.base import BaseRepository


class AttemptRepository(BaseRepository[Attempt]):
    def __init__(self, db: Session):
        super().__init__(Attempt, db)

    def list_by_user(self, user_id: str, limit: int = 50) -> List[Attempt]:
        stmt = (
            select(Attempt)
            .where(Attempt.user_id == user_id)
            .order_by(Attempt.started_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_id_and_user(self, attempt_id: str, user_id: str) -> Optional[Attempt]:
        stmt = (
            select(Attempt)
            .where(Attempt.id == attempt_id)
            .where(Attempt.user_id == user_id)
        )
        return self.db.scalars(stmt).first()
