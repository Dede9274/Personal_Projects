"""Shared notification domain types."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class NotificationChannel(str, Enum):
    """Delivery channels supported by the notification worker."""

    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"


@dataclass(frozen=True, slots=True)
class NotificationPreferences:
    """Persisted choices that control notification delivery."""

    email_enabled: bool
    email_recipients: tuple[str, ...]
    email_timeout_seconds: float
    webhook_enabled: bool
    webhook_url: str | None
    webhook_timeout_seconds: float
    notify_incident_opened: bool
    updated_at: datetime

    def enabled_channels(self) -> tuple[NotificationChannel, ...]:
        if not self.notify_incident_opened:
            return ()

        channels: list[NotificationChannel] = []
        if self.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if self.webhook_enabled:
            channels.append(NotificationChannel.WEBHOOK)
        return tuple(channels)
