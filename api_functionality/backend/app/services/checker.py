import time
from datetime import datetime, timezone
import httpx
from app.models.monitor import Monitor, CheckResult


async def check_monitor(monitor: Monitor) -> CheckResult:
    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                monitor.url,
                timeout=monitor.timeout_seconds,
            )
        latency_ms = (time.perf_counter() - start_time) * 1000
        success = response.status_code == monitor.expected_status_code

        error = None
        if not success:
            error = (
                f"Expected status {monitor.expected_status_code}, "
                f"got {response.status_code} {response.reason_phrase}"
            ).strip()

        return CheckResult(
            status_code=response.status_code,
            latency_ms=latency_ms,
            success=success,
            error=error,
            checked_at=datetime.now(timezone.utc),
        )

    except httpx.TimeoutException as error:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return CheckResult(
            status_code=None,
            latency_ms=latency_ms,
            success=False,
            error=str(error) or "The request timed out",
            checked_at=datetime.now(timezone.utc),
        )

    except httpx.ConnectError as error:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return CheckResult(
            status_code=None,
            latency_ms=latency_ms,
            success=False,
            error=str(error) or "Could not connect to the server",
            checked_at=datetime.now(timezone.utc),
        )

    except httpx.RequestError as error:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return CheckResult(
            status_code=None,
            latency_ms=latency_ms,
            success=False,
            error=str(error) or "Request failed",
            checked_at=datetime.now(timezone.utc),
        )
