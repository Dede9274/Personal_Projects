"""Shared incident domain types."""

from enum import Enum


class IncidentStatus(str, Enum):
    """Valid lifecycle states for an incident."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


ACTIVE_INCIDENT_STATUSES = (
    IncidentStatus.OPEN.value,
    IncidentStatus.INVESTIGATING.value,
)


class IncidentTransitionError(ValueError):
    """Raised when an incident lifecycle transition is not allowed."""
