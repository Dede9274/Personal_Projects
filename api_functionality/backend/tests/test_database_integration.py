import asyncio
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database.connection import async_session_factory, engine
from app.database.models import (
    CheckResultDB,
    IncidentDB,
    MonitorDB,
    NotificationSettingsDB,
)
from app.database.repository import create_incident, increment_incident
from app.services.monitor_service import list_monitor_checks


if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


@unittest.skipUnless(
    os.getenv("RUN_DATABASE_TESTS") == "1",
    "set RUN_DATABASE_TESTS=1 to run PostgreSQL integration tests",
)
class DatabaseIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_monitor_and_result_round_trip_rolls_back(self):
        async with async_session_factory() as session:
            monitor = MonitorDB(
                name="Integration Test Monitor",
                url="https://example.test",
                interval_seconds=30,
                timeout_seconds=5,
                expected_status_code=200,
            )
            session.add(monitor)
            await session.flush()

            check_result = CheckResultDB(
                monitor_id=monitor.id,
                checked_at=datetime.now(timezone.utc),
                status_code=200,
                latency_ms=25.5,
                success=True,
                error=None,
            )
            session.add(check_result)
            await session.flush()

            statement = select(CheckResultDB).where(
                CheckResultDB.id == check_result.id
            )
            stored_result = await session.scalar(statement)

            self.assertIsNotNone(stored_result)
            self.assertEqual(stored_result.monitor_id, monitor.id)
            self.assertEqual(stored_result.status_code, 200)
            self.assertFalse(stored_result.security_rejected)

            await session.rollback()

    async def test_notification_settings_singleton_is_persisted(self):
        async with async_session_factory() as session:
            settings = await session.get(NotificationSettingsDB, 1)

            self.assertIsNotNone(settings)
            settings.email_recipients = ["ci-alerts@example.test"]
            settings.email_enabled = True
            await session.flush()

            stored_settings = await session.get(NotificationSettingsDB, 1)
            self.assertTrue(stored_settings.email_enabled)
            self.assertEqual(
                stored_settings.email_recipients,
                ["ci-alerts@example.test"],
            )

            await session.rollback()

    async def test_monitor_check_history_is_filtered_limited_and_newest_first(self):
        async with async_session_factory() as session:
            monitor = MonitorDB(
                name="Check History Integration Test",
                url="https://history.example.test",
                interval_seconds=30,
                timeout_seconds=5,
                expected_status_code=200,
            )
            other_monitor = MonitorDB(
                name="Other Check History Monitor",
                url="https://other-history.example.test",
                interval_seconds=30,
                timeout_seconds=5,
                expected_status_code=200,
            )
            session.add_all([monitor, other_monitor])
            await session.flush()

            checked_at = datetime.now(timezone.utc)
            older_result = CheckResultDB(
                monitor_id=monitor.id,
                checked_at=checked_at - timedelta(seconds=30),
                status_code=503,
                latency_ms=40,
                success=False,
                error="Expected status 200, got 503",
            )
            newest_result = CheckResultDB(
                monitor_id=monitor.id,
                checked_at=checked_at,
                status_code=200,
                latency_ms=20,
                success=True,
                error=None,
            )
            unrelated_result = CheckResultDB(
                monitor_id=other_monitor.id,
                checked_at=checked_at + timedelta(seconds=30),
                status_code=200,
                latency_ms=10,
                success=True,
                error=None,
            )
            session.add_all([
                older_result,
                newest_result,
                unrelated_result,
            ])
            await session.flush()

            results = await list_monitor_checks(
                session,
                monitor.id,
                limit=1,
            )

            self.assertIsNotNone(results)
            result_ids = [result.id for result in results]
            self.assertEqual(result_ids, [newest_result.id])
            self.assertNotIn(unrelated_result.id, result_ids)

            await session.rollback()

    async def test_incident_increment_is_persisted(self):
        monitor_id: int | None = None

        try:
            async with async_session_factory() as session:
                monitor = MonitorDB(
                    name="Incident Integration Test Monitor",
                    url="https://incident.example.test",
                    interval_seconds=30,
                    timeout_seconds=5,
                    expected_status_code=200,
                )
                session.add(monitor)
                await session.commit()
                await session.refresh(monitor)
                monitor_id = monitor.id

            started_at = datetime.now(timezone.utc)
            incident = await create_incident(
                monitor_id=monitor_id,
                started_at=started_at,
                last_error="Timeout",
            )
            await increment_incident(
                incident.id,
                "Timeout",
                last_failure_at=started_at + timedelta(seconds=1),
            )
            await increment_incident(
                incident.id,
                "Timeout",
                last_failure_at=started_at + timedelta(seconds=2),
            )
            last_failure_at = started_at + timedelta(seconds=3)
            updated_incident = await increment_incident(
                incident.id,
                "Connection refused",
                last_failure_at=last_failure_at,
            )

            self.assertIsNotNone(updated_incident)
            self.assertEqual(updated_incident.failure_count, 4)
            self.assertEqual(updated_incident.last_error, "Connection refused")
            self.assertEqual(
                updated_incident.last_failure_at,
                last_failure_at,
            )

            async with async_session_factory() as session:
                stored_incident = await session.get(IncidentDB, incident.id)

            self.assertIsNotNone(stored_incident)
            self.assertEqual(stored_incident.failure_count, 4)
            self.assertEqual(stored_incident.last_error, "Connection refused")
            self.assertEqual(stored_incident.last_failure_at, last_failure_at)
        finally:
            if monitor_id is not None:
                async with async_session_factory() as session:
                    monitor = await session.get(MonitorDB, monitor_id)
                    if monitor is not None:
                        await session.delete(monitor)
                        await session.commit()

    async def asyncTearDown(self):
        await engine.dispose()


if __name__ == "__main__":
    unittest.main()
