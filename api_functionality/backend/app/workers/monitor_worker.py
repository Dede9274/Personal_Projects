"""Standalone Redis worker that performs queued monitor checks."""

import argparse
import asyncio
import logging
import sys

from app.database.connection import engine
from app.database.repository import (
    get_active_monitor,
    save_check_result,
)
from app.models.incident import IncidentStatus
from app.queue.connection import (
    check_redis_connection,
    close_redis_connection,
)
from app.queue.worker import MonitorStreamWorker
from app.services.checker import check_monitor
from app.services.incident_service import process_check_result
from app.services.notification_service import (
    enqueue_incident_opened_notifications,
)


logger = logging.getLogger(__name__)


async def execute_monitor_job(monitor_id: int) -> None:
    """Check one active monitor and persist the result before incidents."""
    monitor = await get_active_monitor(monitor_id)

    if monitor is None:
        logger.info(
            "Skipping monitor %s because it is missing or inactive",
            monitor_id,
        )
        return

    logger.info("Checking %s (monitor %s)", monitor.name, monitor_id)
    result = await check_monitor(monitor)

    # This ordering is important: incident detection reads recent saved checks.
    await save_check_result(
        monitor_id=monitor_id,
        check_result=result,
    )
    incident = await process_check_result(
        monitor_id=monitor_id,
        check_result=result,
    )

    # The incident service returns the existing OPEN incident for every
    # additional failure. Per-channel Redis locks make these calls retry-safe
    # while allowing only one email and one webhook for the incident.
    if (
        incident is not None
        and incident.status == IncidentStatus.OPEN.value
    ):
        queued_notifications = await enqueue_incident_opened_notifications(
            incident_id=incident.id,
            monitor_id=monitor_id,
        )

        for channel, message_id in queued_notifications.items():
            if message_id is not None:
                logger.info(
                    "Queued %s notification %s for incident %s",
                    channel.value,
                    message_id,
                    incident.id,
                )

    state = "UP" if result.success else "DOWN"
    logger.info(
        "%s: %s - %.2fms",
        monitor.name,
        state,
        result.latency_ms,
    )

    if result.error is not None:
        logger.info("%s error: %s", monitor.name, result.error)


async def main(consumer_name: str | None = None) -> None:
    worker = MonitorStreamWorker(
        execute_monitor_job,
        consumer_name=consumer_name,
    )

    try:
        await check_redis_connection()
        await worker.run()
    finally:
        await close_redis_connection()
        await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a monitor worker")
    parser.add_argument(
        "--name",
        dest="consumer_name",
        help="Unique Redis consumer name; defaults to hostname-process_id",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )

        asyncio.run(main(arguments.consumer_name))
    except KeyboardInterrupt:
        print("\nWorker interrupted")
