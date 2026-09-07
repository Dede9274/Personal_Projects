"""Standalone entry point for the monitor scheduler."""

import asyncio
import sys

from app.database.connection import engine
from app.database.repository import get_active_monitors
from app.queue.connection import close_redis_connection
from app.services.scheduler import Scheduler


async def main() -> None:
    try:
        # The scheduler owns the refresh loop. It remains alive when the
        # database is empty and notices API changes without a restart.
        scheduler = Scheduler(monitor_loader=get_active_monitors)
        await scheduler.run()
    finally:
        await close_redis_connection()
        await engine.dispose()


if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScheduler interrupted")
