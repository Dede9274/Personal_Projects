import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.models.monitor import Monitor
from app.queue.producer import enqueue_monitor_check


MonitorLoader = Callable[[], Awaitable[list[Monitor]]]


@dataclass
class ScheduledMonitor:
    monitor: Monitor
    next_run: float
    running: bool = False


class Scheduler:
    def __init__(
        self,
        monitors: list[Monitor] | None = None,
        *,
        monitor_loader: MonitorLoader | None = None,
        refresh_interval_seconds: float = 5.0,
        poll_interval_seconds: float = 0.1,
    ):
        monitors = monitors or []
        current_time = time.monotonic()

        for monitor in monitors:
            self._validate_monitor(monitor)

        if refresh_interval_seconds <= 0:
            raise ValueError("refresh_interval_seconds must be positive")
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")

        self.schedule = [
            ScheduledMonitor(monitor=monitor, next_run=current_time)
            for monitor in monitors
        ]
        self.monitor_loader = monitor_loader
        self.refresh_interval_seconds = refresh_interval_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.next_refresh = current_time if monitor_loader is not None else None

        # Create an empty set for asyncio tasks that don't return a value.
        self.active_tasks: set[asyncio.Task[None]] = set()
        self.running = False

    @staticmethod
    def _validate_monitor(monitor: Monitor) -> None:
        if monitor.interval_seconds <= 0:
            raise ValueError(
                f"{monitor.name} must have a positive time interval"
            )

    def reconcile_monitors(
        self,
        monitors: list[Monitor],
        *,
        current_time: float | None = None,
    ) -> None:
        """Make the in-memory schedule match the active database monitors."""
        if current_time is None:
            current_time = time.monotonic()

        for monitor in monitors:
            self._validate_monitor(monitor)
            if monitor.id is None:
                raise ValueError(
                    f"Active monitor {monitor.name} has no database ID"
                )

        monitor_ids = [monitor.id for monitor in monitors]
        if len(monitor_ids) != len(set(monitor_ids)):
            raise ValueError("Active monitor IDs must be unique")

        existing_by_id = {
            scheduled.monitor.id: scheduled
            for scheduled in self.schedule
            if scheduled.monitor.id is not None
        }
        reconciled_schedule: list[ScheduledMonitor] = []

        for monitor in monitors:
            scheduled_monitor = existing_by_id.get(monitor.id)

            if scheduled_monitor is None:
                # A newly created or reactivated monitor is checked promptly.
                scheduled_monitor = ScheduledMonitor(
                    monitor=monitor,
                    next_run=current_time,
                )
            else:
                interval_changed = (
                    scheduled_monitor.monitor.interval_seconds
                    != monitor.interval_seconds
                )
                scheduled_monitor.monitor = monitor

                if interval_changed:
                    # Start a fresh cadence from the time the change is seen.
                    scheduled_monitor.next_run = (
                        current_time + monitor.interval_seconds
                    )

            reconciled_schedule.append(scheduled_monitor)

        self.schedule = reconciled_schedule

    async def refresh_monitors(self) -> None:
        """Reload active monitors and reconcile them with the schedule."""
        if self.monitor_loader is None:
            return

        monitors = await self.monitor_loader()
        self.reconcile_monitors(monitors)

    # Execute task
    async def execute_monitor(self, scheduled_monitor: ScheduledMonitor) -> None:
        monitor = scheduled_monitor.monitor
        try:
            if monitor.id is None:
                raise RuntimeError(
                    f"{monitor.name} has no database ID"
                )

            message_id = await enqueue_monitor_check(monitor.id)

            if message_id is None:
                print(f"{monitor.name} already has an outstanding job")
            else:
                print(f"Queued {monitor.name} as Redis job {message_id}")
        finally:
            scheduled_monitor.running = False

    # Handle finished tasks
    def handle_finished_task(self, task: asyncio.Task[None]) -> None:
        self.active_tasks.discard(task)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            print(f"Unexpected task error {error}")

    # Scheduler that handles which task runs next
    async def run(self) -> None:
        self.running = True
        print("Scheduler started")

        try:
            while self.running:
                current_time = time.monotonic()

                if (
                    self.monitor_loader is not None
                    and self.next_refresh is not None
                    and current_time >= self.next_refresh
                ):
                    try:
                        await self.refresh_monitors()
                    except Exception as error:
                        # Keep the last known schedule during a temporary
                        # database failure, then retry on the next refresh.
                        print(f"Could not refresh active monitors: {error}")
                    finally:
                        self.next_refresh = (
                            time.monotonic()
                            + self.refresh_interval_seconds
                        )

                    current_time = time.monotonic()

                for scheduled_monitor in self.schedule:
                    is_due = current_time >= scheduled_monitor.next_run

                    if is_due and not scheduled_monitor.running:
                        monitor = scheduled_monitor.monitor

                        # Update when this monitor should run next.
                        while scheduled_monitor.next_run <= current_time:
                            scheduled_monitor.next_run += monitor.interval_seconds

                        scheduled_monitor.running = True
                        task = asyncio.create_task(
                            self.execute_monitor(scheduled_monitor),
                            name=f"monitor:{monitor.name}",
                        )

                        self.active_tasks.add(task)
                        task.add_done_callback(
                            self.handle_finished_task
                        )

                # Give tasks time to run and prevent constant CPU usage.
                await asyncio.sleep(self.poll_interval_seconds)
        finally:
            self.running = False

            #allowing checks that are already runnning to finish
            if self.active_tasks:
                await asyncio.gather(
                    *tuple(self.active_tasks), return_exceptions=True
                )

            print("Scheduler stopped")

    def stop(self) -> None:
        self.running = False
