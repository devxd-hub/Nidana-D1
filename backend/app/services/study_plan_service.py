"""Study plan service for learner intervention tracking."""

from typing import Optional
from sqlalchemy.orm import Session

from app.core.errors import APIErrorCode, APIException
from app.core.security import AuthenticatedUser, enforce_ownership
from app.models.study_plan import StudyPlan, StudyPlanTask
from app.repositories.study_plan_repo import StudyPlanRepository
from app.schemas.study_plan import StudyPlanTaskUpdate


class StudyPlanService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StudyPlanRepository(db)

    def get_user_plan(self, user: AuthenticatedUser) -> Optional[StudyPlan]:
        """Fetch study plan for caller."""
        return self.repo.get_by_user(user.id)

    def update_task_status(
        self, task_id: str, user: AuthenticatedUser, payload: StudyPlanTaskUpdate
    ) -> StudyPlanTask:
        """Update task status with ownership validation."""
        task = self.repo.get_task(task_id)
        if not task:
            raise APIException(
                status_code=404,
                error_code=APIErrorCode.RESOURCE_NOT_FOUND,
                message=f"Study plan task '{task_id}' not found.",
            )
        # Ensure task belongs to user's plan
        plan = self.repo.get_by_id(task.study_plan_id)
        if not plan:
            raise APIException(status_code=404, error_code=APIErrorCode.RESOURCE_NOT_FOUND, message="Plan not found")
        enforce_ownership(plan.user_id, user)

        if payload.status:
            task.status = payload.status.value
        self.db.flush()
        return task
