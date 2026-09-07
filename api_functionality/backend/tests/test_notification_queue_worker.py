import os
import unittest
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.models.notification import NotificationChannel
from app.queue import (
    NOTIFICATION_DEAD_LETTER_STREAM,
    NOTIFICATION_STREAM,
)
from app.queue.notification_worker import (
    NotificationJob,
    NotificationStreamWorker,
)


class FakePipeline:
    def __init__(self):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def set(self, *args, **kwargs):
        self.calls.append(("set", args, kwargs))
        return self

    def xadd(self, *args, **kwargs):
        self.calls.append(("xadd", args, kwargs))
        return self

    def xack(self, *args, **kwargs):
        self.calls.append(("xack", args, kwargs))
        return self

    def xdel(self, *args, **kwargs):
        self.calls.append(("xdel", args, kwargs))
        return self

    async def execute(self):
        self.calls.append(("execute", (), {}))
        return []


class FakeRedis:
    def __init__(self):
        self.last_pipeline = None

    def pipeline(self, **kwargs):
        self.last_pipeline = FakePipeline()
        return self.last_pipeline


def make_job(attempt: int = 1) -> NotificationJob:
    return NotificationJob(
        message_id="1-0",
        incident_id=42,
        monitor_id=7,
        channel=NotificationChannel.EMAIL,
        event_type="INCIDENT_OPENED",
        attempt=attempt,
    )


class NotificationQueueWorkerTests(unittest.IsolatedAsyncioTestCase):
    def make_worker(self, handler=None):
        return NotificationStreamWorker(
            handler or AsyncMock(),
            client=AsyncMock(),
            consumer_name="notification-test",
        )

    async def test_valid_job_dispatches_its_channel(self):
        handler = AsyncMock()
        worker = self.make_worker(handler)

        with patch.object(
            worker,
            "_acknowledge_and_mark_sent",
            AsyncMock(),
        ) as acknowledge_mock:
            await worker.process_message(
                "1-0",
                {
                    "incident_id": "42",
                    "monitor_id": "7",
                    "channel": "WEBHOOK",
                    "event_type": "INCIDENT_OPENED",
                    "attempt": "1",
                },
            )

        handler.assert_awaited_once_with(
            42,
            7,
            NotificationChannel.WEBHOOK,
        )
        acknowledge_mock.assert_awaited_once()

    async def test_handler_failure_enters_retry_flow(self):
        handler = AsyncMock(side_effect=RuntimeError("SMTP unavailable"))
        worker = self.make_worker(handler)

        with patch.object(
            worker,
            "_retry_or_dead_letter",
            AsyncMock(),
        ) as retry_mock:
            await worker.process_message(
                "1-0",
                {
                    "incident_id": "42",
                    "monitor_id": "7",
                    "channel": "EMAIL",
                    "event_type": "INCIDENT_OPENED",
                    "attempt": "2",
                },
            )

        retry_mock.assert_awaited_once()

    async def test_success_marks_only_this_channel_sent(self):
        client = FakeRedis()
        worker = NotificationStreamWorker(
            AsyncMock(),
            client=client,
            consumer_name="notification-test",
        )

        await worker._acknowledge_and_mark_sent(make_job())

        calls = client.last_pipeline.calls
        self.assertEqual(
            [call[0] for call in calls],
            ["set", "xack", "xdel", "execute"],
        )
        self.assertTrue(calls[0][1][0].endswith(":42:email"))
        self.assertEqual(calls[0][1][1], "SENT")

    async def test_retry_preserves_delivery_lock(self):
        client = FakeRedis()
        worker = NotificationStreamWorker(
            AsyncMock(),
            client=client,
            consumer_name="notification-test",
        )

        await worker._retry_or_dead_letter(
            make_job(attempt=1),
            RuntimeError("temporary"),
        )

        calls = client.last_pipeline.calls
        self.assertEqual(
            [call[0] for call in calls],
            ["xadd", "xack", "xdel", "execute"],
        )
        self.assertEqual(calls[0][1][0], NOTIFICATION_STREAM)
        self.assertEqual(calls[0][1][1]["attempt"], "2")

    async def test_final_failure_is_dead_lettered_and_marked_failed(self):
        client = FakeRedis()
        worker = NotificationStreamWorker(
            AsyncMock(),
            client=client,
            consumer_name="notification-test",
            max_attempts=3,
        )

        await worker._retry_or_dead_letter(
            make_job(attempt=3),
            RuntimeError("permanent"),
        )

        calls = client.last_pipeline.calls
        self.assertEqual(
            [call[0] for call in calls],
            ["xadd", "set", "xack", "xdel", "execute"],
        )
        self.assertEqual(
            calls[0][1][0],
            NOTIFICATION_DEAD_LETTER_STREAM,
        )
        self.assertEqual(calls[1][1][1], "FAILED")

    async def test_unknown_channel_is_dead_lettered(self):
        handler = AsyncMock()
        worker = self.make_worker(handler)

        with patch.object(
            worker,
            "_dead_letter_invalid_message",
            AsyncMock(),
        ) as dead_letter_mock:
            await worker.process_message(
                "1-0",
                {
                    "incident_id": "42",
                    "monitor_id": "7",
                    "channel": "SMS",
                    "event_type": "INCIDENT_OPENED",
                },
            )

        handler.assert_not_awaited()
        dead_letter_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
