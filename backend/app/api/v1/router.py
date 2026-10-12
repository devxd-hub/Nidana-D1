"""API v1 master router."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    attempts,
    chapters,
    concepts,
    health,
    questions,
    study_plans,
    subjects,
    users,
)

api_v1_router = APIRouter(prefix="/api/v1")

# Mount endpoints
api_v1_router.include_router(health.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(subjects.router)
api_v1_router.include_router(chapters.router)
api_v1_router.include_router(concepts.router)
api_v1_router.include_router(questions.router)
api_v1_router.include_router(attempts.router)
api_v1_router.include_router(study_plans.router)
