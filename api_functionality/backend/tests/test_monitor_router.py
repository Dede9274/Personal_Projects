import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI
from redis.exceptions import ConnectionError as RedisConnectionError

from app.database.connection import get_session
from app.database.models import CheckResultDB, MonitorDB
from app.routers.monitors import router
from app.security.url_validator import MonitorUrlRejectedError


def make_monitor(monitor_id: int = 1) -> MonitorDB:
    now = datetime.now(timezone.utc)
    return MonitorDB(
        id=monitor_id,
        name="Google",
        url="https://google.com",
        purpose="Search engine availability",
        interval_seconds=30,
        timeout_seconds=5,
        expected_status_code=200,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_check_result(
    result_id: int = 10,
    monitor_id: int = 1,
) -> CheckResultDB:
    return CheckResultDB(
        id=result_id,
        monitor_id=monitor_id,
        checked_at=datetime.now(timezone.utc),
        status_code=200,
        latency_ms=25.5,
        success=True,
        error=None,
        security_rejected=False,
    )


class MonitorRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = object()
        self.app = FastAPI()
        self.app.include_router(router)

        async def override_session():
            yield self.session

        self.app.dependency_overrides[get_session] = override_session
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.app.dependency_overrides.clear()

    async def test_create_monitor_returns_201(self):
        monitor = make_monitor()

        with patch(
            "app.routers.monitors.monitor_service.create_monitor",
            AsyncMock(return_value=monitor),
        ) as create_mock:
            response = await self.client.post(
                "/monitors",
                json={
                    "name": "Google",
                    "url": "https://google.com",
                    "interval_seconds": 30,
                    "timeout_seconds": 5,
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], 1)
        create_mock.assert_awaited_once()

    async def test_create_monitor_reports_a_rejected_target(self):
        with patch(
            "app.routers.monitors.monitor_service.create_monitor",
            AsyncMock(
                side_effect=MonitorUrlRejectedError(
                    "The target resolves to a non-public address."
                )
            ),
        ):
            response = await self.client.post(
                "/monitors",
                json={
                    "name": "Private service",
                    "url": "https://example.com",
                    "interval_seconds": 30,
                    "timeout_seconds": 5,
                },
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn("Monitor URL rejected", response.json()["detail"])

    async def test_list_monitors_returns_a_list(self):
        with patch(
            "app.routers.monitors.monitor_service.list_monitors",
            AsyncMock(return_value=[make_monitor()]),
        ):
            response = await self.client.get("/monitors")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    async def test_get_monitor_returns_404_when_missing(self):
        with patch(
            "app.routers.monitors.monitor_service.get_monitor",
            AsyncMock(return_value=None),
        ):
            response = await self.client.get("/monitors/99")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Monitor 99 was not found"},
        )

    async def test_list_monitor_checks_returns_empty_history(self):
        with patch(
            "app.routers.monitors.monitor_service.list_monitor_checks",
            AsyncMock(return_value=[]),
        ) as list_mock:
            response = await self.client.get("/monitors/1/checks")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        list_mock.assert_awaited_once_with(self.session, 1, 500)

    async def test_list_monitor_checks_serializes_results(self):
        check_result = make_check_result()

        with patch(
            "app.routers.monitors.monitor_service.list_monitor_checks",
            AsyncMock(return_value=[check_result]),
        ) as list_mock:
            response = await self.client.get("/monitors/1/checks?limit=25")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()[0],
            {
                "id": 10,
                "monitor_id": 1,
                "checked_at": check_result.checked_at.isoformat().replace(
                    "+00:00",
                    "Z",
                ),
                "status_code": 200,
                "latency_ms": 25.5,
                "success": True,
                "error": None,
                "security_rejected": False,
            },
        )
        list_mock.assert_awaited_once_with(self.session, 1, 25)

    async def test_list_monitor_checks_returns_404_when_monitor_is_missing(self):
        with patch(
            "app.routers.monitors.monitor_service.list_monitor_checks",
            AsyncMock(return_value=None),
        ):
            response = await self.client.get("/monitors/99/checks")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Monitor 99 was not found"},
        )

    async def test_list_monitor_checks_rejects_an_invalid_limit(self):
        with patch(
            "app.routers.monitors.monitor_service.list_monitor_checks",
            AsyncMock(),
        ) as list_mock:
            response = await self.client.get("/monitors/1/checks?limit=501")

        self.assertEqual(response.status_code, 422)
        list_mock.assert_not_awaited()

    async def test_run_monitor_check_queues_an_extra_check(self):
        with (
            patch(
                "app.routers.monitors.monitor_service.get_monitor",
                AsyncMock(return_value=make_monitor()),
            ) as get_mock,
            patch(
                "app.routers.monitors.enqueue_monitor_check",
                AsyncMock(return_value="123-0"),
            ) as enqueue_mock,
        ):
            response = await self.client.post("/monitors/1/checks")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {
                "monitor_id": 1,
                "status": "queued",
                "job_id": "123-0",
            },
        )
        get_mock.assert_awaited_once_with(self.session, 1)
        enqueue_mock.assert_awaited_once_with(1)

    async def test_run_monitor_check_reports_an_outstanding_check(self):
        with (
            patch(
                "app.routers.monitors.monitor_service.get_monitor",
                AsyncMock(return_value=make_monitor()),
            ),
            patch(
                "app.routers.monitors.enqueue_monitor_check",
                AsyncMock(return_value=None),
            ) as enqueue_mock,
        ):
            response = await self.client.post("/monitors/1/checks")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "monitor_id": 1,
                "status": "already_outstanding",
                "job_id": None,
            },
        )
        enqueue_mock.assert_awaited_once_with(1)

    async def test_run_monitor_check_returns_404_when_monitor_is_missing(self):
        with (
            patch(
                "app.routers.monitors.monitor_service.get_monitor",
                AsyncMock(return_value=None),
            ),
            patch(
                "app.routers.monitors.enqueue_monitor_check",
                AsyncMock(),
            ) as enqueue_mock,
        ):
            response = await self.client.post("/monitors/99/checks")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Monitor 99 was not found"},
        )
        enqueue_mock.assert_not_awaited()

    async def test_run_monitor_check_rejects_an_inactive_monitor(self):
        monitor = make_monitor()
        monitor.is_active = False

        with (
            patch(
                "app.routers.monitors.monitor_service.get_monitor",
                AsyncMock(return_value=monitor),
            ),
            patch(
                "app.routers.monitors.enqueue_monitor_check",
                AsyncMock(),
            ) as enqueue_mock,
        ):
            response = await self.client.post("/monitors/1/checks")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {"detail": "Monitor 1 is inactive"},
        )
        enqueue_mock.assert_not_awaited()

    async def test_run_monitor_check_returns_503_when_queue_is_unavailable(self):
        with (
            patch(
                "app.routers.monitors.monitor_service.get_monitor",
                AsyncMock(return_value=make_monitor()),
            ),
            patch(
                "app.routers.monitors.enqueue_monitor_check",
                AsyncMock(side_effect=RedisConnectionError("offline")),
            ),
        ):
            response = await self.client.post("/monitors/1/checks")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "The monitor-check queue is unavailable"},
        )

    async def test_update_monitor_returns_updated_monitor(self):
        monitor = make_monitor()
        monitor.interval_seconds = 60

        with patch(
            "app.routers.monitors.monitor_service.update_monitor",
            AsyncMock(return_value=monitor),
        ) as update_mock:
            response = await self.client.patch(
                "/monitors/1",
                json={"interval_seconds": 60},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["interval_seconds"], 60)
        update_mock.assert_awaited_once()

    async def test_update_monitor_returns_404_when_missing(self):
        with patch(
            "app.routers.monitors.monitor_service.update_monitor",
            AsyncMock(return_value=None),
        ):
            response = await self.client.patch(
                "/monitors/99",
                json={"is_active": False},
            )

        self.assertEqual(response.status_code, 404)

    async def test_update_monitor_reports_a_rejected_target(self):
        with patch(
            "app.routers.monitors.monitor_service.update_monitor",
            AsyncMock(
                side_effect=MonitorUrlRejectedError(
                    "The target resolves to a non-public address."
                )
            ),
        ):
            response = await self.client.patch(
                "/monitors/1",
                json={"url": "https://example.com"},
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn("Monitor URL rejected", response.json()["detail"])

    async def test_delete_monitor_returns_204_without_a_body(self):
        with patch(
            "app.routers.monitors.monitor_service.delete_monitor",
            AsyncMock(return_value=True),
        ) as delete_mock:
            response = await self.client.delete("/monitors/1")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        delete_mock.assert_awaited_once_with(self.session, 1)

    async def test_delete_monitor_returns_404_when_missing(self):
        with patch(
            "app.routers.monitors.monitor_service.delete_monitor",
            AsyncMock(return_value=False),
        ):
            response = await self.client.delete("/monitors/99")

        self.assertEqual(response.status_code, 404)

    async def test_nonpositive_monitor_id_is_rejected(self):
        with patch(
            "app.routers.monitors.monitor_service.get_monitor",
            AsyncMock(),
        ) as get_mock:
            response = await self.client.get("/monitors/0")

        self.assertEqual(response.status_code, 422)
        get_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
