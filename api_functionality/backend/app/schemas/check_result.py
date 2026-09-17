"""Response schemas for persisted monitor checks."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class CheckResultResponse(BaseModel):
    """One completed check returned by the monitor history API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    monitor_id: int
    checked_at: datetime
    status_code: int | None
    latency_ms: float
    success: bool
    error: str | None


class CheckEnqueueStatus(str, Enum):
    """Possible outcomes when a manual check is requested."""

    QUEUED = "queued"
    ALREADY_OUTSTANDING = "already_outstanding"


class CheckEnqueueResponse(BaseModel):
    """Describe whether a manual monitor check entered the queue."""

    monitor_id: int
    status: CheckEnqueueStatus
    job_id: str | None
