r"""Insert development monitors into PostgreSQL on demand.

Run from the backend directory with:

    ..\.venv\Scripts\python.exe -m app.database.seed_monitors

The seed is idempotent by URL, so running it again skips existing monitors.
"""

import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.database.connection import async_session_factory, engine
from app.database.models import MonitorDB


@dataclass(frozen=True, slots=True)
class SeedMonitor:
    name: str
    url: str
    purpose: str
    interval_seconds: int
    timeout_seconds: float
    expected_status_code: int = 200
    is_active: bool = True


SEED_MONITORS = (
    SeedMonitor(
        name="Google",
        url="https://www.google.com",
        purpose="Public search-engine availability check.",
        interval_seconds=300,
        timeout_seconds=10,
    ),
    SeedMonitor(
        name="GitHub API",
        url="https://api.github.com",
        purpose="Public GitHub API availability check.",
        interval_seconds=300,
        timeout_seconds=10,
    ),
    SeedMonitor(
        name="HTTPBin Health",
        url="https://httpbin.org/status/200",
        purpose="Simple endpoint used to verify successful HTTP checks.",
        interval_seconds=60,
        timeout_seconds=5,
    ),
)


async def seed_monitors() -> list[str]:
    """Create missing seed monitors and return the names that were added."""
    seed_urls = [monitor.url for monitor in SEED_MONITORS]
    statement = select(MonitorDB.url).where(MonitorDB.url.in_(seed_urls))

    async with async_session_factory() as session:
        result = await session.execute(statement)
        existing_urls = set(result.scalars().all())

        monitors_to_create = [
            monitor
            for monitor in SEED_MONITORS
            if monitor.url not in existing_urls
        ]

        session.add_all(
            [
                MonitorDB(
                    name=monitor.name,
                    url=monitor.url,
                    purpose=monitor.purpose,
                    interval_seconds=monitor.interval_seconds,
                    timeout_seconds=monitor.timeout_seconds,
                    expected_status_code=monitor.expected_status_code,
                    is_active=monitor.is_active,
                )
                for monitor in monitors_to_create
            ]
        )

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return [monitor.name for monitor in monitors_to_create]


async def main() -> None:
    try:
        created_names = await seed_monitors()

        if created_names:
            print(f"Created {len(created_names)} monitor(s):")
            for name in created_names:
                print(f"- {name}")
        else:
            print("All seed monitors already exist; nothing was added.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
