"""Content and syllabus hierarchy service (Subjects, Chapters, Concepts, ContentChunks)."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.constants import ClassLevel
from app.core.errors import APIErrorCode, APIException
from app.models.chapter import Chapter
from app.models.concept import Concept
from app.models.content_chunk import ContentChunk
from app.models.subject import Subject
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.concept_repo import ConceptRepository
from app.repositories.content_chunk_repo import ContentChunkRepository
from app.repositories.subject_repo import SubjectRepository
from app.schemas.chapter import ChapterCreate
from app.schemas.concept import ConceptCreate
from app.schemas.content_chunk import ContentChunkCreate
from app.schemas.subject import SubjectCreate


class ContentService:
    def __init__(self, db: Session):
        self.db = db
        self.subject_repo = SubjectRepository(db)
        self.chapter_repo = ChapterRepository(db)
        self.concept_repo = ConceptRepository(db)
        self.chunk_repo = ContentChunkRepository(db)

    # ----------------- Subjects -----------------
    def list_subjects(self) -> List[Subject]:
        return self.subject_repo.list_active()

    def get_subject(self, subject_id: str) -> Subject:
        subject = self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise APIException(
                status_code=404,
                error_code=APIErrorCode.RESOURCE_NOT_FOUND,
                message=f"Subject '{subject_id}' not found.",
            )
        return subject

    def create_subject(self, payload: SubjectCreate) -> Subject:
        if self.subject_repo.get_by_id(payload.id):
            raise APIException(
                status_code=409,
                error_code=APIErrorCode.RESOURCE_CONFLICT,
                message=f"Subject with ID '{payload.id}' already exists.",
            )
        subject = Subject(**payload.model_dump())
        return self.subject_repo.create(subject)

    # ----------------- Chapters -----------------
    def list_chapters(
        self, subject_id: Optional[str] = None, class_level: Optional[int] = None
    ) -> List[Chapter]:
        if class_level is not None and class_level not in ClassLevel.values():
            raise APIException(
                status_code=422,
                error_code=APIErrorCode.INVALID_CLASS_LEVEL,
                message=f"Class level {class_level} is invalid. Supported class levels are {ClassLevel.values()}.",
            )
        return self.chapter_repo.list_by_filter(subject_id=subject_id, class_level=class_level)

    def get_chapter(self, chapter_id: str) -> Chapter:
        chapter = self.chapter_repo.get_by_id(chapter_id)
        if not chapter:
            raise APIException(
                status_code=404,
                error_code=APIErrorCode.RESOURCE_NOT_FOUND,
                message=f"Chapter '{chapter_id}' not found.",
            )
        return chapter

    def create_chapter(self, payload: ChapterCreate) -> Chapter:
        if payload.class_level not in ClassLevel.values():
            raise APIException(
                status_code=422,
                error_code=APIErrorCode.INVALID_CLASS_LEVEL,
                message=f"Class level {payload.class_level} is invalid. Supported: {ClassLevel.values()}",
            )
        self.get_subject(payload.subject_id)
        if self.chapter_repo.get_by_id(payload.id):
            raise APIException(
                status_code=409,
                error_code=APIErrorCode.RESOURCE_CONFLICT,
                message=f"Chapter '{payload.id}' already exists.",
            )
        chapter = Chapter(**payload.model_dump())
        return self.chapter_repo.create(chapter)

    # ----------------- Concepts -----------------
    def list_concepts(
        self, subject_id: Optional[str] = None, chapter_id: Optional[str] = None
    ) -> List[Concept]:
        return self.concept_repo.list_by_filter(subject_id=subject_id, chapter_id=chapter_id)

    def get_concept(self, concept_id: str) -> Concept:
        concept = self.concept_repo.get_by_id(concept_id)
        if not concept:
            raise APIException(
                status_code=404,
                error_code=APIErrorCode.RESOURCE_NOT_FOUND,
                message=f"Concept '{concept_id}' not found.",
            )
        return concept

    def create_concept(self, payload: ConceptCreate) -> Concept:
        self.get_subject(payload.subject_id)
        if payload.chapter_id:
            self.get_chapter(payload.chapter_id)
        if self.concept_repo.get_by_id(payload.id):
            raise APIException(
                status_code=409,
                error_code=APIErrorCode.RESOURCE_CONFLICT,
                message=f"Concept '{payload.id}' already exists.",
            )
        concept = Concept(**payload.model_dump())
        return self.concept_repo.create(concept)

    # ----------------- Content Chunks -----------------
    def list_content_chunks(
        self, chapter_id: Optional[str] = None, concept_id: Optional[str] = None
    ) -> List[ContentChunk]:
        return self.chunk_repo.list_by_filter(chapter_id=chapter_id, concept_id=concept_id)

    def create_content_chunk(self, payload: ContentChunkCreate) -> ContentChunk:
        self.get_chapter(payload.chapter_id)
        if payload.concept_id:
            self.get_concept(payload.concept_id)
        if self.chunk_repo.get_by_id(payload.id):
            raise APIException(
                status_code=409,
                error_code=APIErrorCode.RESOURCE_CONFLICT,
                message=f"Content chunk '{payload.id}' already exists.",
            )
        chunk = ContentChunk(**payload.model_dump())
        return self.chunk_repo.create(chunk)
