import os
import unittest
from unittest.mock import AsyncMock

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.models.notification import NotificationChannel
from app.queue import NOTIFICATION_STREAM
from app.queue.notification_producer import (
    enqueue_incident_opened_notification,
    notification_lock_key,
)


class NotificationProducerTests(unittest.IsolatedAsyncioTestCase):
    async def test_enqueue_includes_channel_and_returns_message_id(self):
        client = AsyncMock()
        client.eval.return_value = b"123-0"

        message_id = await enqueue_incident_opened_notification(
            incident_id=42,
            monitor_id=7,
            channel=NotificationChannel.EMAIL,
            client=client,
        )

        self.assertEqual(message_id, "123-0")
        arguments = client.eval.await_args.args
        self.assertEqual(arguments[1], 2)
        self.assertEqual(
            arguments[2],
            notification_lock_key(42, NotificationChannel.EMAIL),
        )
        self.assertEqual(arguments[3], NOTIFICATION_STREAM)
        self.assertEqual(arguments[4:], ("42", "7", "EMAIL"))

    async def test_email_and_webhook_have_different_locks(self):
        self.assertNotEqual(
            notification_lock_key(42, NotificationChannel.EMAIL),
            notification_lock_key(42, NotificationChannel.WEBHOOK),
        )

    async def test_existing_delivery_returns_none(self):
        client = AsyncMock()
        client.eval.return_value = None

        message_id = await enqueue_incident_opened_notification(
            incident_id=42,
            monitor_id=7,
            channel=NotificationChannel.WEBHOOK,
            client=client,
        )

        self.assertIsNone(message_id)

    async def test_invalid_identifiers_are_rejected(self):
        client = AsyncMock()

        with self.assertRaises(ValueError):
            await enqueue_incident_opened_notification(
                incident_id=0,
                monitor_id=7,
                channel=NotificationChannel.EMAIL,
                client=client,
            )

        with self.assertRaises(ValueError):
            await enqueue_incident_opened_notification(
                incident_id=42,
                monitor_id=0,
                channel=NotificationChannel.EMAIL,
                client=client,
            )

        client.eval.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
