"""Chapters endpoints with class-level filtering and validation."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_content_service
from app.core.constants import UserRole
from app.core.security import require_role
from app.schemas.chapter import ChapterCreate, ChapterRead
from app.services.content_service import ContentService

router = APIRouter(prefix="/chapters", tags=["Chapters"])


@router.get("", response_model=List[ChapterRead], status_code=status.HTTP_200_OK)
def list_chapters(
    subject_id: Optional[str] = Query(default=None, description="Filter by subject slug"),
    class_level: Optional[int] = Query(default=None, description="Filter by class level (9, 10, 12)"),
    service: ContentService = Depends(get_content_service),
) -> List[ChapterRead]:
    chapters = service.list_chapters(subject_id=subject_id, class_level=class_level)
    return [ChapterRead.model_validate(c) for c in chapters]


@router.get("/{chapter_id}", response_model=ChapterRead, status_code=status.HTTP_200_OK)
def get_chapter(chapter_id: str, service: ContentService = Depends(get_content_service)) -> ChapterRead:
    chapter = service.get_chapter(chapter_id)
    return ChapterRead.model_validate(chapter)


@router.post(
    "",
    response_model=ChapterRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.EDUCATOR))],
)
def create_chapter(
    payload: ChapterCreate, service: ContentService = Depends(get_content_service)
) -> ChapterRead:
    chapter = service.create_chapter(payload)
    return ChapterRead.model_validate(chapter)
