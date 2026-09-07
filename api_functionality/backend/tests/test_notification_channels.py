import hashlib
import hmac
import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.database.models import IncidentDB
from app.models.monitor import Monitor
from app.notifications.config import EmailSettings, WebhookSettings
from app.notifications.email import (
    build_incident_email,
    send_incident_opened_email,
)
from app.notifications.webhook import send_incident_opened_webhook


def make_monitor() -> Monitor:
    return Monitor(
        id=7,
        name="Production API",
        url="https://api.example.test",
        interval_seconds=30,
        timeout_seconds=5,
    )


def make_incident() -> IncidentDB:
    started_at = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)
    return IncidentDB(
        id=42,
        monitor_id=7,
        status="OPEN",
        started_at=started_at,
        last_failure_at=started_at,
        resolved_at=None,
        failure_count=3,
        last_error="Connection timed out",
    )


class NotificationChannelTests(unittest.IsolatedAsyncioTestCase):
    def test_build_email_contains_incident_details(self):
        settings = EmailSettings(
            host="smtp.example.test",
            port=587,
            username=None,
            password=None,
            from_email="uptime@example.test",
            recipients=("owner@example.test",),
            security="starttls",
            timeout_seconds=10,
        )

        message = build_incident_email(
            incident=make_incident(),
            monitor=make_monitor(),
            settings=settings,
        )

        self.assertEqual(message["Subject"], "[DOWN] Production API")
        self.assertIn("Incident ID: 42", message.get_content())
        self.assertIn("Connection timed out", message.get_content())

    async def test_async_email_uses_a_thread_for_blocking_smtp(self):
        settings = EmailSettings(
            host="smtp.example.test",
            port=587,
            username=None,
            password=None,
            from_email="uptime@example.test",
            recipients=("owner@example.test",),
            security="none",
            timeout_seconds=10,
        )

        with patch(
            "app.notifications.email.asyncio.to_thread",
            AsyncMock(),
        ) as to_thread_mock:
            await send_incident_opened_email(
                incident=make_incident(),
                monitor=make_monitor(),
                settings=settings,
            )

        to_thread_mock.assert_awaited_once()

    async def test_webhook_sends_signed_json(self):
        settings = WebhookSettings(
            url="https://hooks.example.test/uptime",
            bearer_token="token",
            signing_secret="secret",
            timeout_seconds=10,
        )
        response = AsyncMock()
        response.raise_for_status = lambda: None
        client = AsyncMock()
        client.post.return_value = response
        client_context = AsyncMock()
        client_context.__aenter__.return_value = client

        with patch(
            "app.notifications.webhook.httpx.AsyncClient",
            return_value=client_context,
        ):
            await send_incident_opened_webhook(
                incident=make_incident(),
                monitor=make_monitor(),
                settings=settings,
            )

        arguments = client.post.await_args
        body = arguments.kwargs["content"]
        headers = arguments.kwargs["headers"]
        payload = json.loads(body)

        self.assertEqual(payload["event"], "incident.opened")
        self.assertEqual(payload["incident"]["id"], 42)
        self.assertEqual(headers["Authorization"], "Bearer token")
        expected_digest = hmac.new(
            b"secret",
            body,
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(
            headers["X-Uptime-Signature"],
            f"sha256={expected_digest}",
        )


if __name__ == "__main__":
    unittest.main()
