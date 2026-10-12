"""Question and QuestionVariant repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ApprovalState
from app.models.question import Question, QuestionVariant
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    def __init__(self, db: Session):
        super().__init__(Question, db)

    def list_by_filter(
        self,
        chapter_id: Optional[str] = None,
        concept_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        approval_state: str = ApprovalState.APPROVED.value,
        limit: int = 50,
    ) -> List[Question]:
        stmt = select(Question).where(Question.approval_state == approval_state)
        if chapter_id:
            stmt = stmt.where(Question.chapter_id == chapter_id)
        if concept_id:
            stmt = stmt.where(Question.concept_id == concept_id)
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)
        stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_variant_by_id(self, variant_id: str) -> Optional[QuestionVariant]:
        return self.db.get(QuestionVariant, variant_id)

    def list_variants_for_question(self, question_id: str) -> List[QuestionVariant]:
        stmt = (
            select(QuestionVariant)
            .where(QuestionVariant.base_question_id == question_id)
            .where(QuestionVariant.approval_state == ApprovalState.APPROVED.value)
        )
        return list(self.db.scalars(stmt).all())

    def create_variant(self, variant: QuestionVariant) -> QuestionVariant:
        self.db.add(variant)
        self.db.flush()
        return variant
