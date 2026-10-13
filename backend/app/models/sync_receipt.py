"""Sync receipt domain model for client event tracking and offline synchronization."""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SyncReceipt(Base, TimestampMixin):
    """Authoritative ledger entry for client offline-sync events.

    Ensures idempotency and deduplication when client sync queues are replayed.
    """

    __tablename__ = "sync_receipts"
    __table_args__ = (
        Index("ix_sync_receipts_client_event", "client_event_id", unique=True),
        Index("ix_sync_receipts_user_status", "user_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    client_event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # ATTEMPT_SUBMIT, OFFLINE_DIAGNOSIS
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACCEPTED", nullable=False)  # ACCEPTED, DUPLICATE, REJECTED, CONFLICT
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
