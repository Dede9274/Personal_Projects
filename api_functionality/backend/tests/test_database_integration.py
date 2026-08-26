import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.connection import async_session_factory, engine
from app.database.models import CheckResultDB, MonitorDB


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

            await session.rollback()

    async def asyncTearDown(self):
        await engine.dispose()


if __name__ == "__main__":
    unittest.main()
