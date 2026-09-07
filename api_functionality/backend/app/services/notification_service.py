"""Decide which configured channels receive an incident notification."""

from app.models.notification import NotificationChannel
from app.notifications.config import get_enabled_notification_channels
from app.queue.notification_producer import (
    enqueue_incident_opened_notification,
)


async def enqueue_incident_opened_notifications(
    *,
    incident_id: int,
    monitor_id: int,
) -> dict[NotificationChannel, str | None]:
    """Enqueue one independent Redis job for each enabled channel."""
    queued_jobs: dict[NotificationChannel, str | None] = {}

    for channel in get_enabled_notification_channels():
        queued_jobs[channel] = await enqueue_incident_opened_notification(
            incident_id=incident_id,
            monitor_id=monitor_id,
            channel=channel,
        )

    return queued_jobs
