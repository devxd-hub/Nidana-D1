"""Schemas for Offline Content Packs and Idempotent Event Synchronization."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.question import QuestionPublic


class ContentPackManifest(BaseModel):
    """Manifest describing an offline curriculum package."""

    pack_id: str
    class_level: int
    subject_id: Optional[str]
    language: str
    version: str
    content_version: str
    checksum: str
    generated_at: datetime
    min_app_version: str = "1.0.0"
    item_counts: Dict[str, int]


class ContentPackBundle(BaseModel):
    """Self-contained, bounded package for offline IndexedDB/Dexie consumption."""

    manifest: ContentPackManifest
    chapters: List[Dict[str, Any]]
    concepts: List[Dict[str, Any]]
    questions: List[QuestionPublic]
    learning_chunks: List[Dict[str, Any]]
    offline_rules: Dict[str, Any]


class SyncEvent(BaseModel):
    """Individual client queued event representation."""

    client_event_id: str = Field(description="Client-generated unique ID (UUID or nanoid)")
    event_type: str = Field(description="Event type, e.g. 'ATTEMPT_SUBMIT'")
    payload_schema_version: str = Field(default="1.0.0")
    client_timestamp: datetime
    device_id: Optional[str] = None
    payload: Dict[str, Any] = Field(description="Event payload (e.g., question_id, selected_option, signals)")


class SyncBatchRequest(BaseModel):
    """Batch of queued events submitted by the client upon network restoration."""

    events: List[SyncEvent]


class SyncEventResult(BaseModel):
    """Per-event processing outcome ensuring idempotency and conflict reporting."""

    client_event_id: str
    status: str  # ACCEPTED, DUPLICATE, REJECTED, CONFLICT
    server_receipt_id: Optional[str] = None
    message: Optional[str] = None
    processed_data: Optional[Dict[str, Any]] = None


class SyncBatchResponse(BaseModel):
    """Overall batch outcome with per-event receipts."""

    batch_id: str
    accepted_count: int
    duplicate_count: int
    rejected_count: int
    event_results: List[SyncEventResult]
