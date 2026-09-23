import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.models.notification import (
    NotificationChannel,
    NotificationPreferences,
)
from app.services.notification_service import (
    enqueue_incident_opened_notifications,
)


class NotificationServiceTests(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def preferences(
        *,
        email_enabled: bool,
        webhook_enabled: bool,
        notify_incident_opened: bool = True,
    ) -> NotificationPreferences:
        return NotificationPreferences(
            email_enabled=email_enabled,
            email_recipients=("alerts@example.test",),
            email_timeout_seconds=10,
            webhook_enabled=webhook_enabled,
            webhook_url="https://hooks.example.test/uptime",
            webhook_timeout_seconds=10,
            notify_incident_opened=notify_incident_opened,
            updated_at=datetime.now(timezone.utc),
        )

    async def test_enqueues_each_enabled_channel_independently(self):
        enqueue_mock = AsyncMock(side_effect=["1-0", "2-0"])

        with (
            patch(
                "app.services.notification_service."
                "get_notification_preferences",
                AsyncMock(
                    return_value=self.preferences(
                        email_enabled=True,
                        webhook_enabled=True,
                    )
                ),
            ),
            patch(
                "app.services.notification_service."
                "enqueue_incident_opened_notification",
                enqueue_mock,
            ),
        ):
            jobs = await enqueue_incident_opened_notifications(
                incident_id=42,
                monitor_id=7,
            )

        self.assertEqual(
            jobs,
            {
                NotificationChannel.EMAIL: "1-0",
                NotificationChannel.WEBHOOK: "2-0",
            },
        )
        self.assertEqual(enqueue_mock.await_count, 2)

    async def test_no_enabled_channels_creates_no_jobs(self):
        with (
            patch(
                "app.services.notification_service."
                "get_notification_preferences",
                AsyncMock(
                    return_value=self.preferences(
                        email_enabled=False,
                        webhook_enabled=False,
                    )
                ),
            ),
            patch(
                "app.services.notification_service."
                "enqueue_incident_opened_notification",
                AsyncMock(),
            ) as enqueue_mock,
        ):
            jobs = await enqueue_incident_opened_notifications(
                incident_id=42,
                monitor_id=7,
            )

        self.assertEqual(jobs, {})
        enqueue_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
