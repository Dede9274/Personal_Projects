"""Shared incident domain types."""

from enum import Enum


class IncidentStatus(str, Enum):
    """Valid lifecycle states for an incident."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
