"""User management service."""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.core.constants import ExamTarget, PreferredLanguage, UserRole
from app.core.errors import APIErrorCode, APIException
from app.core.security import AuthenticatedUser
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def get_or_create_from_token(self, auth_user: AuthenticatedUser) -> User:
        """Synchronize or fetch database user record corresponding to the Supabase authenticated JWT."""
        user = self.repo.get_by_id(auth_user.id)
        if not user:
            logger.info("Registering initial user record for authenticated subject %s", auth_user.id)
            user = User(
                id=auth_user.id,
                email=auth_user.email or f"{auth_user.id}@nidana.local",
                display_name=auth_user.raw_payload.get("user_metadata", {}).get("display_name"),
                role=auth_user.role,
                preferred_language=PreferredLanguage.ODIA.value,
                exam_target=ExamTarget.CHSE_CLASS_12.value,
            )
            self.repo.create(user)
        return user

    def get_by_id(self, user_id: str) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise APIException(
                status_code=404,
                error_code=APIErrorCode.RESOURCE_NOT_FOUND,
                message=f"User profile with ID '{user_id}' was not found.",
            )
        return user

    def update_profile(self, user_id: str, update_data: UserUpdate) -> User:
        user = self.get_by_id(user_id)
        if update_data.display_name is not None:
            user.display_name = update_data.display_name
        if update_data.preferred_language is not None:
            user.preferred_language = update_data.preferred_language.value
        if update_data.exam_target is not None:
            user.exam_target = update_data.exam_target.value
        self.db.flush()
        return user
