import unittest

from app.database.base import Base
from app.database.models import CheckResultDB, MonitorDB
from app.models.monitor import Monitor


class ModelTests(unittest.TestCase):
    def test_domain_monitor_defaults(self):
        monitor = Monitor(
            name="Google",
            url="https://google.com",
            interval_seconds=30,
            timeout_seconds=5,
        )

        self.assertEqual(monitor.expected_status_code, 200)
        self.assertIsNone(monitor.id)

    def test_orm_tables_are_registered(self):
        self.assertEqual(
            set(Base.metadata.tables),
            {"monitors", "check_results"},
        )
        self.assertEqual(MonitorDB.__tablename__, "monitors")
        self.assertEqual(CheckResultDB.__tablename__, "check_results")

    def test_nullable_result_columns(self):
        table = CheckResultDB.__table__

        self.assertTrue(table.c.status_code.nullable)
        self.assertTrue(table.c.error.nullable)
        self.assertFalse(table.c.latency_ms.nullable)

    def test_composite_result_index_exists(self):
        indexes = {
            index.name: tuple(column.name for column in index.columns)
            for index in CheckResultDB.__table__.indexes
        }

        self.assertEqual(
            indexes["ix_check_results_monitor_checked_at"],
            ("monitor_id", "checked_at"),
        )


if __name__ == "__main__":
    unittest.main()
