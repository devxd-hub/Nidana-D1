"""Study plan endpoints for post-autopsy interventions."""

from typing import Optional
from fastapi import APIRouter, Depends, status
from app.api.deps import get_study_plan_service
from app.core.errors import APIErrorCode, APIException
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.study_plan import StudyPlanRead, StudyPlanTaskRead, StudyPlanTaskUpdate
from app.services.study_plan_service import StudyPlanService

router = APIRouter(prefix="/study-plans", tags=["Study Plans"])


@router.get(
    "/me",
    response_model=Optional[StudyPlanRead],
    status_code=status.HTTP_200_OK,
    summary="Get current learner's active study plan",
)
def get_my_study_plan(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: StudyPlanService = Depends(get_study_plan_service),
) -> Optional[StudyPlanRead]:
    plan = service.get_user_plan(current_user)
    if not plan:
        return None
    return StudyPlanRead.model_validate(plan)


@router.patch(
    "/tasks/{task_id}",
    response_model=StudyPlanTaskRead,
    status_code=status.HTTP_200_OK,
    summary="Update study plan task status",
)
def update_task_status(
    task_id: str,
    payload: StudyPlanTaskUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: StudyPlanService = Depends(get_study_plan_service),
) -> StudyPlanTaskRead:
    task = service.update_task_status(task_id=task_id, user=current_user, payload=payload)
    return StudyPlanTaskRead.model_validate(task)
