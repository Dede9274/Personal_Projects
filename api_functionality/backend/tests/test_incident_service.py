import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, call, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.database.models import IncidentDB
from app.models.monitor import CheckResult
from app.services.incident_service import process_check_result


def check_result(
    *,
    success: bool,
    checked_at: datetime,
    error: str | None = None,
) -> CheckResult:
    return CheckResult(
        status_code=200 if success else None,
        latency_ms=10,
        success=success,
        error=error,
        checked_at=checked_at,
    )


def incident(incident_id: int, failure_count: int = 3) -> IncidentDB:
    started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    return IncidentDB(
        id=incident_id,
        monitor_id=7,
        started_at=started_at,
        last_failure_at=started_at,
        resolved_at=None,
        status="OPEN",
        failure_count=failure_count,
        last_error="Timeout",
    )


class IncidentServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_without_open_incident_does_nothing(self):
        result = check_result(
            success=True,
            checked_at=datetime.now(timezone.utc),
        )

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=None),
            ),
            patch(
                "app.services.incident_service.resolve_incident",
                AsyncMock(),
            ) as resolve_mock,
            patch(
                "app.services.incident_service.get_check_results",
                AsyncMock(),
            ) as history_mock,
        ):
            processed_incident = await process_check_result(7, result)

        self.assertIsNone(processed_incident)
        resolve_mock.assert_not_awaited()
        history_mock.assert_not_awaited()

    async def test_success_resolves_open_incident(self):
        recovered_at = datetime.now(timezone.utc)
        result = check_result(success=True, checked_at=recovered_at)
        open_incident = incident(11)
        resolved_incident = incident(11)
        resolved_incident.status = "RESOLVED"
        resolved_incident.resolved_at = recovered_at

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=open_incident),
            ),
            patch(
                "app.services.incident_service.resolve_incident",
                AsyncMock(return_value=resolved_incident),
            ) as resolve_mock,
        ):
            processed_incident = await process_check_result(7, result)

        self.assertIs(processed_incident, resolved_incident)
        resolve_mock.assert_awaited_once_with(
            monitor_id=7,
            resolved_at=recovered_at,
        )

    async def test_success_resolves_investigating_incident(self):
        recovered_at = datetime.now(timezone.utc)
        result = check_result(success=True, checked_at=recovered_at)
        investigating_incident = incident(12)
        investigating_incident.status = "INVESTIGATING"

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=investigating_incident),
            ),
            patch(
                "app.services.incident_service.resolve_incident",
                AsyncMock(return_value=investigating_incident),
            ) as resolve_mock,
        ):
            processed_incident = await process_check_result(7, result)

        self.assertIs(processed_incident, investigating_incident)
        resolve_mock.assert_awaited_once_with(
            monitor_id=7,
            resolved_at=recovered_at,
        )

    async def test_failure_increments_existing_open_incident(self):
        failed_at = datetime.now(timezone.utc)
        result = check_result(
            success=False,
            checked_at=failed_at,
            error="Connection refused",
        )
        open_incident = incident(11)
        incremented_incident = incident(11, failure_count=4)

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=open_incident),
            ),
            patch(
                "app.services.incident_service.increment_incident",
                AsyncMock(return_value=incremented_incident),
            ) as increment_mock,
            patch(
                "app.services.incident_service.get_check_results",
                AsyncMock(),
            ) as history_mock,
        ):
            processed_incident = await process_check_result(7, result)

        self.assertIs(processed_incident, incremented_incident)
        increment_mock.assert_awaited_once_with(
            incident_id=11,
            last_error="Connection refused",
            last_failure_at=failed_at,
        )
        history_mock.assert_not_awaited()

    async def test_failure_increments_investigating_incident(self):
        failed_at = datetime.now(timezone.utc)
        result = check_result(
            success=False,
            checked_at=failed_at,
            error="Connection refused",
        )
        investigating_incident = incident(12)
        investigating_incident.status = "INVESTIGATING"

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=investigating_incident),
            ),
            patch(
                "app.services.incident_service.increment_incident",
                AsyncMock(return_value=investigating_incident),
            ) as increment_mock,
            patch(
                "app.services.incident_service.get_check_results",
                AsyncMock(),
            ) as history_mock,
        ):
            processed_incident = await process_check_result(7, result)

        self.assertIs(processed_incident, investigating_incident)
        increment_mock.assert_awaited_once_with(
            incident_id=12,
            last_error="Connection refused",
            last_failure_at=failed_at,
        )
        history_mock.assert_not_awaited()

    async def test_two_failures_do_not_open_incident(self):
        first_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        failures = [
            check_result(
                success=False,
                checked_at=first_at + timedelta(seconds=2),
                error="Failure two",
            ),
            check_result(
                success=False,
                checked_at=first_at,
                error="Failure one",
            ),
        ]

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=None),
            ),
            patch(
                "app.services.incident_service.get_check_results",
                AsyncMock(return_value=failures),
            ),
            patch(
                "app.services.incident_service.create_incident",
                AsyncMock(),
            ) as create_mock,
        ):
            processed_incident = await process_check_result(7, failures[0])

        self.assertIsNone(processed_incident)
        create_mock.assert_not_awaited()

    async def test_success_inside_latest_three_resets_failure_streak(self):
        first_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        results = [
            check_result(
                success=False,
                checked_at=first_at + timedelta(seconds=4),
                error="Failure two",
            ),
            check_result(
                success=False,
                checked_at=first_at + timedelta(seconds=2),
                error="Failure one",
            ),
            check_result(success=True, checked_at=first_at),
        ]

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=None),
            ),
            patch(
                "app.services.incident_service.get_check_results",
                AsyncMock(return_value=results),
            ),
            patch(
                "app.services.incident_service.create_incident",
                AsyncMock(),
            ) as create_mock,
        ):
            processed_incident = await process_check_result(7, results[0])

        self.assertIsNone(processed_incident)
        create_mock.assert_not_awaited()

    async def test_third_failure_opens_incident_from_first_failure(self):
        first_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        first = check_result(
            success=False,
            checked_at=first_at,
            error="Timeout",
        )
        second = check_result(
            success=False,
            checked_at=first_at + timedelta(seconds=2),
            error="Connection reset",
        )
        third = check_result(
            success=False,
            checked_at=first_at + timedelta(seconds=4),
            error="Connection refused",
        )
        created_incident = incident(11, failure_count=1)
        count_two = incident(11, failure_count=2)
        count_three = incident(11, failure_count=3)

        with (
            patch(
                "app.services.incident_service.get_active_incident",
                AsyncMock(return_value=None),
            ),
            patch(
                "app.services.incident_service.get_check_results",
                AsyncMock(return_value=[third, second, first]),
            ) as history_mock,
            patch(
                "app.services.incident_service.create_incident",
                AsyncMock(return_value=created_incident),
            ) as create_mock,
            patch(
                "app.services.incident_service.increment_incident",
                AsyncMock(side_effect=[count_two, count_three]),
            ) as increment_mock,
        ):
            processed_incident = await process_check_result(7, third)

        self.assertIs(processed_incident, count_three)
        history_mock.assert_awaited_once_with(monitor_id=7, limit=3)
        create_mock.assert_awaited_once_with(
            monitor_id=7,
            started_at=first.checked_at,
            last_error="Timeout",
        )
        self.assertEqual(
            increment_mock.await_args_list,
            [
                call(
                    incident_id=11,
                    last_error="Connection reset",
                    last_failure_at=second.checked_at,
                ),
                call(
                    incident_id=11,
                    last_error="Connection refused",
                    last_failure_at=third.checked_at,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
