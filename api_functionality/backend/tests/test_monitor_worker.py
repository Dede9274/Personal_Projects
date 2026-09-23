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
from app.database.models import IncidentDB
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
            patch(
                "app.workers.monitor_worker."
                "enqueue_incident_opened_notifications",
                AsyncMock(),
            ) as notification_mock,
        ):
            await execute_monitor_job(7)

        self.assertEqual(events, ["save", "incident"])
        notification_mock.assert_not_awaited()

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

    async def test_security_rejection_is_saved_without_opening_incident(self):
        monitor = Monitor(
            id=7,
            name="Blocked target",
            url="http://127.0.0.1",
            interval_seconds=30,
            timeout_seconds=5,
        )
        check_result = CheckResult(
            status_code=None,
            latency_ms=1,
            success=False,
            error="Monitor URL rejected: The target is not public.",
            checked_at=datetime.now(timezone.utc),
            security_rejected=True,
        )

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
                AsyncMock(),
            ) as save_mock,
            patch(
                "app.workers.monitor_worker.process_check_result",
                AsyncMock(return_value=None),
            ) as incident_mock,
            patch(
                "app.workers.monitor_worker."
                "enqueue_incident_opened_notifications",
                AsyncMock(),
            ) as notification_mock,
        ):
            await execute_monitor_job(7)

        save_mock.assert_awaited_once_with(
            monitor_id=7,
            check_result=check_result,
        )
        incident_mock.assert_awaited_once_with(
            monitor_id=7,
            check_result=check_result,
        )
        notification_mock.assert_not_awaited()

    async def test_open_incident_enqueues_notifications(self):
        monitor = Monitor(
            id=7,
            name="Production API",
            url="https://api.example.test",
            interval_seconds=30,
            timeout_seconds=5,
        )
        failed_at = datetime.now(timezone.utc)
        check_result = CheckResult(
            status_code=None,
            latency_ms=5000,
            success=False,
            error="Connection timed out",
            checked_at=failed_at,
        )
        incident = IncidentDB(
            id=42,
            monitor_id=7,
            status="OPEN",
            started_at=failed_at,
            last_failure_at=failed_at,
            resolved_at=None,
            failure_count=3,
            last_error=check_result.error,
        )

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
                AsyncMock(),
            ),
            patch(
                "app.workers.monitor_worker.process_check_result",
                AsyncMock(return_value=incident),
            ),
            patch(
                "app.workers.monitor_worker."
                "enqueue_incident_opened_notifications",
                AsyncMock(return_value={}),
            ) as notification_mock,
        ):
            await execute_monitor_job(7)

        notification_mock.assert_awaited_once_with(
            incident_id=42,
            monitor_id=7,
        )


if __name__ == "__main__":
    unittest.main()
