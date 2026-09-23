import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.database.models import IncidentDB
from app.models.monitor import Monitor
from app.models.notification import (
    NotificationChannel,
    NotificationPreferences,
)
from app.workers.notification_worker import execute_notification_job


def make_incident(monitor_id: int = 7) -> IncidentDB:
    started_at = datetime.now(timezone.utc)
    return IncidentDB(
        id=42,
        monitor_id=monitor_id,
        status="OPEN",
        started_at=started_at,
        last_failure_at=started_at,
        resolved_at=None,
        failure_count=3,
        last_error="Timeout",
    )


def make_monitor() -> Monitor:
    return Monitor(
        id=7,
        name="Production API",
        url="https://api.example.test",
        interval_seconds=30,
        timeout_seconds=5,
    )


def make_preferences() -> NotificationPreferences:
    return NotificationPreferences(
        email_enabled=True,
        email_recipients=("alerts@example.test",),
        email_timeout_seconds=10,
        webhook_enabled=True,
        webhook_url="https://hooks.example.test/uptime",
        webhook_timeout_seconds=10,
        notify_incident_opened=True,
        updated_at=datetime.now(timezone.utc),
    )


class NotificationWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_email_job_uses_only_email_sender(self):
        with (
            patch(
                "app.workers.notification_worker.get_incident",
                AsyncMock(return_value=make_incident()),
            ),
            patch(
                "app.workers.notification_worker.get_monitor_by_id",
                AsyncMock(return_value=make_monitor()),
            ),
            patch(
                "app.workers.notification_worker."
                "get_notification_preferences",
                AsyncMock(return_value=make_preferences()),
            ),
            patch(
                "app.workers.notification_worker.get_email_settings",
                return_value=object(),
            ),
            patch(
                "app.workers.notification_worker."
                "send_incident_opened_email",
                AsyncMock(),
            ) as email_mock,
            patch(
                "app.workers.notification_worker."
                "send_incident_opened_webhook",
                AsyncMock(),
            ) as webhook_mock,
        ):
            await execute_notification_job(
                42,
                7,
                NotificationChannel.EMAIL,
            )

        email_mock.assert_awaited_once()
        webhook_mock.assert_not_awaited()

    async def test_webhook_job_uses_only_webhook_sender(self):
        with (
            patch(
                "app.workers.notification_worker.get_incident",
                AsyncMock(return_value=make_incident()),
            ),
            patch(
                "app.workers.notification_worker.get_monitor_by_id",
                AsyncMock(return_value=make_monitor()),
            ),
            patch(
                "app.workers.notification_worker."
                "get_notification_preferences",
                AsyncMock(return_value=make_preferences()),
            ),
            patch(
                "app.workers.notification_worker.get_webhook_settings",
                return_value=object(),
            ),
            patch(
                "app.workers.notification_worker."
                "send_incident_opened_email",
                AsyncMock(),
            ) as email_mock,
            patch(
                "app.workers.notification_worker."
                "send_incident_opened_webhook",
                AsyncMock(),
            ) as webhook_mock,
        ):
            await execute_notification_job(
                42,
                7,
                NotificationChannel.WEBHOOK,
            )

        webhook_mock.assert_awaited_once()
        email_mock.assert_not_awaited()

    async def test_mismatched_monitor_is_rejected(self):
        with (
            patch(
                "app.workers.notification_worker.get_incident",
                AsyncMock(return_value=make_incident(monitor_id=8)),
            ),
            patch(
                "app.workers.notification_worker.get_monitor_by_id",
                AsyncMock(return_value=make_monitor()),
            ),
        ):
            with self.assertRaises(RuntimeError):
                await execute_notification_job(
                    42,
                    7,
                    NotificationChannel.EMAIL,
                )


if __name__ == "__main__":
    unittest.main()
