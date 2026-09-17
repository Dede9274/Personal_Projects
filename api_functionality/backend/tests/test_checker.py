import unittest
from unittest.mock import patch

import httpx

from app.models.monitor import Monitor
from app.services.checker import check_monitor


REAL_ASYNC_CLIENT = httpx.AsyncClient


class FakeAsyncClient:
    outcome: httpx.Response | Exception

    def __init__(self, *, follow_redirects: bool = False):
        self.follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url: str, timeout: float):
        if isinstance(self.outcome, Exception):
            raise self.outcome

        return self.outcome


class CheckerTests(unittest.IsolatedAsyncioTestCase):
    async def test_expected_status_is_successful(self):
        request = httpx.Request("GET", "https://example.test")
        FakeAsyncClient.outcome = httpx.Response(204, request=request)
        monitor = Monitor(
            name="Example",
            url=str(request.url),
            interval_seconds=30,
            timeout_seconds=5,
            expected_status_code=204,
        )

        with patch(
            "app.services.checker.httpx.AsyncClient",
            FakeAsyncClient,
        ):
            result = await check_monitor(monitor)

        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 204)
        self.assertIsNone(result.error)
        self.assertGreaterEqual(result.latency_ms, 0)
        self.assertIsNotNone(result.checked_at.tzinfo)

    async def test_redirect_to_expected_status_is_successful(self):
        def handle_request(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/redirect":
                return httpx.Response(
                    301,
                    headers={"Location": "/healthy"},
                    request=request,
                )

            return httpx.Response(200, request=request)

        def create_client(**kwargs):
            return REAL_ASYNC_CLIENT(
                transport=httpx.MockTransport(handle_request),
                **kwargs,
            )

        monitor = Monitor(
            name="Redirecting API",
            url="https://example.test/redirect",
            interval_seconds=30,
            timeout_seconds=5,
            expected_status_code=200,
        )

        with patch(
            "app.services.checker.httpx.AsyncClient",
            side_effect=create_client,
        ):
            result = await check_monitor(monitor)

        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error)

    async def test_unexpected_status_is_failure(self):
        request = httpx.Request("GET", "https://example.test")
        FakeAsyncClient.outcome = httpx.Response(200, request=request)
        monitor = Monitor(
            name="Example",
            url=str(request.url),
            interval_seconds=30,
            timeout_seconds=5,
            expected_status_code=204,
        )

        with patch(
            "app.services.checker.httpx.AsyncClient",
            FakeAsyncClient,
        ):
            result = await check_monitor(monitor)

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertIn("Expected status 204", result.error or "")

    async def test_timeout_has_no_status_code(self):
        request = httpx.Request("GET", "https://example.test")
        FakeAsyncClient.outcome = httpx.TimeoutException(
            "timed out",
            request=request,
        )
        monitor = Monitor(
            name="Example",
            url=str(request.url),
            interval_seconds=30,
            timeout_seconds=5,
        )

        with patch(
            "app.services.checker.httpx.AsyncClient",
            FakeAsyncClient,
        ):
            result = await check_monitor(monitor)

        self.assertFalse(result.success)
        self.assertIsNone(result.status_code)
        self.assertEqual(result.error, "timed out")
        self.assertGreaterEqual(result.latency_ms, 0)


if __name__ == "__main__":
    unittest.main()
