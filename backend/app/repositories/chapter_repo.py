"""Chapter repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ApprovalState
from app.models.chapter import Chapter
from app.repositories.base import BaseRepository


class ChapterRepository(BaseRepository[Chapter]):
    def __init__(self, db: Session):
        super().__init__(Chapter, db)

    def list_by_filter(
        self,
        subject_id: Optional[str] = None,
        class_level: Optional[int] = None,
        approval_state: str = ApprovalState.APPROVED.value,
    ) -> List[Chapter]:
        stmt = select(Chapter).where(Chapter.approval_state == approval_state)
        if subject_id:
            stmt = stmt.where(Chapter.subject_id == subject_id)
        if class_level:
            stmt = stmt.where(Chapter.class_level == class_level)
        stmt = stmt.order_by(Chapter.class_level, Chapter.chapter_number)
        return list(self.db.scalars(stmt).all())
