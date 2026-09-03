"""Reusable Redis Stream consumer for monitor-check jobs."""

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

from app.queue import (
    DEFAULT_MAX_ATTEMPTS,
    MONITOR_CONSUMER_GROUP,
    MONITOR_DEAD_LETTER_STREAM,
    MONITOR_STREAM,
    STREAM_MAX_LENGTH,
)
from app.queue.connection import redis_client
from app.queue.producer import monitor_job_lock_key


logger = logging.getLogger(__name__)
JobHandler = Callable[[int], Awaitable[None]]


@dataclass(frozen=True)
class MonitorJob:
    message_id: str
    monitor_id: int
    attempt: int


class MonitorStreamWorker:
    """Consume, process, retry, and acknowledge monitor jobs."""

    def __init__(
        self,
        handler: JobHandler,
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
        """Create the shared worker group and stream if they do not exist."""
        try:
            await self.client.xgroup_create(
                MONITOR_STREAM,
                MONITOR_CONSUMER_GROUP,
                id="0",
                mkstream=True,
            )
        except ResponseError as error:
            if "BUSYGROUP" not in str(error):
                raise

    async def run(self) -> None:
        """Process jobs until stop() is called or this task is cancelled."""
        await self.ensure_consumer_group()
        self.running = True
        last_claim_at = 0.0
        logger.info("Worker %s started", self.consumer_name)

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
            logger.info("Worker %s stopped", self.consumer_name)

    def stop(self) -> None:
        self.running = False

    async def _read_new_jobs(
        self,
    ) -> list[tuple[str, Mapping[str, str]]]:
        response = await self.client.xreadgroup(
            MONITOR_CONSUMER_GROUP,
            self.consumer_name,
            streams={MONITOR_STREAM: ">"},
            # Own only what this worker can start immediately. A prefetched
            # batch could become idle and be reclaimed before it is processed.
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
            MONITOR_STREAM,
            MONITOR_CONSUMER_GROUP,
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
        """Run one job and update its Redis delivery state."""
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
            name=f"redis-heartbeat:{job.message_id}",
        )
        processing_error: Exception | None = None

        try:
            try:
                await self.handler(job.monitor_id)
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

        await self._acknowledge_and_release(job)

    async def _heartbeat(self, job: MonitorJob) -> None:
        """Keep a healthy long-running job from looking abandoned."""
        interval_seconds = max(self.claim_idle_ms / 3_000, 0.1)

        while True:
            await asyncio.sleep(interval_seconds)
            await self.client.xclaim(
                MONITOR_STREAM,
                MONITOR_CONSUMER_GROUP,
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
    ) -> MonitorJob:
        monitor_id = int(fields["monitor_id"])
        attempt = int(fields.get("attempt", "1"))

        if monitor_id <= 0:
            raise ValueError("monitor_id must be positive")
        if attempt <= 0:
            raise ValueError("attempt must be positive")

        return MonitorJob(
            message_id=str(message_id),
            monitor_id=monitor_id,
            attempt=attempt,
        )

    async def _acknowledge_and_release(self, job: MonitorJob) -> None:
        async with self.client.pipeline(transaction=True) as pipeline:
            pipeline.xack(
                MONITOR_STREAM,
                MONITOR_CONSUMER_GROUP,
                job.message_id,
            )
            pipeline.xdel(MONITOR_STREAM, job.message_id)
            pipeline.delete(monitor_job_lock_key(job.monitor_id))
            await pipeline.execute()

    async def _retry_or_dead_letter(
        self,
        job: MonitorJob,
        error: Exception,
    ) -> None:
        error_message = f"{type(error).__name__}: {error}"[:1_000]

        async with self.client.pipeline(transaction=True) as pipeline:
            if job.attempt < self.max_attempts:
                pipeline.xadd(
                    MONITOR_STREAM,
                    {
                        "monitor_id": str(job.monitor_id),
                        "attempt": str(job.attempt + 1),
                        "previous_error": error_message,
                    },
                )
            else:
                pipeline.xadd(
                    MONITOR_DEAD_LETTER_STREAM,
                    {
                        "monitor_id": str(job.monitor_id),
                        "attempt": str(job.attempt),
                        "error": error_message,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                        "source_message_id": job.message_id,
                    },
                    maxlen=STREAM_MAX_LENGTH,
                    approximate=True,
                )
                pipeline.delete(monitor_job_lock_key(job.monitor_id))

            pipeline.xack(
                MONITOR_STREAM,
                MONITOR_CONSUMER_GROUP,
                job.message_id,
            )
            pipeline.xdel(MONITOR_STREAM, job.message_id)
            await pipeline.execute()

        if job.attempt < self.max_attempts:
            logger.error(
                "Monitor %s failed on attempt %s; queued retry: %s",
                job.monitor_id,
                job.attempt,
                error_message,
            )
        else:
            logger.error(
                "Monitor %s exhausted %s attempts; moved to dead-letter "
                "stream: %s",
                job.monitor_id,
                self.max_attempts,
                error_message,
            )

    async def _dead_letter_invalid_message(
        self,
        message_id: str,
        fields: Mapping[str, str],
        error: Exception,
    ) -> None:
        monitor_id = self._valid_monitor_id_or_none(fields)

        async with self.client.pipeline(transaction=True) as pipeline:
            pipeline.xadd(
                MONITOR_DEAD_LETTER_STREAM,
                {
                    "error": f"Invalid job: {error}"[:1_000],
                    "raw_fields": json.dumps(dict(fields), default=str),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "source_message_id": str(message_id),
                },
                maxlen=STREAM_MAX_LENGTH,
                approximate=True,
            )
            pipeline.xack(
                MONITOR_STREAM,
                MONITOR_CONSUMER_GROUP,
                message_id,
            )
            pipeline.xdel(MONITOR_STREAM, message_id)
            if monitor_id is not None:
                pipeline.delete(monitor_job_lock_key(monitor_id))
            await pipeline.execute()

    @staticmethod
    def _valid_monitor_id_or_none(
        fields: Mapping[str, str],
    ) -> int | None:
        try:
            monitor_id = int(fields["monitor_id"])
        except (KeyError, TypeError, ValueError):
            return None

        return monitor_id if monitor_id > 0 else None
