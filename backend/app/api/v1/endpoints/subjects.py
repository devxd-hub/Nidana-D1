"""Subjects endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from app.api.deps import get_content_service
from app.core.constants import UserRole
from app.core.security import AuthenticatedUser, require_role
from app.schemas.subject import SubjectCreate, SubjectRead
from app.services.content_service import ContentService

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("", response_model=List[SubjectRead], status_code=status.HTTP_200_OK)
def list_subjects(service: ContentService = Depends(get_content_service)) -> List[SubjectRead]:
    subjects = service.list_subjects()
    return [SubjectRead.model_validate(s) for s in subjects]


@router.get("/{subject_id}", response_model=SubjectRead, status_code=status.HTTP_200_OK)
def get_subject(subject_id: str, service: ContentService = Depends(get_content_service)) -> SubjectRead:
    subject = service.get_subject(subject_id)
    return SubjectRead.model_validate(subject)


@router.post(
    "",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
def create_subject(
    payload: SubjectCreate, service: ContentService = Depends(get_content_service)
) -> SubjectRead:
    subject = service.create_subject(payload)
    return SubjectRead.model_validate(subject)
