"""Concepts endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_content_service
from app.core.constants import UserRole
from app.core.security import require_role
from app.schemas.concept import ConceptCreate, ConceptRead
from app.services.content_service import ContentService

router = APIRouter(prefix="/concepts", tags=["Concepts"])


@router.get("", response_model=List[ConceptRead], status_code=status.HTTP_200_OK)
def list_concepts(
    subject_id: Optional[str] = Query(default=None),
    chapter_id: Optional[str] = Query(default=None),
    service: ContentService = Depends(get_content_service),
) -> List[ConceptRead]:
    concepts = service.list_concepts(subject_id=subject_id, chapter_id=chapter_id)
    return [ConceptRead.model_validate(c) for c in concepts]


@router.get("/{concept_id}", response_model=ConceptRead, status_code=status.HTTP_200_OK)
def get_concept(concept_id: str, service: ContentService = Depends(get_content_service)) -> ConceptRead:
    concept = service.get_concept(concept_id)
    return ConceptRead.model_validate(concept)


@router.post(
    "",
    response_model=ConceptRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.EDUCATOR))],
)
def create_concept(
    payload: ConceptCreate, service: ContentService = Depends(get_content_service)
) -> ConceptRead:
    concept = service.create_concept(payload)
    return ConceptRead.model_validate(concept)
