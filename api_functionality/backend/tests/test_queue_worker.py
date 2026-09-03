import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from redis.exceptions import ResponseError

from app.queue import MONITOR_DEAD_LETTER_STREAM, MONITOR_STREAM
from app.queue.worker import MonitorJob, MonitorStreamWorker


class FakePipeline:
    def __init__(self):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def xadd(self, *args, **kwargs):
        self.calls.append(("xadd", args, kwargs))
        return self

    def xack(self, *args, **kwargs):
        self.calls.append(("xack", args, kwargs))
        return self

    def xdel(self, *args, **kwargs):
        self.calls.append(("xdel", args, kwargs))
        return self

    def delete(self, *args, **kwargs):
        self.calls.append(("delete", args, kwargs))
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


class QueueWorkerTests(unittest.IsolatedAsyncioTestCase):
    def make_worker(self, handler=None):
        return MonitorStreamWorker(
            handler or AsyncMock(),
            client=AsyncMock(),
            consumer_name="worker-test",
        )

    async def test_successful_job_is_acknowledged(self):
        handler = AsyncMock()
        worker = self.make_worker(handler)

        with patch.object(
            worker,
            "_acknowledge_and_release",
            AsyncMock(),
        ) as acknowledge_mock:
            await worker.process_message(
                "1-0",
                {"monitor_id": "7", "attempt": "1"},
            )

        handler.assert_awaited_once_with(7)
        acknowledge_mock.assert_awaited_once()

    async def test_failed_job_enters_retry_flow(self):
        handler = AsyncMock(side_effect=RuntimeError("database unavailable"))
        worker = self.make_worker(handler)

        with patch.object(
            worker,
            "_retry_or_dead_letter",
            AsyncMock(),
        ) as retry_mock:
            await worker.process_message(
                "1-0",
                {"monitor_id": "7", "attempt": "2"},
            )

        retry_mock.assert_awaited_once()
        job, error = retry_mock.await_args.args
        self.assertEqual(job.monitor_id, 7)
        self.assertEqual(job.attempt, 2)
        self.assertIsInstance(error, RuntimeError)

    async def test_invalid_job_is_dead_lettered_without_running_handler(self):
        handler = AsyncMock()
        worker = self.make_worker(handler)

        with patch.object(
            worker,
            "_dead_letter_invalid_message",
            AsyncMock(),
        ) as dead_letter_mock:
            await worker.process_message(
                "1-0",
                {"monitor_id": "not-an-integer"},
            )

        handler.assert_not_awaited()
        dead_letter_mock.assert_awaited_once()

    async def test_existing_consumer_group_is_allowed(self):
        worker = self.make_worker()
        worker.client.xgroup_create.side_effect = ResponseError(
            "BUSYGROUP Consumer Group name already exists"
        )

        await worker.ensure_consumer_group()

    async def test_unexpected_group_creation_error_is_raised(self):
        worker = self.make_worker()
        worker.client.xgroup_create.side_effect = ResponseError(
            "Redis is read only"
        )

        with self.assertRaises(ResponseError):
            await worker.ensure_consumer_group()

    async def test_heartbeat_refreshes_job_ownership(self):
        worker = self.make_worker()
        job = MonitorJob(message_id="1-0", monitor_id=7, attempt=1)

        sleep_calls = 0

        async def stop_after_first_sleep(_delay):
            nonlocal sleep_calls
            sleep_calls += 1
            if sleep_calls > 1:
                raise asyncio.CancelledError

        with patch(
            "app.queue.worker.asyncio.sleep",
            side_effect=stop_after_first_sleep,
        ):
            with self.assertRaises(asyncio.CancelledError):
                await worker._heartbeat(job)

        worker.client.xclaim.assert_awaited_once_with(
            MONITOR_STREAM,
            "monitor-workers",
            "worker-test",
            min_idle_time=0,
            message_ids=["1-0"],
            idle=0,
            justid=True,
        )

    async def test_slow_handler_heartbeats_before_acknowledgement(self):
        handler_started = asyncio.Event()
        allow_handler_to_finish = asyncio.Event()

        async def slow_handler(_monitor_id):
            handler_started.set()
            await allow_handler_to_finish.wait()

        worker = MonitorStreamWorker(
            slow_handler,
            client=AsyncMock(),
            consumer_name="worker-test",
            claim_idle_ms=300,
        )

        with patch.object(
            worker,
            "_acknowledge_and_release",
            AsyncMock(),
        ) as acknowledge_mock:
            processing = asyncio.create_task(
                worker.process_message(
                    "1-0",
                    {"monitor_id": "7", "attempt": "1"},
                )
            )
            await asyncio.wait_for(handler_started.wait(), timeout=1)

            for _ in range(20):
                if worker.client.xclaim.await_count > 0:
                    break
                await asyncio.sleep(0.02)

            self.assertGreater(worker.client.xclaim.await_count, 0)
            acknowledge_mock.assert_not_awaited()

            allow_handler_to_finish.set()
            await asyncio.wait_for(processing, timeout=1)

        acknowledge_mock.assert_awaited_once()

    async def test_retry_requeues_then_acknowledges_source_message(self):
        client = FakeRedis()
        worker = MonitorStreamWorker(
            AsyncMock(),
            client=client,
            consumer_name="worker-test",
            max_attempts=3,
        )
        job = MonitorJob(message_id="1-0", monitor_id=7, attempt=1)

        await worker._retry_or_dead_letter(job, RuntimeError("temporary"))

        calls = client.last_pipeline.calls
        self.assertEqual(
            [call[0] for call in calls],
            ["xadd", "xack", "xdel", "execute"],
        )
        self.assertEqual(calls[0][1][0], MONITOR_STREAM)
        self.assertEqual(calls[0][1][1]["attempt"], "2")

    async def test_final_failure_is_dead_lettered_and_releases_lock(self):
        client = FakeRedis()
        worker = MonitorStreamWorker(
            AsyncMock(),
            client=client,
            consumer_name="worker-test",
            max_attempts=3,
        )
        job = MonitorJob(message_id="1-0", monitor_id=7, attempt=3)

        await worker._retry_or_dead_letter(job, RuntimeError("permanent"))

        calls = client.last_pipeline.calls
        self.assertEqual(
            [call[0] for call in calls],
            ["xadd", "delete", "xack", "xdel", "execute"],
        )
        self.assertEqual(calls[0][1][0], MONITOR_DEAD_LETTER_STREAM)

    async def test_success_acknowledges_deletes_and_releases_lock(self):
        client = FakeRedis()
        worker = MonitorStreamWorker(
            AsyncMock(),
            client=client,
            consumer_name="worker-test",
        )
        job = MonitorJob(message_id="1-0", monitor_id=7, attempt=1)

        await worker._acknowledge_and_release(job)

        self.assertEqual(
            [call[0] for call in client.last_pipeline.calls],
            ["xack", "xdel", "delete", "execute"],
        )


if __name__ == "__main__":
    unittest.main()
