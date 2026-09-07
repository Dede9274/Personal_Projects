import os
import unittest
from unittest.mock import patch

from app.models.notification import NotificationChannel
from app.notifications.config import (
    get_email_settings,
    get_enabled_notification_channels,
    get_webhook_settings,
)


class NotificationConfigTests(unittest.TestCase):
    def test_enabled_channels_are_explicit(self):
        with patch.dict(
            os.environ,
            {
                "EMAIL_NOTIFICATIONS_ENABLED": "true",
                "WEBHOOK_NOTIFICATIONS_ENABLED": "1",
            },
        ):
            self.assertEqual(
                get_enabled_notification_channels(),
                [
                    NotificationChannel.EMAIL,
                    NotificationChannel.WEBHOOK,
                ],
            )

    def test_email_settings_parse_recipients_and_security(self):
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.test",
                "SMTP_PORT": "465",
                "SMTP_SECURITY": "ssl",
                "SMTP_USERNAME": "user",
                "SMTP_PASSWORD": "password",
                "SMTP_FROM_EMAIL": "uptime@example.test",
                "ALERT_EMAIL_TO": (
                    "first@example.test, second@example.test"
                ),
                "SMTP_TIMEOUT_SECONDS": "12",
            },
        ):
            settings = get_email_settings()

        self.assertEqual(settings.port, 465)
        self.assertEqual(settings.security, "ssl")
        self.assertEqual(
            settings.recipients,
            ("first@example.test", "second@example.test"),
        )

    def test_webhook_settings_support_optional_security(self):
        with patch.dict(
            os.environ,
            {
                "ALERT_WEBHOOK_URL": "https://hooks.example.test/uptime",
                "WEBHOOK_BEARER_TOKEN": "token",
                "WEBHOOK_SIGNING_SECRET": "secret",
                "WEBHOOK_TIMEOUT_SECONDS": "8",
            },
        ):
            settings = get_webhook_settings()

        self.assertEqual(settings.bearer_token, "token")
        self.assertEqual(settings.signing_secret, "secret")
        self.assertEqual(settings.timeout_seconds, 8)


if __name__ == "__main__":
    unittest.main()
