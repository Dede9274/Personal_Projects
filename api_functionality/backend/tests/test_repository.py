import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.database.models import CheckResultDB, IncidentDB, MonitorDB
from app.database.repository import (
    create_incident,
    create_monitor,
    get_active_monitor,
    get_active_monitors,
    get_check_results,
    get_incident,
    get_incidents,
    get_incidents_for_monitor,
    get_open_incidents,
    get_monitor_by_id,
    increment_incident,
    resolve_incident,
    save_check_result,
    transition_incident_status,
    update_incident,
)
from app.models.incident import IncidentStatus, IncidentTransitionError
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

    def scalar_one_or_none(self):
        if not self.rows:
            return None
        if len(self.rows) > 1:
            raise AssertionError("Expected at most one fake row")
        return self.rows[0]


class FakeSession:
    def __init__(self, rows=(), commit_error=None):
        self.rows = rows
        self.commit_error = commit_error
        self.added = []
        self.committed = False
        self.rolled_back = False
        self.statement = None
        self.get_call = None

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

    async def get(self, model, identifier, **kwargs):
        self.get_call = (model, identifier, kwargs)
        return next(
            (
                row
                for row in self.rows
                if isinstance(row, model) and row.id == identifier
            ),
            None,
        )


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

    async def test_get_active_monitor_maps_one_row(self):
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
            monitor = await get_active_monitor(7)

        self.assertIsNotNone(monitor)
        self.assertEqual(monitor.id, 7)
        self.assertEqual(monitor.name, "Google")

    async def test_get_active_monitor_returns_none_when_unavailable(self):
        session = FakeSession(rows=[])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            monitor = await get_active_monitor(99)

        self.assertIsNone(monitor)

    async def test_get_monitor_by_id_includes_inactive_monitor(self):
        row = MonitorDB(
            id=7,
            name="Paused monitor",
            url="https://paused.example.test",
            interval_seconds=30,
            timeout_seconds=5,
            expected_status_code=200,
            is_active=False,
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            monitor = await get_monitor_by_id(7)

        self.assertIsNotNone(monitor)
        self.assertEqual(monitor.id, 7)
        self.assertEqual(monitor.name, "Paused monitor")
        self.assertEqual(session.get_call[0], MonitorDB)
        self.assertEqual(session.get_call[1], 7)

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

    async def test_create_incident_creates_an_open_incident(self):
        started_at = datetime.now(timezone.utc)
        session = FakeSession()

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await create_incident(
                monitor_id=7,
                started_at=started_at,
                last_error="Connection failed",
            )

        self.assertIs(incident, session.added[0])
        self.assertIsInstance(incident, IncidentDB)
        self.assertEqual(incident.id, 1)
        self.assertEqual(incident.monitor_id, 7)
        self.assertEqual(incident.started_at, started_at)
        self.assertEqual(incident.last_failure_at, started_at)
        self.assertIsNone(incident.resolved_at)
        self.assertEqual(incident.status, "OPEN")
        self.assertEqual(incident.failure_count, 1)
        self.assertEqual(incident.last_error, "Connection failed")
        self.assertTrue(session.committed)

    async def test_create_incident_rolls_back_commit_failure(self):
        session = FakeSession(commit_error=RuntimeError("commit failed"))

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            with self.assertRaisesRegex(RuntimeError, "commit failed"):
                await create_incident(
                    monitor_id=7,
                    started_at=datetime.now(timezone.utc),
                    last_error="Connection failed",
                )

        self.assertTrue(session.rolled_back)

    async def test_get_open_incidents_executes_the_statement(self):
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=datetime.now(timezone.utc),
            last_failure_at=datetime.now(timezone.utc),
            resolved_at=None,
            status="OPEN",
            failure_count=1,
            last_error="Connection failed",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incidents = await get_open_incidents()

        self.assertEqual(incidents, [row])
        self.assertIsNotNone(session.statement)
        self.assertIsNot(session.statement, session)

    async def test_get_incidents_returns_all_rows(self):
        rows = [
            IncidentDB(id=2, monitor_id=7),
            IncidentDB(id=1, monitor_id=8),
        ]
        session = FakeSession(rows=rows)

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incidents = await get_incidents()

        self.assertEqual(incidents, rows)
        self.assertIsNotNone(session.statement)

    async def test_get_incident_returns_row_by_primary_key(self):
        row = IncidentDB(id=3, monitor_id=7)
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await get_incident(3)

        self.assertIs(incident, row)
        self.assertEqual(session.get_call, (IncidentDB, 3, {}))

    async def test_get_incidents_for_monitor_returns_matching_rows(self):
        rows = [IncidentDB(id=3, monitor_id=7)]
        session = FakeSession(rows=rows)

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incidents = await get_incidents_for_monitor(7)

        self.assertEqual(incidents, rows)
        self.assertIsNotNone(session.statement)

    async def test_increment_incident_updates_failure_details(self):
        started_at = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)
        failed_at = datetime(2026, 8, 28, 10, 5, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=None,
            status="OPEN",
            failure_count=3,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await increment_incident(
                incident_id=3,
                last_error="Connection refused",
                last_failure_at=failed_at,
            )

        self.assertIs(incident, row)
        self.assertEqual(incident.failure_count, 4)
        self.assertEqual(incident.last_error, "Connection refused")
        self.assertEqual(incident.last_failure_at, failed_at)
        self.assertTrue(session.committed)

    async def test_increment_incident_returns_none_when_not_open(self):
        session = FakeSession(rows=[])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await increment_incident(
                incident_id=3,
                last_error="Connection refused",
            )

        self.assertIsNone(incident)
        self.assertFalse(session.committed)

    async def test_resolve_incident_awaits_and_returns_the_incident(self):
        started_at = datetime(2026, 8, 28, 10, 0, tzinfo=timezone.utc)
        resolved_at = datetime(2026, 8, 28, 10, 10, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=None,
            status="OPEN",
            failure_count=1,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await resolve_incident(7, resolved_at)

        self.assertIs(incident, row)
        self.assertEqual(incident.status, "RESOLVED")
        self.assertEqual(incident.resolved_at, resolved_at)
        self.assertTrue(session.committed)

    async def test_update_incident_changes_only_supplied_fields(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        failed_at = datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=None,
            status="OPEN",
            failure_count=3,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await update_incident(
                incident_id=3,
                changes={
                    "last_error": "Connection refused",
                    "last_failure_at": failed_at,
                },
            )

        self.assertIs(incident, row)
        self.assertEqual(incident.last_error, "Connection refused")
        self.assertEqual(incident.last_failure_at, failed_at)
        self.assertEqual(incident.failure_count, 3)
        self.assertEqual(incident.status, "OPEN")
        self.assertTrue(session.committed)
        self.assertEqual(session.get_call[2], {"with_for_update": True})

    async def test_update_incident_can_resolve_with_both_fields(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        resolved_at = datetime(2026, 9, 1, 10, 10, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=None,
            status="OPEN",
            failure_count=3,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await update_incident(
                incident_id=3,
                changes={
                    "status": "RESOLVED",
                    "resolved_at": resolved_at,
                },
            )

        self.assertIs(incident, row)
        self.assertEqual(incident.status, "RESOLVED")
        self.assertEqual(incident.resolved_at, resolved_at)
        self.assertTrue(session.committed)

    async def test_update_incident_rejects_invalid_field(self):
        with self.assertRaisesRegex(ValueError, "monitor_id"):
            await update_incident(
                incident_id=3,
                changes={"monitor_id": 99},
            )

    async def test_update_incident_rejects_naive_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            await update_incident(
                incident_id=3,
                changes={
                    "last_failure_at": datetime(2026, 9, 1, 10, 5),
                },
            )

    async def test_update_incident_rejects_inconsistent_state(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=None,
            status="OPEN",
            failure_count=3,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "RESOLVED incident requires resolved_at",
            ):
                await update_incident(
                    incident_id=3,
                    changes={"status": "RESOLVED"},
                )

        self.assertTrue(session.rolled_back)
        self.assertFalse(session.committed)

    async def test_update_incident_does_not_reopen_resolved_history(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        resolved_at = datetime(2026, 9, 1, 10, 10, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=resolved_at,
            status="RESOLVED",
            failure_count=3,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            with self.assertRaisesRegex(ValueError, "cannot be reopened"):
                await update_incident(
                    incident_id=3,
                    changes={
                        "status": "OPEN",
                        "resolved_at": None,
                    },
                )

        self.assertTrue(session.rolled_back)
        self.assertFalse(session.committed)

    async def test_update_incident_returns_none_when_missing(self):
        session = FakeSession(rows=[])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            incident = await update_incident(
                incident_id=999,
                changes={"last_error": "Connection refused"},
            )

        self.assertIsNone(incident)
        self.assertFalse(session.committed)

    async def test_update_incident_rolls_back_commit_failure(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=None,
            status="OPEN",
            failure_count=3,
            last_error="Timeout",
        )
        session = FakeSession(
            rows=[row],
            commit_error=RuntimeError("commit failed"),
        )

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            with self.assertRaisesRegex(RuntimeError, "commit failed"):
                await update_incident(
                    incident_id=3,
                    changes={"last_error": "Connection refused"},
                )

        self.assertTrue(session.rolled_back)

    async def test_transition_open_incident_to_investigating(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at,
            resolved_at=None,
            status="OPEN",
            failure_count=3,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            updated = await transition_incident_status(
                3,
                IncidentStatus.INVESTIGATING,
            )

        self.assertIs(updated, row)
        self.assertEqual(row.status, "INVESTIGATING")
        self.assertIsNone(row.resolved_at)
        self.assertTrue(session.committed)

    async def test_transition_investigating_incident_to_resolved(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        resolved_at = started_at + timedelta(minutes=12)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at + timedelta(minutes=10),
            resolved_at=None,
            status="INVESTIGATING",
            failure_count=5,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            updated = await transition_incident_status(
                3,
                IncidentStatus.RESOLVED,
                transitioned_at=resolved_at,
            )

        self.assertIs(updated, row)
        self.assertEqual(row.status, "RESOLVED")
        self.assertEqual(row.resolved_at, resolved_at)
        self.assertTrue(session.committed)

    async def test_transition_resolved_incident_is_terminal(self):
        started_at = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        resolved_at = started_at + timedelta(minutes=12)
        row = IncidentDB(
            id=3,
            monitor_id=7,
            started_at=started_at,
            last_failure_at=started_at + timedelta(minutes=10),
            resolved_at=resolved_at,
            status="RESOLVED",
            failure_count=5,
            last_error="Timeout",
        )
        session = FakeSession(rows=[row])

        with patch(
            "app.database.repository.async_session_factory",
            return_value=session,
        ):
            with self.assertRaises(IncidentTransitionError):
                await transition_incident_status(
                    3,
                    IncidentStatus.INVESTIGATING,
                )

        self.assertEqual(row.status, "RESOLVED")
        self.assertFalse(session.committed)


if __name__ == "__main__":
    unittest.main()
