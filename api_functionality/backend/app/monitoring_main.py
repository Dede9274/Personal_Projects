"""Run the local scheduler and one monitor worker in a single process."""

import asyncio
import logging
import sys

from app.database.connection import engine
from app.database.repository import get_active_monitors
from app.queue.connection import (
    check_redis_connection,
    close_redis_connection,
)
from app.queue.worker import MonitorStreamWorker
from app.services.scheduler import Scheduler
from app.workers.monitor_worker import execute_monitor_job


logger = logging.getLogger(__name__)


async def main() -> None:
    """Keep scheduling and processing checks until the process is stopped."""
    scheduler = Scheduler(monitor_loader=get_active_monitors)
    worker = MonitorStreamWorker(execute_monitor_job)
    tasks: set[asyncio.Task[None]] = set()

    try:
        await check_redis_connection()

        tasks = {
            asyncio.create_task(scheduler.run(), name="scheduler"),
            asyncio.create_task(worker.run(), name="monitor-worker"),
        }

        done, _ = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        for completed_task in done:
            if completed_task.cancelled():
                continue

            error = completed_task.exception()
            if error is not None:
                raise error

        stopped_names = ", ".join(
            sorted(task.get_name() for task in done)
        )
        raise RuntimeError(f"{stopped_names} stopped unexpectedly")
    finally:
        scheduler.stop()
        worker.stop()

        for task in tasks:
            if not task.done():
                task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        cleanup_results = await asyncio.gather(
            close_redis_connection(),
            engine.dispose(),
            return_exceptions=True,
        )
        for cleanup_result in cleanup_results:
            if isinstance(cleanup_result, BaseException):
                logger.error(
                    "Monitoring resource cleanup failed: %s",
                    cleanup_result,
                )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )

        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Monitoring engine interrupted")
