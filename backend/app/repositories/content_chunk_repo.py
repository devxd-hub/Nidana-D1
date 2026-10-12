"""ContentChunk repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ApprovalState
from app.models.content_chunk import ContentChunk
from app.repositories.base import BaseRepository


class ContentChunkRepository(BaseRepository[ContentChunk]):
    def __init__(self, db: Session):
        super().__init__(ContentChunk, db)

    def list_by_filter(
        self,
        chapter_id: Optional[str] = None,
        concept_id: Optional[str] = None,
        approval_state: str = ApprovalState.APPROVED.value,
        limit: int = 20,
    ) -> List[ContentChunk]:
        stmt = select(ContentChunk).where(ContentChunk.approval_state == approval_state)
        if chapter_id:
            stmt = stmt.where(ContentChunk.chapter_id == chapter_id)
        if concept_id:
            stmt = stmt.where(ContentChunk.concept_id == concept_id)
        stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())
