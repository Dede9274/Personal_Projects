import asyncio
import os
import sys
import unittest

from sqlalchemy import select

from app.database.connection import async_session_factory, engine
from app.database.models import CheckResultDB, IncidentDB, MonitorDB
from app.workers.monitor_worker import execute_monitor_job


if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


class LocalHTTPServer:
    def __init__(self) -> None:
        self._server: asyncio.Server | None = None
        self._port: int | None = None

    @property
    def url(self) -> str:
        if self._port is None:
            raise RuntimeError("The local HTTP server has not been started")
        return f"http://127.0.0.1:{self._port}/health"

    async def start(self) -> None:
        if self._server is not None:
            return

        self._server = await asyncio.start_server(
            self._handle_request,
            host="127.0.0.1",
            port=self._port or 0,
            reuse_address=True,
        )

        if self._port is None:
            socket = self._server.sockets[0]
            self._port = socket.getsockname()[1]

    async def stop(self) -> None:
        if self._server is None:
            return

        self._server.close()
        await self._server.wait_closed()
        self._server = None

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            await reader.readuntil(b"\r\n\r\n")
            writer.write(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Length: 2\r\n"
                b"Content-Type: text/plain\r\n"
                b"Connection: close\r\n"
                b"\r\n"
                b"OK"
            )
            await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass


@unittest.skipUnless(
    os.getenv("RUN_DATABASE_TESTS") == "1",
    "set RUN_DATABASE_TESTS=1 to run PostgreSQL integration tests",
)
class IncidentLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_incident_lifecycle_with_local_server(self):
        server = LocalHTTPServer()
        monitor_id: int | None = None

        try:
            await server.start()

            async with async_session_factory() as session:
                monitor_db = MonitorDB(
                    name="Local Incident Lifecycle Monitor",
                    url=server.url,
                    interval_seconds=2,
                    timeout_seconds=1,
                    expected_status_code=200,
                )
                session.add(monitor_db)
                await session.commit()
                await session.refresh(monitor_db)
                monitor_id = monitor_db.id

            async def execute_check() -> None:
                if monitor_id is None:
                    raise RuntimeError("Test monitor was not created")
                await execute_monitor_job(monitor_id)

            async def load_results() -> list[CheckResultDB]:
                statement = (
                    select(CheckResultDB)
                    .where(CheckResultDB.monitor_id == monitor_id)
                    .order_by(
                        CheckResultDB.checked_at,
                        CheckResultDB.id,
                    )
                )
                async with async_session_factory() as session:
                    result = await session.execute(statement)
                    return list(result.scalars().all())

            async def load_incidents() -> list[IncidentDB]:
                statement = (
                    select(IncidentDB)
                    .where(IncidentDB.monitor_id == monitor_id)
                    .order_by(IncidentDB.started_at)
                )
                async with async_session_factory() as session:
                    result = await session.execute(statement)
                    return list(result.scalars().all())

            # UP, UP, UP: results are saved but no incident is opened.
            for _ in range(3):
                await execute_check()

            results = await load_results()
            self.assertEqual(len(results), 3)
            self.assertTrue(all(result.success for result in results))
            self.assertEqual(await load_incidents(), [])

            # DOWN, DOWN: below the threshold, so still no incident.
            await server.stop()
            for _ in range(2):
                await execute_check()

            results = await load_results()
            self.assertEqual(len(results), 5)
            self.assertTrue(all(not result.success for result in results[-2:]))
            self.assertEqual(await load_incidents(), [])

            # The third DOWN opens one incident beginning at failure one.
            await execute_check()

            results = await load_results()
            first_three_failures = results[-3:]
            incidents = await load_incidents()
            self.assertEqual(len(incidents), 1)
            self.assertEqual(incidents[0].status, "OPEN")
            self.assertEqual(incidents[0].failure_count, 3)
            incident_id = incidents[0].id
            self.assertEqual(
                incidents[0].started_at,
                first_three_failures[0].checked_at,
            )
            self.assertEqual(
                incidents[0].last_failure_at,
                first_three_failures[-1].checked_at,
            )
            self.assertIsNone(incidents[0].resolved_at)

            # More DOWN results increment the same incident.
            await execute_check()
            await execute_check()

            results = await load_results()
            incidents = await load_incidents()
            self.assertEqual(len(incidents), 1)
            self.assertEqual(incidents[0].id, incident_id)
            self.assertEqual(incidents[0].failure_count, 5)
            self.assertEqual(
                incidents[0].last_failure_at,
                results[-1].checked_at,
            )

            # The first recovery resolves that same incident.
            await server.start()
            await execute_check()

            results = await load_results()
            incidents = await load_incidents()
            self.assertEqual(len(incidents), 1)
            self.assertEqual(incidents[0].id, incident_id)
            self.assertEqual(incidents[0].status, "RESOLVED")
            self.assertEqual(
                incidents[0].resolved_at,
                results[-1].checked_at,
            )

            # DOWN, DOWN, UP, DOWN, DOWN: each UP resets the streak.
            await server.stop()
            await execute_check()
            await execute_check()
            await server.start()
            await execute_check()
            await server.stop()
            await execute_check()
            await execute_check()

            incidents = await load_incidents()
            self.assertEqual(len(incidents), 1)
            self.assertEqual(incidents[0].id, incident_id)
            self.assertEqual(incidents[0].status, "RESOLVED")

            results = await load_results()
            self.assertEqual(len(results), 14)
            self.assertEqual(
                [result.success for result in results],
                [
                    True,
                    True,
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    True,
                    False,
                    False,
                    True,
                    False,
                    False,
                ],
            )
        finally:
            await server.stop()

            if monitor_id is not None:
                async with async_session_factory() as session:
                    monitor_db = await session.get(MonitorDB, monitor_id)
                    if monitor_db is not None:
                        await session.delete(monitor_db)
                        await session.commit()

    async def asyncTearDown(self):
        await engine.dispose()


if __name__ == "__main__":
    unittest.main()
