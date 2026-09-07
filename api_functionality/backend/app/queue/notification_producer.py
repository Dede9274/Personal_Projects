"""Publish channel-specific incident notification jobs to Redis."""

from redis.asyncio import Redis

from app.models.notification import NotificationChannel
from app.queue import NOTIFICATION_LOCK_PREFIX, NOTIFICATION_STREAM
from app.queue.connection import redis_client


# Redis executes a Lua script atomically. Two monitor workers therefore cannot
# enqueue the same incident/channel pair between a separate EXISTS and XADD.
_ENQUEUE_NOTIFICATION_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    return false
end

local message_id = redis.call(
    'XADD', KEYS[2], '*',
    'incident_id', ARGV[1],
    'monitor_id', ARGV[2],
    'channel', ARGV[3],
    'event_type', 'INCIDENT_OPENED',
    'attempt', '1'
)

redis.call('SET', KEYS[1], message_id)
return message_id
"""


def notification_lock_key(
    incident_id: int,
    channel: NotificationChannel,
) -> str:
    """Return the deduplication key for one incident and channel."""
    return (
        f"{NOTIFICATION_LOCK_PREFIX}:"
        f"{incident_id}:{channel.value.lower()}"
    )


async def enqueue_incident_opened_notification(
    *,
    incident_id: int,
    monitor_id: int,
    channel: NotificationChannel,
    client: Redis = redis_client,
) -> str | None:
    """Enqueue once, returning None when this channel is already handled."""
    if incident_id <= 0:
        raise ValueError("incident_id must be positive")
    if monitor_id <= 0:
        raise ValueError("monitor_id must be positive")
    if not isinstance(channel, NotificationChannel):
        raise TypeError("channel must be a NotificationChannel")

    message_id = await client.eval(
        _ENQUEUE_NOTIFICATION_SCRIPT,
        2,
        notification_lock_key(incident_id, channel),
        NOTIFICATION_STREAM,
        str(incident_id),
        str(monitor_id),
        channel.value,
    )

    if message_id is None or message_id is False:
        return None

    if isinstance(message_id, bytes):
        return message_id.decode()

    return str(message_id)
