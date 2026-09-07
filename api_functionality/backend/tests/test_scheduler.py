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

    def test_reconcile_adds_updates_and_removes_monitors(self):
        existing = Monitor(
            id=1,
            name="Existing",
            url="https://old.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        removed = Monitor(
            id=2,
            name="Removed",
            url="https://removed.test",
            interval_seconds=20,
            timeout_seconds=1,
        )
        scheduler = Scheduler([existing, removed])
        original_scheduled_monitor = scheduler.schedule[0]
        original_scheduled_monitor.next_run = 75

        updated = Monitor(
            id=1,
            name="Updated",
            url="https://new.test",
            interval_seconds=30,
            timeout_seconds=2,
        )
        added = Monitor(
            id=3,
            name="Added",
            url="https://added.test",
            interval_seconds=15,
            timeout_seconds=1,
        )

        scheduler.reconcile_monitors(
            [updated, added],
            current_time=100,
        )

        self.assertEqual(
            [item.monitor.id for item in scheduler.schedule],
            [1, 3],
        )
        self.assertIs(scheduler.schedule[0], original_scheduled_monitor)
        self.assertEqual(scheduler.schedule[0].monitor, updated)
        self.assertEqual(scheduler.schedule[0].next_run, 130)
        self.assertEqual(scheduler.schedule[1].next_run, 100)

    def test_reconcile_preserves_cadence_when_interval_is_unchanged(self):
        monitor = Monitor(
            id=1,
            name="Before",
            url="https://before.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        scheduler = Scheduler([monitor])
        scheduler.schedule[0].next_run = 123

        changed = Monitor(
            id=1,
            name="After",
            url="https://after.test",
            interval_seconds=10,
            timeout_seconds=3,
        )
        scheduler.reconcile_monitors([changed], current_time=100)

        self.assertEqual(scheduler.schedule[0].monitor, changed)
        self.assertEqual(scheduler.schedule[0].next_run, 123)

    def test_reconcile_requires_persisted_unique_monitors(self):
        unsaved = Monitor(
            name="Unsaved",
            url="https://example.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        scheduler = Scheduler()

        with self.assertRaises(ValueError):
            scheduler.reconcile_monitors([unsaved])

        duplicate = Monitor(
            id=1,
            name="Duplicate",
            url="https://duplicate.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        with self.assertRaises(ValueError):
            scheduler.reconcile_monitors([duplicate, duplicate])

    async def test_empty_scheduler_keeps_refreshing_and_finds_new_monitor(self):
        monitor = Monitor(
            id=9,
            name="Created through API",
            url="https://created.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        refresh_count = 0

        async def load_monitors():
            nonlocal refresh_count
            refresh_count += 1
            return [] if refresh_count == 1 else [monitor]

        loader = AsyncMock(side_effect=load_monitors)
        scheduler = Scheduler(
            monitor_loader=loader,
            refresh_interval_seconds=0.01,
            poll_interval_seconds=0.005,
        )

        async def stop_soon():
            await asyncio.sleep(0.04)
            scheduler.stop()

        with patch(
            "app.services.scheduler.enqueue_monitor_check",
            AsyncMock(return_value="1-0"),
        ) as enqueue_mock:
            await asyncio.gather(scheduler.run(), stop_soon())

        self.assertGreaterEqual(loader.await_count, 2)
        enqueue_mock.assert_awaited_once_with(9)

    async def test_refresh_failure_keeps_last_known_schedule(self):
        monitor = Monitor(
            id=4,
            name="Known",
            url="https://known.test",
            interval_seconds=10,
            timeout_seconds=1,
        )
        loader = AsyncMock(side_effect=RuntimeError("database unavailable"))
        scheduler = Scheduler(
            [monitor],
            monitor_loader=loader,
            refresh_interval_seconds=0.01,
            poll_interval_seconds=0.005,
        )

        async def stop_soon():
            await asyncio.sleep(0.02)
            scheduler.stop()

        with patch(
            "app.services.scheduler.enqueue_monitor_check",
            AsyncMock(return_value="1-0"),
        ) as enqueue_mock:
            await asyncio.gather(scheduler.run(), stop_soon())

        self.assertEqual(len(scheduler.schedule), 1)
        enqueue_mock.assert_awaited_once_with(4)


if __name__ == "__main__":
    unittest.main()
