import os
import asyncio
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test",
)

from app.models.monitor import CheckResult, Monitor
from app.services.scheduler import ScheduledMonitor, Scheduler


def successful_result() -> CheckResult:
    return CheckResult(
        status_code=200,
        latency_ms=10,
        success=True,
        error=None,
        checked_at=datetime.now(timezone.utc),
    )


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

    async def test_due_monitors_are_checked_and_saved(self):
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
        check_mock = AsyncMock(return_value=successful_result())
        save_mock = AsyncMock()

        async def stop_soon():
            await asyncio.sleep(0.02)
            scheduler.stop()

        with (
            patch(
                "app.services.scheduler.check_monitor",
                check_mock,
            ),
            patch(
                "app.services.scheduler.save_check_result",
                save_mock,
            ),
        ):
            await asyncio.gather(scheduler.run(), stop_soon())

        self.assertEqual(check_mock.await_count, 2)
        self.assertEqual(save_mock.await_count, 2)
        self.assertFalse(scheduler.active_tasks)

    async def test_monitor_without_database_id_is_not_saved(self):
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

        with (
            patch(
                "app.services.scheduler.check_monitor",
                AsyncMock(return_value=successful_result()),
            ),
            patch(
                "app.services.scheduler.save_check_result",
                AsyncMock(),
            ) as save_mock,
        ):
            with self.assertRaises(RuntimeError):
                await scheduler.execute_monitor(scheduled_monitor)

        save_mock.assert_not_awaited()
        self.assertFalse(scheduled_monitor.running)


if __name__ == "__main__":
    unittest.main()
