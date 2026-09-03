"""Publish monitor-check jobs to Redis Streams."""

from redis.asyncio import Redis

from app.queue import (
    MONITOR_JOB_LOCK_PREFIX,
    MONITOR_STREAM,
)
from app.queue.connection import redis_client


# Checking the lock, adding the message, and recording its ID must happen as
# one Redis operation. Otherwise two scheduler processes could both enqueue
# the same monitor between a separate EXISTS and XADD call.
_ENQUEUE_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    return false
end

local message_id = redis.call(
    'XADD', KEYS[2], '*',
    'monitor_id', ARGV[1],
    'attempt', '1'
)
redis.call('SET', KEYS[1], message_id)
return message_id
"""


def monitor_job_lock_key(monitor_id: int) -> str:
    """Return the duplicate-protection key for one monitor."""
    return f"{MONITOR_JOB_LOCK_PREFIX}:{monitor_id}"


async def enqueue_monitor_check(
    monitor_id: int,
    *,
    client: Redis = redis_client,
) -> str | None:
    """Enqueue a monitor once, returning None if it is already outstanding."""
    if monitor_id <= 0:
        raise ValueError("monitor_id must be positive")

    message_id = await client.eval(
        _ENQUEUE_SCRIPT,
        2,
        monitor_job_lock_key(monitor_id),
        MONITOR_STREAM,
        str(monitor_id),
    )

    if message_id is None or message_id is False:
        return None

    if isinstance(message_id, bytes):
        return message_id.decode()

    return str(message_id)
