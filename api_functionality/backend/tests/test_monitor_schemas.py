import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.database.models import MonitorDB
from app.schemas.monitor import (
    MonitorCreate,
    MonitorRead,
    MonitorUpdate,
)


class MonitorSchemaTests(unittest.TestCase):
    def test_create_validates_and_applies_defaults(self):
        monitor = MonitorCreate(
            name="  Google  ",
            url="https://google.com",
            interval_seconds=30,
            timeout_seconds=5,
        )

        self.assertEqual(monitor.name, "Google")
        self.assertEqual(monitor.expected_status_code, 200)
        self.assertTrue(monitor.is_active)

    def test_create_rejects_invalid_values(self):
        invalid_values = (
            {"name": "   "},
            {"url": "not-a-url"},
            {"interval_seconds": 0},
            {"timeout_seconds": -1},
            {"expected_status_code": 99},
            {"expected_status_code": 600},
        )
        valid_data = {
            "name": "Google",
            "url": "https://google.com",
            "interval_seconds": 30,
            "timeout_seconds": 5,
        }

        for invalid_change in invalid_values:
            with self.subTest(invalid_change=invalid_change):
                with self.assertRaises(ValidationError):
                    MonitorCreate(**(valid_data | invalid_change))

    def test_create_rejects_unknown_fields(self):
        with self.assertRaises(ValidationError):
            MonitorCreate(
                name="Google",
                url="https://google.com",
                interval_seconds=30,
                timeout_seconds=5,
                unknown_setting=True,
            )

    def test_update_accepts_only_the_supplied_fields(self):
        update = MonitorUpdate(interval_seconds=60)

        self.assertEqual(
            update.model_dump(exclude_unset=True),
            {"interval_seconds": 60},
        )

    def test_update_rejects_an_empty_body(self):
        with self.assertRaisesRegex(
            ValidationError,
            "At least one field must be provided",
        ):
            MonitorUpdate()

    def test_update_rejects_explicit_null(self):
        with self.assertRaisesRegex(
            ValidationError,
            "Fields cannot be null: name",
        ):
            MonitorUpdate(name=None)

    def test_read_schema_accepts_an_orm_object(self):
        now = datetime.now(timezone.utc)
        monitor_db = MonitorDB(
            id=7,
            name="Google",
            url="https://google.com",
            interval_seconds=30,
            timeout_seconds=5,
            expected_status_code=200,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        response = MonitorRead.model_validate(monitor_db)

        self.assertEqual(response.id, 7)
        self.assertEqual(response.name, "Google")
        self.assertEqual(str(response.url), "https://google.com/")
        self.assertEqual(response.created_at, now)


if __name__ == "__main__":
    unittest.main()
