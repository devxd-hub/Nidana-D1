"""Endpoints for the 5-Question Mini-Mock workflow."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_service
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.mock_test import (
    MockResultResponse,
    MockSessionResponse,
    MockStartRequest,
    MockSubmitRequest,
)
from app.services.mock_service import MockService
from app.services.user_service import UserService

router = APIRouter(prefix="/mock", tags=["Mini-Mock"])


def get_mock_service(db: Session = Depends(get_db)) -> MockService:
    return MockService(db)


@router.post(
    "/start",
    response_model=MockSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a 5-question mini-mock",
    description="Returns 5 curriculum questions for the specified class. Answer keys are strictly omitted.",
)
def start_mini_mock(
    payload: MockStartRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    mock_service: MockService = Depends(get_mock_service),
) -> MockSessionResponse:
    user_service.get_or_create_from_token(current_user)
    return mock_service.start_mini_mock(user=current_user, payload=payload)


@router.post(
    "/{session_id}/submit",
    response_model=MockResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit mini-mock for authoritative server grading",
    description="Calculates scores, records individual attempts, and initiates diagnostics for incorrect answers.",
)
def submit_mini_mock(
    session_id: str,
    payload: MockSubmitRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    mock_service: MockService = Depends(get_mock_service),
) -> MockResultResponse:
    return mock_service.submit_mini_mock(session_id=session_id, user=current_user, payload=payload)
