import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.models.monitor import CheckResult, Monitor
from app.workers.monitor_worker import execute_monitor_job


class MonitorWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_result_is_saved_before_incident_processing(self):
        monitor = Monitor(
            id=7,
            name="Google",
            url="https://google.com",
            interval_seconds=30,
            timeout_seconds=5,
        )
        check_result = CheckResult(
            status_code=200,
            latency_ms=10,
            success=True,
            error=None,
            checked_at=datetime.now(timezone.utc),
        )
        events: list[str] = []

        async def record_save(**kwargs):
            events.append("save")

        async def record_incident(**kwargs):
            events.append("incident")

        with (
            patch(
                "app.workers.monitor_worker.get_active_monitor",
                AsyncMock(return_value=monitor),
            ),
            patch(
                "app.workers.monitor_worker.check_monitor",
                AsyncMock(return_value=check_result),
            ),
            patch(
                "app.workers.monitor_worker.save_check_result",
                side_effect=record_save,
            ),
            patch(
                "app.workers.monitor_worker.process_check_result",
                side_effect=record_incident,
            ),
        ):
            await execute_monitor_job(7)

        self.assertEqual(events, ["save", "incident"])

    async def test_missing_or_inactive_monitor_is_skipped(self):
        with (
            patch(
                "app.workers.monitor_worker.get_active_monitor",
                AsyncMock(return_value=None),
            ),
            patch(
                "app.workers.monitor_worker.check_monitor",
                AsyncMock(),
            ) as check_mock,
        ):
            await execute_monitor_job(99)

        check_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
