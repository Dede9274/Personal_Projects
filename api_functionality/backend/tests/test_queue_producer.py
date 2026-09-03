import os
import unittest
from unittest.mock import AsyncMock

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.queue import MONITOR_STREAM
from app.queue.producer import (
    enqueue_monitor_check,
    monitor_job_lock_key,
)


class QueueProducerTests(unittest.IsolatedAsyncioTestCase):
    async def test_enqueue_returns_stream_message_id(self):
        client = AsyncMock()
        client.eval.return_value = "123-0"

        message_id = await enqueue_monitor_check(7, client=client)

        self.assertEqual(message_id, "123-0")
        arguments = client.eval.await_args.args
        self.assertEqual(arguments[1], 2)
        self.assertEqual(arguments[2], monitor_job_lock_key(7))
        self.assertEqual(arguments[3], MONITOR_STREAM)
        self.assertEqual(arguments[4], "7")

    async def test_enqueue_returns_none_for_outstanding_monitor(self):
        client = AsyncMock()
        client.eval.return_value = None

        message_id = await enqueue_monitor_check(7, client=client)

        self.assertIsNone(message_id)

    async def test_enqueue_rejects_nonpositive_monitor_id(self):
        client = AsyncMock()

        with self.assertRaisesRegex(ValueError, "positive"):
            await enqueue_monitor_check(0, client=client)

        client.eval.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
