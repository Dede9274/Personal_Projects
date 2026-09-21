"""Perform monitor checks while enforcing the outbound request policy."""

import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx

from app.models.monitor import CheckResult, Monitor
from app.security.url_validator import (
    MonitorUrlRejectedError,
    validate_monitor_url,
)


MAX_REDIRECTS = 5
REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})


def _result(
    start_time: float,
    *,
    status_code: int | None,
    success: bool,
    error: str | None,
    security_rejected: bool = False,
) -> CheckResult:
    return CheckResult(
        status_code=status_code,
        latency_ms=(time.perf_counter() - start_time) * 1000,
        success=success,
        error=error,
        checked_at=datetime.now(timezone.utc),
        security_rejected=security_rejected,
    )


async def _get_with_validated_redirects(
    client: httpx.AsyncClient,
    url: str,
    timeout_seconds: float,
) -> httpx.Response:
    current_url = url

    for redirect_count in range(MAX_REDIRECTS + 1):
        await validate_monitor_url(current_url)
        response = await client.get(
            current_url,
            timeout=timeout_seconds,
        )

        location = response.headers.get("Location")
        if (
            response.status_code not in REDIRECT_STATUS_CODES
            or location is None
        ):
            return response

        if redirect_count >= MAX_REDIRECTS:
            raise httpx.TooManyRedirects(
                f"The target exceeded the limit of {MAX_REDIRECTS} redirects",
                request=response.request,
            )

        current_url = urljoin(str(response.url), location)

    raise RuntimeError("Redirect handling exhausted unexpectedly")


async def check_monitor(monitor: Monitor) -> CheckResult:
    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = await _get_with_validated_redirects(
                client,
                monitor.url,
                monitor.timeout_seconds,
            )

        success = response.status_code == monitor.expected_status_code
        error = None
        if not success:
            error = (
                f"Expected status {monitor.expected_status_code}, "
                f"got {response.status_code} {response.reason_phrase}"
            ).strip()

        return _result(
            start_time,
            status_code=response.status_code,
            success=success,
            error=error,
        )

    except MonitorUrlRejectedError as error:
        return _result(
            start_time,
            status_code=None,
            success=False,
            error=str(error),
            security_rejected=True,
        )

    except httpx.TimeoutException as error:
        return _result(
            start_time,
            status_code=None,
            success=False,
            error=str(error) or "The request timed out",
        )

    except httpx.ConnectError as error:
        return _result(
            start_time,
            status_code=None,
            success=False,
            error=str(error) or "Could not connect to the server",
        )

    except httpx.RequestError as error:
        return _result(
            start_time,
            status_code=None,
            success=False,
            error=str(error) or "Request failed",
        )
