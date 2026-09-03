import os
import unittest
from unittest.mock import patch
from uuid import uuid4

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from redis.asyncio import Redis

from app.queue import producer as queue_producer
from app.queue import worker as queue_worker
from app.queue.connection import REDIS_URL


@unittest.skipUnless(
    os.getenv("RUN_REDIS_TESTS") == "1",
    "set RUN_REDIS_TESTS=1 to run Redis integration tests",
)
class RedisQueueIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_consumers_share_jobs_and_duplicate_lock_is_released(self):
        suffix = uuid4().hex
        stream = f"test:uptime:jobs:{suffix}"
        group = f"test-workers:{suffix}"
        dead_stream = f"test:uptime:dead:{suffix}"
        lock_prefix = f"test:uptime:outstanding:{suffix}"
        client = Redis.from_url(REDIS_URL, decode_responses=True)
        handled_by: dict[int, str] = {}

        async def worker_one_handler(monitor_id: int) -> None:
            handled_by[monitor_id] = "worker-one"

        async def worker_two_handler(monitor_id: int) -> None:
            handled_by[monitor_id] = "worker-two"

        patches = (
            patch.object(queue_producer, "MONITOR_STREAM", stream),
            patch.object(
                queue_producer,
                "MONITOR_JOB_LOCK_PREFIX",
                lock_prefix,
            ),
            patch.object(queue_worker, "MONITOR_STREAM", stream),
            patch.object(queue_worker, "MONITOR_CONSUMER_GROUP", group),
            patch.object(
                queue_worker,
                "MONITOR_DEAD_LETTER_STREAM",
                dead_stream,
            ),
        )

        try:
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                worker_one = queue_worker.MonitorStreamWorker(
                    worker_one_handler,
                    client=client,
                    consumer_name="worker-one",
                )
                worker_two = queue_worker.MonitorStreamWorker(
                    worker_two_handler,
                    client=client,
                    consumer_name="worker-two",
                )
                await worker_one.ensure_consumer_group()

                first_id = await queue_producer.enqueue_monitor_check(
                    101,
                    client=client,
                )
                duplicate_id = await queue_producer.enqueue_monitor_check(
                    101,
                    client=client,
                )

                self.assertIsNotNone(first_id)
                self.assertIsNone(duplicate_id)

                first_messages = await worker_one._read_new_jobs()
                self.assertEqual(len(first_messages), 1)
                await worker_one.process_message(*first_messages[0])

                second_id = await queue_producer.enqueue_monitor_check(
                    202,
                    client=client,
                )
                self.assertIsNotNone(second_id)

                second_messages = await worker_two._read_new_jobs()
                self.assertEqual(len(second_messages), 1)
                await worker_two.process_message(*second_messages[0])

                self.assertEqual(
                    handled_by,
                    {101: "worker-one", 202: "worker-two"},
                )
                self.assertEqual(await client.xlen(stream), 0)

                next_id = await queue_producer.enqueue_monitor_check(
                    101,
                    client=client,
                )
                self.assertIsNotNone(next_id)
        finally:
            await client.delete(
                stream,
                dead_stream,
                f"{lock_prefix}:101",
                f"{lock_prefix}:202",
            )
            await client.aclose()


if __name__ == "__main__":
    unittest.main()
