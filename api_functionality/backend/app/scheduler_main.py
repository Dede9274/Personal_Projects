"""Standalone entry point for the monitor scheduler."""

import asyncio
import sys

from app.database.connection import engine
from app.database.repository import get_active_monitors
from app.services.scheduler import Scheduler


async def main() -> None:
    try:
        monitors = await get_active_monitors()

        if not monitors:
            print("No active monitors found")
            return

        scheduler = Scheduler(monitors)
        await scheduler.run()
    finally:
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
