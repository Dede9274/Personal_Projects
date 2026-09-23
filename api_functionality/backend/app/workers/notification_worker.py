"""Standalone worker that delivers email and webhook notifications."""

import argparse
import asyncio
import logging
import sys

from app.database.connection import engine
from app.database.repository import (
    get_incident,
    get_monitor_by_id,
    get_notification_preferences,
)
from app.models.notification import NotificationChannel
from app.notifications.config import (
    get_email_settings,
    get_webhook_settings,
)
from app.notifications.email import send_incident_opened_email
from app.notifications.webhook import send_incident_opened_webhook
from app.queue.connection import (
    check_redis_connection,
    close_redis_connection,
)
from app.queue.notification_worker import NotificationStreamWorker


logger = logging.getLogger(__name__)


async def execute_notification_job(
    incident_id: int,
    monitor_id: int,
    channel: NotificationChannel,
) -> None:
    """Load current data and deliver one channel-specific notification."""
    incident = await get_incident(incident_id)
    monitor = await get_monitor_by_id(monitor_id)

    if incident is None:
        logger.info(
            "Skipping notification because incident %s no longer exists",
            incident_id,
        )
        return

    if monitor is None:
        logger.info(
            "Skipping notification because monitor %s no longer exists",
            monitor_id,
        )
        return

    if incident.monitor_id != monitor_id:
        raise RuntimeError(
            f"Incident {incident_id} does not belong to monitor {monitor_id}"
        )

    preferences = await get_notification_preferences()

    if not preferences.notify_incident_opened:
        logger.info(
            "Skipping %s notification because incident alerts are disabled",
            channel.value,
        )
        return

    if channel is NotificationChannel.EMAIL:
        if not preferences.email_enabled:
            logger.info(
                "Skipping email notification because email is disabled"
            )
            return

        await send_incident_opened_email(
            incident=incident,
            monitor=monitor,
            settings=get_email_settings(
                recipients=preferences.email_recipients,
                timeout_seconds=preferences.email_timeout_seconds,
            ),
        )
    elif channel is NotificationChannel.WEBHOOK:
        if not preferences.webhook_enabled:
            logger.info(
                "Skipping webhook notification because webhooks are disabled"
            )
            return

        await send_incident_opened_webhook(
            incident=incident,
            monitor=monitor,
            settings=get_webhook_settings(
                url=preferences.webhook_url,
                timeout_seconds=preferences.webhook_timeout_seconds,
            ),
        )
    else:
        raise ValueError(f"Unsupported notification channel: {channel}")

    logger.info(
        "Sent %s notification for incident %s",
        channel.value,
        incident_id,
    )


async def main(consumer_name: str | None = None) -> None:
    worker = NotificationStreamWorker(
        execute_notification_job,
        consumer_name=consumer_name,
    )

    try:
        await check_redis_connection()
        await worker.run()
    finally:
        await close_redis_connection()
        await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an email/webhook notification worker"
    )
    parser.add_argument(
        "--name",
        dest="consumer_name",
        help="Unique Redis consumer name; defaults to hostname-process_id",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )

        asyncio.run(main(arguments.consumer_name))
    except KeyboardInterrupt:
        print("\nNotification worker interrupted")
