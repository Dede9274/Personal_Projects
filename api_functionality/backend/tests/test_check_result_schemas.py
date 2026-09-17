import unittest
from datetime import datetime, timezone

from app.database.models import CheckResultDB
from app.schemas.check_result import CheckResultResponse


class CheckResultSchemaTests(unittest.TestCase):
    def test_response_schema_accepts_an_orm_result(self):
        checked_at = datetime.now(timezone.utc)
        result_db = CheckResultDB(
            id=12,
            monitor_id=3,
            checked_at=checked_at,
            status_code=None,
            latency_ms=5000.25,
            success=False,
            error="The request timed out",
        )

        response = CheckResultResponse.model_validate(result_db)

        self.assertEqual(response.id, 12)
        self.assertEqual(response.monitor_id, 3)
        self.assertEqual(response.checked_at, checked_at)
        self.assertIsNone(response.status_code)
        self.assertEqual(response.latency_ms, 5000.25)
        self.assertFalse(response.success)
        self.assertEqual(response.error, "The request timed out")


if __name__ == "__main__":
    unittest.main()
