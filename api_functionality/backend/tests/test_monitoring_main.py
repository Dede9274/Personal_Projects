import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.monitoring_main import main


class MonitoringMainTests(unittest.IsolatedAsyncioTestCase):
    async def test_component_failure_stops_its_sibling_and_cleans_up(self):
        scheduler_error = RuntimeError("scheduler failed")
        worker_started = asyncio.Event()
        worker_cancelled = asyncio.Event()

        async def fail_scheduler():
            await worker_started.wait()
            raise scheduler_error

        async def run_worker():
            worker_started.set()
            try:
                await asyncio.Event().wait()
            finally:
                worker_cancelled.set()

        scheduler = SimpleNamespace(
            run=AsyncMock(side_effect=fail_scheduler),
            stop=Mock(),
        )
        worker = SimpleNamespace(
            run=AsyncMock(side_effect=run_worker),
            stop=Mock(),
        )
        close_redis = AsyncMock()
        dispose_engine = AsyncMock()

        with (
            patch("app.monitoring_main.Scheduler", return_value=scheduler),
            patch(
                "app.monitoring_main.MonitorStreamWorker",
                return_value=worker,
            ),
            patch(
                "app.monitoring_main.check_redis_connection",
                AsyncMock(return_value=True),
            ),
            patch(
                "app.monitoring_main.close_redis_connection",
                close_redis,
            ),
            patch(
                "app.monitoring_main.engine",
                SimpleNamespace(dispose=dispose_engine),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "scheduler failed"):
                await main()

        self.assertTrue(worker_cancelled.is_set())
        scheduler.stop.assert_called_once_with()
        worker.stop.assert_called_once_with()
        close_redis.assert_awaited_once_with()
        dispose_engine.assert_awaited_once_with()

    async def test_cancelling_runtime_stops_both_components(self):
        scheduler_started = asyncio.Event()
        worker_started = asyncio.Event()
        scheduler_cancelled = asyncio.Event()
        worker_cancelled = asyncio.Event()

        async def run_until_cancelled(started, cancelled):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        async def run_scheduler():
            await run_until_cancelled(
                scheduler_started,
                scheduler_cancelled,
            )

        async def run_worker():
            await run_until_cancelled(
                worker_started,
                worker_cancelled,
            )

        scheduler = SimpleNamespace(
            run=AsyncMock(side_effect=run_scheduler),
            stop=Mock(),
        )
        worker = SimpleNamespace(
            run=AsyncMock(side_effect=run_worker),
            stop=Mock(),
        )
        close_redis = AsyncMock()
        dispose_engine = AsyncMock()

        with (
            patch("app.monitoring_main.Scheduler", return_value=scheduler),
            patch(
                "app.monitoring_main.MonitorStreamWorker",
                return_value=worker,
            ),
            patch(
                "app.monitoring_main.check_redis_connection",
                AsyncMock(return_value=True),
            ),
            patch(
                "app.monitoring_main.close_redis_connection",
                close_redis,
            ),
            patch(
                "app.monitoring_main.engine",
                SimpleNamespace(dispose=dispose_engine),
            ),
        ):
            runtime_task = asyncio.create_task(main())
            await asyncio.gather(
                scheduler_started.wait(),
                worker_started.wait(),
            )
            runtime_task.cancel()

            with self.assertRaises(asyncio.CancelledError):
                await runtime_task

        self.assertTrue(scheduler_cancelled.is_set())
        self.assertTrue(worker_cancelled.is_set())
        scheduler.stop.assert_called_once_with()
        worker.stop.assert_called_once_with()
        close_redis.assert_awaited_once_with()
        dispose_engine.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
