import os
import unittest
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.models.notification import NotificationChannel
from app.services.notification_service import (
    enqueue_incident_opened_notifications,
)


class NotificationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_enqueues_each_enabled_channel_independently(self):
        enqueue_mock = AsyncMock(side_effect=["1-0", "2-0"])

        with (
            patch(
                "app.services.notification_service."
                "get_enabled_notification_channels",
                return_value=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.WEBHOOK,
                ],
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
                "get_enabled_notification_channels",
                return_value=[],
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
