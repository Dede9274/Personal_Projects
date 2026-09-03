import os
import unittest

if os.getenv("RUN_DATABASE_TESTS") != "1":
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@localhost:5432/test",
    )

from app.queue.connection import (
    check_redis_connection,
    close_redis_connection,
)


@unittest.skipUnless(
    os.getenv("RUN_REDIS_TESTS") == "1",
    "set RUN_REDIS_TESTS=1 to run Redis integration tests",
)
class RedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_redis_responds_to_ping(self):
        self.assertTrue(await check_redis_connection())

    async def asyncTearDown(self):
        await close_redis_connection()


if __name__ == "__main__":
    unittest.main()
