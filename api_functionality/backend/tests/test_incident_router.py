import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

import httpx
from fastapi import FastAPI

from app.database.models import IncidentDB
from app.models.incident import IncidentStatus, IncidentTransitionError
from app.routers.incidents import router


def make_incident(
    incident_id: int = 1,
    *,
    monitor_id: int = 7,
    status: str = "OPEN",
) -> IncidentDB:
    now = datetime.now(timezone.utc)
    return IncidentDB(
        id=incident_id,
        monitor_id=monitor_id,
        status=status,
        started_at=now,
        last_failure_at=now,
        resolved_at=now if status == "RESOLVED" else None,
        failure_count=3,
        last_error="Connection refused",
        created_at=now,
    )


class IncidentRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=self.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_list_incidents_returns_json_list(self):
        incidents = [
            make_incident(2),
            make_incident(1, status="RESOLVED"),
        ]

        with patch(
            "app.routers.incidents.repository.get_incidents",
            AsyncMock(return_value=incidents),
        ) as get_mock:
            response = await self.client.get("/incidents")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [2, 1])
        self.assertEqual(response.json()[0]["status"], "OPEN")
        get_mock.assert_awaited_once_with()

    async def test_list_open_incidents_uses_static_open_route(self):
        with patch(
            "app.routers.incidents.repository.get_open_incidents",
            AsyncMock(return_value=[make_incident()]),
        ) as get_mock:
            response = await self.client.get("/incidents/open")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["status"], "OPEN")
        get_mock.assert_awaited_once_with()

    async def test_get_incident_returns_json_object(self):
        with patch(
            "app.routers.incidents.repository.get_incident",
            AsyncMock(return_value=make_incident(4)),
        ) as get_mock:
            response = await self.client.get("/incidents/4")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 4)
        get_mock.assert_awaited_once_with(4)

    async def test_get_incident_returns_404_when_missing(self):
        with patch(
            "app.routers.incidents.repository.get_incident",
            AsyncMock(return_value=None),
        ):
            response = await self.client.get("/incidents/99")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Incident 99 was not found"},
        )

    async def test_patch_incident_marks_it_investigating(self):
        investigating = make_incident(4, status="INVESTIGATING")

        with patch(
            "app.routers.incidents.repository.transition_incident_status",
            AsyncMock(return_value=investigating),
        ) as transition_mock:
            response = await self.client.patch(
                "/incidents/4",
                json={"status": "INVESTIGATING"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "INVESTIGATING")
        transition_mock.assert_awaited_once_with(
            4,
            IncidentStatus.INVESTIGATING,
        )

    async def test_patch_incident_returns_404_when_missing(self):
        with patch(
            "app.routers.incidents.repository.transition_incident_status",
            AsyncMock(return_value=None),
        ):
            response = await self.client.patch(
                "/incidents/99",
                json={"status": "RESOLVED"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "Incident 99 was not found"},
        )

    async def test_patch_incident_rejects_terminal_transition(self):
        with patch(
            "app.routers.incidents.repository.transition_incident_status",
            AsyncMock(
                side_effect=IncidentTransitionError(
                    "A resolved incident cannot be reopened"
                )
            ),
        ):
            response = await self.client.patch(
                "/incidents/4",
                json={"status": "OPEN"},
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {"detail": "A resolved incident cannot be reopened"},
        )

    async def test_patch_incident_rejects_unknown_status(self):
        with patch(
            "app.routers.incidents.repository.transition_incident_status",
            AsyncMock(),
        ) as transition_mock:
            response = await self.client.patch(
                "/incidents/4",
                json={"status": "ACKNOWLEDGED"},
            )

        self.assertEqual(response.status_code, 422)
        transition_mock.assert_not_awaited()

    async def test_list_monitor_incidents_returns_json_list(self):
        with patch(
            "app.routers.incidents.repository.get_incidents_for_monitor",
            AsyncMock(return_value=[make_incident(monitor_id=12)]),
        ) as get_mock:
            response = await self.client.get("/monitors/12/incidents")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["monitor_id"], 12)
        get_mock.assert_awaited_once_with(12)

    async def test_nonpositive_ids_are_rejected(self):
        with patch(
            "app.routers.incidents.repository.get_incident",
            AsyncMock(),
        ) as get_incident_mock, patch(
            "app.routers.incidents.repository.get_incidents_for_monitor",
            AsyncMock(),
        ) as get_monitor_incidents_mock:
            incident_response = await self.client.get("/incidents/0")
            monitor_response = await self.client.get(
                "/monitors/0/incidents"
            )

        self.assertEqual(incident_response.status_code, 422)
        self.assertEqual(monitor_response.status_code, 422)
        get_incident_mock.assert_not_awaited()
        get_monitor_incidents_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
