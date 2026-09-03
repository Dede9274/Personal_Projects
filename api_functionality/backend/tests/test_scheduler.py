import os
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.models.monitor import Monitor
from app.services.scheduler import ScheduledMonitor, Scheduler


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    def test_nonpositive_interval_is_rejected(self):
        monitor = Monitor(
            id=1,
            name="Invalid",
            url="https://example.test",
            interval_seconds=0,
            timeout_seconds=1,
        )

        with self.assertRaises(ValueError):
            Scheduler([monitor])

    async def test_due_monitors_are_enqueued(self):
        monitors = [
            Monitor(
                id=1,
                name="A",
                url="https://a.test",
                interval_seconds=10,
                timeout_seconds=1,
            ),
            Monitor(
                id=2,
                name="B",
                url="https://b.test",
                interval_seconds=10,
                timeout_seconds=1,
            ),
        ]
        scheduler = Scheduler(monitors)
        enqueue_mock = AsyncMock(side_effect=["1-0", "2-0"])

        async def stop_soon():
            await asyncio.sleep(0.02)
            scheduler.stop()

        with patch(
            "app.services.scheduler.enqueue_monitor_check",
            enqueue_mock,
        ):
            await asyncio.gather(scheduler.run(), stop_soon())

        self.assertEqual(enqueue_mock.await_count, 2)
        enqueue_mock.assert_any_await(1)
        enqueue_mock.assert_any_await(2)
        self.assertFalse(scheduler.active_tasks)

    async def test_monitor_without_database_id_is_not_enqueued(self):
        monitor = Monitor(
            name="Unsaved",
            url="https://example.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        scheduler = Scheduler([monitor])
        scheduled_monitor = ScheduledMonitor(
            monitor=monitor,
            next_run=0,
            running=True,
        )

        with patch(
            "app.services.scheduler.enqueue_monitor_check",
            AsyncMock(),
        ) as enqueue_mock:
            with self.assertRaises(RuntimeError):
                await scheduler.execute_monitor(scheduled_monitor)

        enqueue_mock.assert_not_awaited()
        self.assertFalse(scheduled_monitor.running)

    async def test_existing_outstanding_job_is_not_duplicated(self):
        monitor = Monitor(
            id=7,
            name="Ordered",
            url="https://example.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        scheduler = Scheduler([monitor])
        scheduled_monitor = ScheduledMonitor(
            monitor=monitor,
            next_run=0,
            running=True,
        )
        with patch(
            "app.services.scheduler.enqueue_monitor_check",
            AsyncMock(return_value=None),
        ) as enqueue_mock:
            await scheduler.execute_monitor(scheduled_monitor)

        enqueue_mock.assert_awaited_once_with(7)
        self.assertFalse(scheduled_monitor.running)


if __name__ == "__main__":
    unittest.main()
