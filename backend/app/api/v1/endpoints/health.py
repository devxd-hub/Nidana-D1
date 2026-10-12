"""Health check endpoint providing safe liveness and readiness status."""

from fastapi import APIRouter, status
from app.core.config import get_settings
from app.db.session import check_database_health
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns service liveness and database readiness. Excludes secrets and internal host configurations.",
)
def get_health() -> HealthResponse:
    settings = get_settings()
    is_db_up = check_database_health()
    return HealthResponse(
        status="ok" if is_db_up else "degraded",
        version=settings.APP_VERSION,
        database_connected=is_db_up,
    )
