"""Redis Stream consumer for email and webhook notifications."""

import asyncio
import json
import logging
import os
import socket
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from app.models.notification import NotificationChannel
from app.queue import (
    DEFAULT_MAX_ATTEMPTS,
    NOTIFICATION_CONSUMER_GROUP,
    NOTIFICATION_DEAD_LETTER_STREAM,
    NOTIFICATION_STREAM,
    STREAM_MAX_LENGTH,
)
from app.queue.connection import redis_client
from app.queue.notification_producer import notification_lock_key


logger = logging.getLogger(__name__)
NotificationHandler = Callable[
    [int, int, NotificationChannel],
    Awaitable[None],
]


@dataclass(frozen=True)
class NotificationJob:
    message_id: str
    incident_id: int
    monitor_id: int
    channel: NotificationChannel
    event_type: str
    attempt: int


class NotificationStreamWorker:
    """Consume, retry, recover, and acknowledge notification jobs."""

    def __init__(
        self,
        handler: NotificationHandler,
        *,
        client: Redis = redis_client,
        consumer_name: str | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        block_ms: int = 1_000,
        claim_idle_ms: int = 60_000,
        claim_interval_seconds: float = 30,
    ) -> None:
        if max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if block_ms <= 0:
            raise ValueError("block_ms must be positive")
        if claim_idle_ms <= 0:
            raise ValueError("claim_idle_ms must be positive")
        if claim_interval_seconds <= 0:
            raise ValueError("claim_interval_seconds must be positive")

        self.handler = handler
        self.client = client
        self.consumer_name = consumer_name or (
            f"{socket.gethostname()}-{os.getpid()}"
        )
        self.max_attempts = max_attempts
        self.block_ms = block_ms
        self.claim_idle_ms = claim_idle_ms
        self.claim_interval_seconds = claim_interval_seconds
        self.running = False

    async def ensure_consumer_group(self) -> None:
        try:
            await self.client.xgroup_create(
                NOTIFICATION_STREAM,
                NOTIFICATION_CONSUMER_GROUP,
                id="0",
                mkstream=True,
            )
        except ResponseError as error:
            if "BUSYGROUP" not in str(error):
                raise

    async def run(self) -> None:
        await self.ensure_consumer_group()
        self.running = True
        last_claim_at = 0.0
        logger.info("Notification worker %s started", self.consumer_name)

        try:
            while self.running:
                now = time.monotonic()

                if now - last_claim_at >= self.claim_interval_seconds:
                    for message_id, fields in await self._claim_stale_jobs():
                        await self.process_message(message_id, fields)
                    last_claim_at = now

                for message_id, fields in await self._read_new_jobs():
                    await self.process_message(message_id, fields)
        finally:
            self.running = False
            logger.info("Notification worker %s stopped", self.consumer_name)

    def stop(self) -> None:
        self.running = False

    async def _read_new_jobs(
        self,
    ) -> list[tuple[str, Mapping[str, str]]]:
        response = await self.client.xreadgroup(
            NOTIFICATION_CONSUMER_GROUP,
            self.consumer_name,
            streams={NOTIFICATION_STREAM: ">"},
            count=1,
            block=self.block_ms,
        )

        if not response:
            return []

        return list(response[0][1])

    async def _claim_stale_jobs(
        self,
    ) -> list[tuple[str, Mapping[str, str]]]:
        response = await self.client.xautoclaim(
            NOTIFICATION_STREAM,
            NOTIFICATION_CONSUMER_GROUP,
            self.consumer_name,
            min_idle_time=self.claim_idle_ms,
            start_id="0-0",
            count=1,
        )

        if len(response) < 2:
            return []

        return list(response[1])

    async def process_message(
        self,
        message_id: str,
        fields: Mapping[str, str],
    ) -> None:
        try:
            job = self._parse_job(message_id, fields)
        except (KeyError, TypeError, ValueError) as error:
            await self._dead_letter_invalid_message(
                message_id,
                fields,
                error,
            )
            return

        heartbeat = asyncio.create_task(
            self._heartbeat(job),
            name=f"notification-heartbeat:{job.message_id}",
        )
        processing_error: Exception | None = None

        try:
            try:
                await self.handler(
                    job.incident_id,
                    job.monitor_id,
                    job.channel,
                )
            except asyncio.CancelledError:
                # Leave the message pending so another worker can claim it.
                raise
            except Exception as error:
                processing_error = error
        finally:
            heartbeat.cancel()
            await asyncio.gather(heartbeat, return_exceptions=True)

        if processing_error is not None:
            await self._retry_or_dead_letter(job, processing_error)
            return

        await self._acknowledge_and_mark_sent(job)

    async def _heartbeat(self, job: NotificationJob) -> None:
        interval_seconds = max(self.claim_idle_ms / 3_000, 0.1)

        while True:
            await asyncio.sleep(interval_seconds)
            await self.client.xclaim(
                NOTIFICATION_STREAM,
                NOTIFICATION_CONSUMER_GROUP,
                self.consumer_name,
                min_idle_time=0,
                message_ids=[job.message_id],
                idle=0,
                justid=True,
            )

    @staticmethod
    def _parse_job(
        message_id: str,
        fields: Mapping[str, str],
    ) -> NotificationJob:
        incident_id = int(fields["incident_id"])
        monitor_id = int(fields["monitor_id"])
        attempt = int(fields.get("attempt", "1"))
        channel = NotificationChannel(fields["channel"])
        event_type = fields["event_type"]

        if incident_id <= 0:
            raise ValueError("incident_id must be positive")
        if monitor_id <= 0:
            raise ValueError("monitor_id must be positive")
        if attempt <= 0:
            raise ValueError("attempt must be positive")
        if event_type != "INCIDENT_OPENED":
            raise ValueError(f"Unsupported event_type: {event_type}")

        return NotificationJob(
            message_id=str(message_id),
            incident_id=incident_id,
            monitor_id=monitor_id,
            channel=channel,
            event_type=event_type,
            attempt=attempt,
        )

    async def _acknowledge_and_mark_sent(
        self,
        job: NotificationJob,
    ) -> None:
        async with self.client.pipeline(transaction=True) as pipeline:
            # Keep a marker so later DOWN checks cannot resend this channel.
            pipeline.set(
                notification_lock_key(job.incident_id, job.channel),
                "SENT",
            )
            pipeline.xack(
                NOTIFICATION_STREAM,
                NOTIFICATION_CONSUMER_GROUP,
                job.message_id,
            )
            pipeline.xdel(NOTIFICATION_STREAM, job.message_id)
            await pipeline.execute()

    async def _retry_or_dead_letter(
        self,
        job: NotificationJob,
        error: Exception,
    ) -> None:
        error_message = f"{type(error).__name__}: {error}"[:1_000]

        async with self.client.pipeline(transaction=True) as pipeline:
            if job.attempt < self.max_attempts:
                pipeline.xadd(
                    NOTIFICATION_STREAM,
                    {
                        "incident_id": str(job.incident_id),
                        "monitor_id": str(job.monitor_id),
                        "channel": job.channel.value,
                        "event_type": job.event_type,
                        "attempt": str(job.attempt + 1),
                        "previous_error": error_message,
                    },
                )
            else:
                pipeline.xadd(
                    NOTIFICATION_DEAD_LETTER_STREAM,
                    {
                        "incident_id": str(job.incident_id),
                        "monitor_id": str(job.monitor_id),
                        "channel": job.channel.value,
                        "event_type": job.event_type,
                        "attempt": str(job.attempt),
                        "error": error_message,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                        "source_message_id": job.message_id,
                    },
                    maxlen=STREAM_MAX_LENGTH,
                    approximate=True,
                )
                pipeline.set(
                    notification_lock_key(job.incident_id, job.channel),
                    "FAILED",
                )

            pipeline.xack(
                NOTIFICATION_STREAM,
                NOTIFICATION_CONSUMER_GROUP,
                job.message_id,
            )
            pipeline.xdel(NOTIFICATION_STREAM, job.message_id)
            await pipeline.execute()

        if job.attempt < self.max_attempts:
            logger.error(
                "%s notification for incident %s failed on attempt %s; "
                "queued retry: %s",
                job.channel.value,
                job.incident_id,
                job.attempt,
                error_message,
            )
        else:
            logger.error(
                "%s notification for incident %s exhausted %s attempts; "
                "moved to dead-letter stream: %s",
                job.channel.value,
                job.incident_id,
                self.max_attempts,
                error_message,
            )

    async def _dead_letter_invalid_message(
        self,
        message_id: str,
        fields: Mapping[str, str],
        error: Exception,
    ) -> None:
        async with self.client.pipeline(transaction=True) as pipeline:
            pipeline.xadd(
                NOTIFICATION_DEAD_LETTER_STREAM,
                {
                    "error": f"Invalid notification job: {error}"[:1_000],
                    "raw_fields": json.dumps(dict(fields), default=str),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "source_message_id": str(message_id),
                },
                maxlen=STREAM_MAX_LENGTH,
                approximate=True,
            )
            pipeline.xack(
                NOTIFICATION_STREAM,
                NOTIFICATION_CONSUMER_GROUP,
                message_id,
            )
            pipeline.xdel(NOTIFICATION_STREAM, message_id)
            await pipeline.execute()
