import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.models.monitor import Monitor
from app.services.checker import check_monitor


REAL_ASYNC_CLIENT = httpx.AsyncClient


class FakeAsyncClient:
    outcome: httpx.Response | Exception

    def __init__(
        self,
        *,
        follow_redirects: bool = False,
        trust_env: bool = True,
    ):
        self.follow_redirects = follow_redirects
        self.trust_env = trust_env

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

        with (
            patch(
                "app.services.checker.httpx.AsyncClient",
                FakeAsyncClient,
            ),
            patch(
                "app.services.checker.validate_monitor_url",
                AsyncMock(),
            ),
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

        validate_mock = AsyncMock()
        with (
            patch(
                "app.services.checker.httpx.AsyncClient",
                side_effect=create_client,
            ),
            patch(
                "app.services.checker.validate_monitor_url",
                validate_mock,
            ),
        ):
            result = await check_monitor(monitor)

        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error)
        self.assertEqual(
            [call.args[0] for call in validate_mock.await_args_list],
            [
                "https://example.test/redirect",
                "https://example.test/healthy",
            ],
        )

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

        with (
            patch(
                "app.services.checker.httpx.AsyncClient",
                FakeAsyncClient,
            ),
            patch(
                "app.services.checker.validate_monitor_url",
                AsyncMock(),
            ),
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

        with (
            patch(
                "app.services.checker.httpx.AsyncClient",
                FakeAsyncClient,
            ),
            patch(
                "app.services.checker.validate_monitor_url",
                AsyncMock(),
            ),
        ):
            result = await check_monitor(monitor)

        self.assertFalse(result.success)
        self.assertIsNone(result.status_code)
        self.assertEqual(result.error, "timed out")
        self.assertGreaterEqual(result.latency_ms, 0)

    async def test_security_rejection_is_not_an_outage_result(self):
        from app.security.url_validator import MonitorUrlRejectedError

        monitor = Monitor(
            name="Internal target",
            url="http://127.0.0.1:6379",
            interval_seconds=30,
            timeout_seconds=5,
        )

        with (
            patch(
                "app.services.checker.httpx.AsyncClient",
                FakeAsyncClient,
            ),
            patch(
                "app.services.checker.validate_monitor_url",
                AsyncMock(
                    side_effect=MonitorUrlRejectedError(
                        "The target is not public."
                    )
                ),
            ),
        ):
            result = await check_monitor(monitor)

        self.assertFalse(result.success)
        self.assertTrue(result.security_rejected)
        self.assertIsNone(result.status_code)
        self.assertIn("Monitor URL rejected", result.error or "")

    async def test_redirect_destination_is_rejected_before_request(self):
        from app.security.url_validator import MonitorUrlRejectedError

        requested_urls: list[str] = []

        def handle_request(request: httpx.Request) -> httpx.Response:
            requested_urls.append(str(request.url))
            return httpx.Response(
                302,
                headers={"Location": "http://127.0.0.1:8000/admin"},
                request=request,
            )

        def create_client(**kwargs):
            return REAL_ASYNC_CLIENT(
                transport=httpx.MockTransport(handle_request),
                **kwargs,
            )

        monitor = Monitor(
            name="Redirecting target",
            url="https://example.test/start",
            interval_seconds=30,
            timeout_seconds=5,
        )
        validate_mock = AsyncMock(
            side_effect=[
                None,
                MonitorUrlRejectedError("The target is not public."),
            ]
        )

        with (
            patch(
                "app.services.checker.httpx.AsyncClient",
                side_effect=create_client,
            ),
            patch(
                "app.services.checker.validate_monitor_url",
                validate_mock,
            ),
        ):
            result = await check_monitor(monitor)

        self.assertTrue(result.security_rejected)
        self.assertEqual(requested_urls, ["https://example.test/start"])

    async def test_redirect_chain_stops_after_five_hops(self):
        requested_urls: list[str] = []

        def handle_request(request: httpx.Request) -> httpx.Response:
            requested_urls.append(str(request.url))
            return httpx.Response(
                302,
                headers={"Location": f"/hop/{len(requested_urls)}"},
                request=request,
            )

        def create_client(**kwargs):
            return REAL_ASYNC_CLIENT(
                transport=httpx.MockTransport(handle_request),
                **kwargs,
            )

        monitor = Monitor(
            name="Redirect loop",
            url="https://example.test/start",
            interval_seconds=30,
            timeout_seconds=5,
        )

        with (
            patch(
                "app.services.checker.httpx.AsyncClient",
                side_effect=create_client,
            ),
            patch(
                "app.services.checker.validate_monitor_url",
                AsyncMock(),
            ) as validate_mock,
        ):
            result = await check_monitor(monitor)

        self.assertFalse(result.success)
        self.assertFalse(result.security_rejected)
        self.assertIn("limit of 5 redirects", result.error or "")
        self.assertEqual(len(requested_urls), 6)
        self.assertEqual(validate_mock.await_count, 6)


if __name__ == "__main__":
    unittest.main()
