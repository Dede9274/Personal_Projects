import asyncio
import time
from dataclasses import dataclass

from app.models.monitor import Monitor
from app.queue.producer import enqueue_monitor_check


@dataclass
class ScheduledMonitor:
    monitor: Monitor
    next_run: float
    running: bool = False


class Scheduler:
    def __init__(self, monitors: list[Monitor]):
        current_time = time.monotonic()

        for monitor in monitors:
            if monitor.interval_seconds <= 0:
                raise ValueError(f"{monitor.name} must have a positive time interval")
            
        self.schedule = [ScheduledMonitor(monitor=monitor, next_run=current_time) for monitor in monitors]
         
        # Create an empty set for asyncio tasks that don't return a value.
        self.active_tasks: set[asyncio.Task[None]] = set() 
        self.running = False

    #Execute task
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

    #Handle finished tasks
    def handle_finished_task(self, task: asyncio.Task[None]) -> None:
        self.active_tasks.discard(task)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            print(f"Unexpected task error {error}")

    #Scheduler that handles which task runs next
    async def run(self) -> None:
        self.running = True
        print("Scheduler started")

        try:
            while self.running:
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

                #let monitor task time to run and prevent loop from constantky consuming CPU    
                await asyncio.sleep(0.1)
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
        

    

