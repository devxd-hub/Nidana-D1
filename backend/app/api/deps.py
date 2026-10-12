"""FastAPI dependency injections for sessions, authentication, and services."""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.services.attempt_service import AttemptService
from app.services.content_service import ContentService
from app.services.question_service import QuestionService
from app.services.study_plan_service import StudyPlanService
from app.services.user_service import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_content_service(db: Session = Depends(get_db)) -> ContentService:
    return ContentService(db)


def get_question_service(db: Session = Depends(get_db)) -> QuestionService:
    return QuestionService(db)


def get_attempt_service(db: Session = Depends(get_db)) -> AttemptService:
    return AttemptService(db)


def get_study_plan_service(db: Session = Depends(get_db)) -> StudyPlanService:
    return StudyPlanService(db)
