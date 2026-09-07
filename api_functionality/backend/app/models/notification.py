"""Shared notification domain types."""

from enum import Enum


class NotificationChannel(str, Enum):
    """Delivery channels supported by the notification worker."""

    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"
