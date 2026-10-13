"""Endpoints for offline content pack downloads and idempotent sync."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_service
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.sync import (
    ContentPackBundle,
    ContentPackManifest,
    SyncBatchRequest,
    SyncBatchResponse,
)
from app.services.sync_service import SyncService
from app.services.user_service import UserService

router = APIRouter(prefix="/sync", tags=["Offline Packs & Sync"])


def get_sync_service(db: Session = Depends(get_db)) -> SyncService:
    return SyncService(db)


@router.get("/packs", response_model=List[ContentPackManifest], summary="List available offline content packs")
def list_content_packs(
    sync_service: SyncService = Depends(get_sync_service),
) -> List[ContentPackManifest]:
    return sync_service.list_packs()


@router.get("/packs/{pack_id}", response_model=ContentPackBundle, summary="Download full offline content pack bundle")
def get_content_pack_bundle(
    pack_id: str,
    sync_service: SyncService = Depends(get_sync_service),
) -> ContentPackBundle:
    return sync_service.get_pack_bundle(pack_id=pack_id)


@router.post("/batch", response_model=SyncBatchResponse, status_code=status.HTTP_200_OK, summary="Sync offline attempt events idempotently")
def sync_event_batch(
    payload: SyncBatchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    sync_service: SyncService = Depends(get_sync_service),
) -> SyncBatchResponse:
    user_service.get_or_create_from_token(current_user)
    return sync_service.process_sync_batch(user=current_user, payload=payload)
