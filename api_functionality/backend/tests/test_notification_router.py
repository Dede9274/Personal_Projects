import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.main import app
from app.models.notification import NotificationPreferences
from app.notifications.config import SmtpConfigurationStatus


def make_preferences(
    *,
    email_enabled: bool = True,
) -> NotificationPreferences:
    return NotificationPreferences(
        email_enabled=email_enabled,
        email_recipients=("alerts@example.test",),
        email_timeout_seconds=10,
        webhook_enabled=False,
        webhook_url=None,
        webhook_timeout_seconds=10,
        notify_incident_opened=True,
        updated_at=datetime.now(timezone.utc),
    )


def smtp_status(*, configured: bool) -> SmtpConfigurationStatus:
    return SmtpConfigurationStatus(
        configured=configured,
        host="smtp.example.test" if configured else None,
        port=587 if configured else None,
        security="starttls" if configured else None,
        from_email="uptime@example.test" if configured else None,
        error=None if configured else "Set SMTP_HOST to a real mail server",
    )


class NotificationRouterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_get_returns_preferences_and_safe_smtp_status(self):
        with (
            patch(
                "app.routers.notifications.get_notification_preferences",
                AsyncMock(return_value=make_preferences()),
            ),
            patch(
                "app.routers.notifications.get_smtp_configuration_status",
                return_value=smtp_status(configured=True),
            ),
        ):
            response = await self.client.get("/notification-settings")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["email_enabled"])
        self.assertTrue(response.json()["smtp_configured"])
        self.assertNotIn("smtp_password", response.json())

    async def test_patch_persists_dashboard_preferences(self):
        current = make_preferences(email_enabled=False)
        saved = make_preferences(email_enabled=True)
        update_mock = AsyncMock(return_value=saved)

        with (
            patch(
                "app.routers.notifications.get_notification_preferences",
                AsyncMock(return_value=current),
            ),
            patch(
                "app.routers.notifications.update_notification_preferences",
                update_mock,
            ),
            patch(
                "app.routers.notifications.get_smtp_configuration_status",
                return_value=smtp_status(configured=True),
            ),
        ):
            response = await self.client.patch(
                "/notification-settings",
                json={
                    "email_enabled": True,
                    "email_recipients": ["alerts@example.test"],
                    "email_timeout_seconds": 10,
                    "webhook_enabled": False,
                    "webhook_url": None,
                    "webhook_timeout_seconds": 10,
                    "notify_incident_opened": True,
                },
            )

        self.assertEqual(response.status_code, 200)
        update_mock.assert_awaited_once()
        persisted = update_mock.await_args.args[0]
        self.assertEqual(
            persisted.email_recipients,
            ("alerts@example.test",),
        )

    async def test_patch_rejects_email_without_smtp_transport(self):
        with patch(
            "app.routers.notifications.get_smtp_configuration_status",
            return_value=smtp_status(configured=False),
        ):
            response = await self.client.patch(
                "/notification-settings",
                json={
                    "email_enabled": True,
                    "email_recipients": ["alerts@example.test"],
                    "email_timeout_seconds": 10,
                    "webhook_enabled": False,
                    "webhook_url": None,
                    "webhook_timeout_seconds": 10,
                    "notify_incident_opened": True,
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("SMTP_HOST", response.json()["detail"])

    async def test_test_email_uses_saved_recipients(self):
        send_mock = AsyncMock()

        with (
            patch(
                "app.routers.notifications.get_notification_preferences",
                AsyncMock(return_value=make_preferences()),
            ),
            patch(
                "app.routers.notifications.get_email_settings",
                return_value=object(),
            ),
            patch(
                "app.routers.notifications.send_test_email",
                send_mock,
            ),
        ):
            response = await self.client.post(
                "/notification-settings/test-email"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["recipients"],
            ["alerts@example.test"],
        )
        send_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
