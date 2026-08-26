import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI

from app.database.connection import get_session
from app.database.models import MonitorDB
from app.routers.monitors import router


def make_monitor(monitor_id: int = 1) -> MonitorDB:
    now = datetime.now(timezone.utc)
    return MonitorDB(
        id=monitor_id,
        name="Google",
        url="https://google.com",
        interval_seconds=30,
        timeout_seconds=5,
        expected_status_code=200,
        is_active=True,
        created_at=now,
        updated_at=now,
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
