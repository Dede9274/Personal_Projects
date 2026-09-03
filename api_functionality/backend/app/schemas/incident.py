"""Response schemas for the incident API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.incident import IncidentStatus


class IncidentResponse(BaseModel):
    """Complete incident representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    monitor_id: int
    status: IncidentStatus
    started_at: datetime
    resolved_at: datetime | None
    failure_count: int
    last_error: str | None
    created_at: datetime
