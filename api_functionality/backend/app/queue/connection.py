"""Shared asynchronous Redis connection."""

import os
from pathlib import Path

from dotenv import load_dotenv
from redis.asyncio import Redis


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client: Redis = Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30,
)


async def check_redis_connection() -> bool:
    """Return True when Redis responds to PING."""
    return bool(await redis_client.ping())


async def close_redis_connection() -> None:
    """Close this process's Redis client and connection pool."""
    await redis_client.aclose()
