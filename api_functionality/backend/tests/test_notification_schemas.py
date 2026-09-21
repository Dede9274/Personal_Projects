import unittest

from pydantic import ValidationError

from app.schemas.notification import NotificationPreferencesUpdate


def valid_preferences() -> dict[str, object]:
    return {
        "email_enabled": True,
        "email_recipients": [" alerts@example.test ", "alerts@example.test"],
        "email_timeout_seconds": 10,
        "webhook_enabled": False,
        "webhook_url": None,
        "webhook_timeout_seconds": 10,
        "notify_incident_opened": True,
    }


class NotificationSchemaTests(unittest.TestCase):
    def test_recipients_are_trimmed_and_deduplicated(self):
        settings = NotificationPreferencesUpdate.model_validate(
            valid_preferences()
        )

        self.assertEqual(
            settings.email_recipients,
            ["alerts@example.test"],
        )

    def test_enabled_email_requires_a_recipient(self):
        values = valid_preferences()
        values["email_recipients"] = []

        with self.assertRaisesRegex(ValidationError, "recipient"):
            NotificationPreferencesUpdate.model_validate(values)

    def test_invalid_email_is_rejected(self):
        values = valid_preferences()
        values["email_recipients"] = ["not-an-email"]

        with self.assertRaisesRegex(ValidationError, "Invalid email"):
            NotificationPreferencesUpdate.model_validate(values)

    def test_enabled_webhook_requires_a_url(self):
        values = valid_preferences()
        values["webhook_enabled"] = True

        with self.assertRaisesRegex(ValidationError, "webhook URL"):
            NotificationPreferencesUpdate.model_validate(values)


if __name__ == "__main__":
    unittest.main()
