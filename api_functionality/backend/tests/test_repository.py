import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://test:test@localhost:5432/test",
)

from app.database.models import CheckResultDB, MonitorDB
from app.database.repository import (
    create_monitor,
    get_active_monitors,
    get_check_results,
    save_check_result,
)
from app.models.monitor import CheckResult


class FakeScalarResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return list(self.rows)


class FakeQueryResult:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return FakeScalarResult(self.rows)


class FakeSession:
    def __init__(self, rows=(), commit_error=None):
        self.rows = rows
        self.commit_error = commit_error
        self.added = []
        self.committed = False
        self.rolled_back = False
        self.statement = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        if self.commit_error is not None:
            raise self.commit_error
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def refresh(self, value):
        if value.id is None:
            value.id = 1

    async def execute(self, statement):
        self.statement = statement
        return FakeQueryResult(self.rows)


class RepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_monitor_returns_domain_monitor(self):
        session = FakeSession()

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            monitor = await create_monitor(
                name="Google",
                url="https://google.com",
                interval_seconds=30,
                timeout_seconds=5,
                expected_status_code=200,
            )

        self.assertEqual(monitor.id, 1)
        self.assertEqual(monitor.name, "Google")
        self.assertTrue(session.committed)
        self.assertIsInstance(session.added[0], MonitorDB)

    async def test_create_monitor_rolls_back_commit_failure(self):
        session = FakeSession(commit_error=RuntimeError("commit failed"))

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            with self.assertRaises(RuntimeError):
                await create_monitor(
                    name="Google",
                    url="https://google.com",
                    interval_seconds=30,
                    timeout_seconds=5,
                )

        self.assertTrue(session.rolled_back)

    async def test_get_active_monitors_maps_rows(self):
        row = MonitorDB(
            id=7,
            name="Google",
            url="https://google.com",
            interval_seconds=30,
            timeout_seconds=5,
            expected_status_code=200,
            is_active=True,
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            monitors = await get_active_monitors()

        self.assertEqual(len(monitors), 1)
        self.assertEqual(monitors[0].id, 7)
        self.assertIsNotNone(session.statement)

    async def test_save_and_read_check_results(self):
        checked_at = datetime.now(timezone.utc)
        domain_result = CheckResult(
            status_code=200,
            latency_ms=42.5,
            success=True,
            error=None,
            checked_at=checked_at,
        )
        write_session = FakeSession()

        with patch(
            "app.database.repository.async_session_factory",
            return_value=write_session,
        ):
            await save_check_result(7, domain_result)

        saved = write_session.added[0]
        self.assertIsInstance(saved, CheckResultDB)
        self.assertEqual(saved.monitor_id, 7)
        self.assertTrue(write_session.committed)

        row = CheckResultDB(
            id=9,
            monitor_id=7,
            checked_at=checked_at,
            status_code=200,
            latency_ms=42.5,
            success=True,
            error=None,
        )
        read_session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=read_session,
        ):
            results = await get_check_results(7, limit=10)

        self.assertEqual(results, [domain_result])

    async def test_get_check_results_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            await get_check_results(1, limit=0)


if __name__ == "__main__":
    unittest.main()
