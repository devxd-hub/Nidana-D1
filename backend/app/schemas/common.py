"""Shared common schemas, health check responses, and uniform error structures."""

from datetime import datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness and readiness health status.

    Guarantees: Never exposes credentials, hosts, database strings, or internals.
    """

    status: str = Field(default="ok", description="Overall service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Current server timestamp (UTC)",
    )
    database_connected: bool = Field(description="Database connectivity status")


class ErrorDetail(BaseModel):
    """Detailed validation or context information."""

    loc: Optional[List[str]] = None
    msg: str
    type: Optional[str] = None


class APIErrorBody(BaseModel):
    """Inner error payload structure."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Safe human-readable error description")
    details: Optional[Any] = Field(default=None, description="Optional error metadata or validation items")


class APIErrorResponse(BaseModel):
    """Standardized root error response wrapper."""

    error: APIErrorBody
