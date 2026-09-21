import os
import unittest
from unittest.mock import patch

from app.notifications.config import (
    get_email_settings,
    get_smtp_configuration_status,
    get_webhook_settings,
)


class NotificationConfigTests(unittest.TestCase):
    def test_smtp_status_rejects_placeholder_configuration(self):
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_FROM_EMAIL": "uptime@example.com",
            },
            clear=True,
        ):
            status = get_smtp_configuration_status()

        self.assertFalse(status.configured)
        self.assertIn("SMTP_HOST", status.error)

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
            clear=True,
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
            clear=True,
        ):
            settings = get_webhook_settings()

        self.assertEqual(settings.bearer_token, "token")
        self.assertEqual(settings.signing_secret, "secret")
        self.assertEqual(settings.timeout_seconds, 8)


if __name__ == "__main__":
    unittest.main()
