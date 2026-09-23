import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.models import MonitorDB
from app.schemas.monitor import MonitorCreate, MonitorUpdate
from app.security.url_validator import MonitorUrlRejectedError
from app.services.monitor_service import create_monitor, update_monitor


class MonitorServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_validates_target_before_persisting(self):
        session = MagicMock()
        data = MonitorCreate(
            name="Public API",
            url="https://example.com/health",
            interval_seconds=30,
            timeout_seconds=5,
        )

        with (
            patch(
                "app.services.monitor_service.validate_monitor_url",
                AsyncMock(),
            ) as validate_mock,
            patch(
                "app.services.monitor_service._save_monitor",
                AsyncMock(),
            ),
        ):
            monitor = await create_monitor(session, data)

        validate_mock.assert_awaited_once_with(
            "https://example.com/health"
        )
        session.add.assert_called_once_with(monitor)

    async def test_create_does_not_persist_a_rejected_target(self):
        session = MagicMock()
        data = MonitorCreate(
            name="Private target",
            url="http://127.0.0.1:6379",
            interval_seconds=30,
            timeout_seconds=5,
        )

        with patch(
            "app.services.monitor_service.validate_monitor_url",
            AsyncMock(
                side_effect=MonitorUrlRejectedError(
                    "The target is not public."
                )
            ),
        ):
            with self.assertRaises(MonitorUrlRejectedError):
                await create_monitor(session, data)

        session.add.assert_not_called()

    async def test_update_validates_a_changed_url_before_saving(self):
        session = MagicMock()
        monitor = MonitorDB(
            id=7,
            name="Public API",
            url="https://example.com/health",
            purpose="",
            interval_seconds=30,
            timeout_seconds=5,
            expected_status_code=200,
            is_active=True,
        )
        data = MonitorUpdate(url="https://example.org/health")

        with (
            patch(
                "app.services.monitor_service.get_monitor",
                AsyncMock(return_value=monitor),
            ),
            patch(
                "app.services.monitor_service.validate_monitor_url",
                AsyncMock(),
            ) as validate_mock,
            patch(
                "app.services.monitor_service._save_monitor",
                AsyncMock(),
            ) as save_mock,
        ):
            updated = await update_monitor(session, 7, data)

        self.assertIs(updated, monitor)
        self.assertEqual(monitor.url, "https://example.org/health")
        validate_mock.assert_awaited_once_with(
            "https://example.org/health"
        )
        save_mock.assert_awaited_once_with(session, monitor)


if __name__ == "__main__":
    unittest.main()
