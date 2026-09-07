# Redis worker architecture

## What changed

The scheduler no longer performs HTTP checks itself. Monitor checking and
incident notification delivery run as separate worker roles:

```text


Scheduler producer
    |
    | monitor_id
    v
Redis Stream
    |
    | one message per consumer
    v
Monitor workers
    |
    +--> load monitor from PostgreSQL
    +--> call check_monitor()
    +--> save CheckResult
    +--> call process_check_result()
    +--> enqueue email/webhook notification jobs for OPEN incidents
    +--> acknowledge the Redis message

Notification workers
    |
    +--> consume one channel-specific notification job
    +--> load monitor and incident data from PostgreSQL
    +--> send email or webhook
    +--> acknowledge the Redis message
```

PostgreSQL remains the source of truth for monitors, check results, and
incidents. Redis contains temporary job-delivery state; it is not where monitor
configuration or results are stored.

## Project files

| File | Responsibility |
| --- | --- |
| `compose.yaml` | Runs PostgreSQL and Redis locally. |
| `.env.example` | Documents `REDIS_URL` and `REDIS_PORT`. |
| `app/queue/connection.py` | Creates and closes the shared async Redis client for one process. |
| `app/queue/producer.py` | Atomically deduplicates and adds monitor jobs to the stream. |
| `app/queue/worker.py` | Implements consumer groups, ownership heartbeats, ACK, retry, stale-job recovery, and dead-lettering. |
| `app/workers/monitor_worker.py` | Contains the monitor-specific job handler and worker command-line entry point. |
| `app/services/scheduler.py` | Decides when monitors are due and asks the producer to enqueue them. |
| `app/scheduler_main.py` | Runs the producer scheduler with a recurring PostgreSQL monitor loader. |
| `app/database/repository.py` | Lets a worker load one active monitor by ID. |
| `app/queue/notification_producer.py` | Atomically deduplicates notification jobs per incident and channel. |
| `app/queue/notification_worker.py` | Delivers notification jobs with retry, stale-job recovery, and dead-lettering. |
| `app/workers/notification_worker.py` | Dispatches notification jobs to the email or webhook sender. |
| `docs/notifications.md` | Documents channel configuration, payloads, and operation. |

## Redis keys and message data

The implementation uses these Redis keys:

| Key | Meaning |
| --- | --- |
| `uptime:monitor-checks` | Stream containing queued or currently owned jobs. |
| `monitor-workers` | Consumer group shared by every monitor worker. |
| `uptime:monitor-check:outstanding:{monitor_id}` | Duplicate-protection key for one monitor. |
| `uptime:monitor-checks:dead` | Jobs that failed on all three attempts or were malformed. |
| `uptime:notifications` | Channel-specific incident notification jobs. |
| `notification-workers` | Consumer group shared by notification workers. |
| `uptime:notification:incident-opened:{incident_id}:{channel}` | Per-channel notification deduplication and final state. |
| `uptime:notifications:dead` | Notifications that exhausted their retries. |

A new message begins with only the data a worker needs to locate current
configuration:

```text
monitor_id = 7
attempt = 1
```

The URL and timeout are deliberately not copied into Redis. A worker loads
monitor 7 from PostgreSQL, so it uses the newest saved configuration and can
skip a monitor that has been deleted or deactivated.

## How multiple workers share jobs

Every worker joins the same Redis consumer group but has a unique consumer
name. `XREADGROUP` gives each stream entry to one consumer in that group.

```text
job 101 --> worker-1
job 102 --> worker-2
job 103 --> worker-1 or worker-2, whichever asks next
```

Each worker requests only one message at a time. This avoids claiming a batch
of messages that the process cannot start immediately.

The worker runs an ownership heartbeat during a check. The heartbeat resets
the pending message's idle time, so another worker does not mistake a healthy
slow check for an abandoned job. A worker only uses `XAUTOCLAIM` when a pending
message has had no heartbeat for 60 seconds.

## Duplicate-job prevention

An in-process `scheduled_monitor.running` flag is visible only to that Python
process. It cannot coordinate a separate scheduler and worker, or two scheduler
processes.

The Redis producer therefore uses a per-monitor outstanding key. Checking the
key, adding the stream entry, and saving the message ID in the key happen in
one Lua script. Redis runs the script atomically, so another producer cannot
insert itself between those operations.

For a 30-second monitor whose check takes 45 seconds:

```text
t=0   scheduler creates job and outstanding:7
t=30  scheduler sees outstanding:7 and does not create another job
t=45  worker finishes, ACKs the job, and deletes outstanding:7
t=60  scheduler can create the next job
```

The lock remains present while a job is queued, running, or waiting for a
retry. It is released only when:

- processing succeeds;
- the monitor no longer exists or is inactive, which counts as a successful
  no-op;
- all retries are exhausted and the job is moved to the dead-letter stream;
- a malformed message contains a valid monitor ID that can be unlocked.

## Acknowledgement, retry, and worker crashes

An HTTP response that means the monitored site is DOWN is not a queue failure.
The checker returns `CheckResult(success=False)`, the worker saves it, incident
processing runs, and the queue job is acknowledged normally.

A queue attempt fails when the handler raises an unexpected exception, such as
a PostgreSQL outage. The worker then adds a replacement message with an
incremented attempt number and atomically acknowledges and deletes the old
message. After attempt 3, it writes the job and error to the dead-letter stream
and releases the outstanding key.

If a worker crashes before saving a result:

```text
worker receives message
    |
    X no ACK and heartbeat stops
    |
message remains in the pending-entry list
    |
after 60 seconds, another worker uses XAUTOCLAIM
    |
job runs again
```

This is **at-least-once delivery**: the system prefers occasionally repeating
work over silently losing it.

There is still an important failure window:

```text
PostgreSQL commit succeeds
    |
worker crashes before Redis ACK
    |
another worker eventually runs the job again
```

The Redis outstanding key prevents duplicate scheduling, but it cannot make a
PostgreSQL commit and Redis ACK one atomic transaction. Full processing
idempotency would require adding a unique `job_id` to the database and making
result/incident writes recognize an already-completed job.

## Redis connection lifecycle

The project uses `redis.asyncio.Redis`. Creating the client is synchronous and
connections are opened lazily when the first awaited command runs. One client
per process shares its internal connection pool between async tasks.

The scheduler and worker call `await close_redis_connection()` during shutdown.
Each process owns its own pool; pools are not shared between operating-system
processes.

## Docker configuration

Redis runs from `redis:8.2-alpine` with:

- port `6379` exposed only on `127.0.0.1`;
- append-only persistence with `appendfsync everysec`;
- a named `redis_data` volume;
- a `redis-cli ping` health check;
- `restart: unless-stopped`.

For locally executed Python, use:

```text
REDIS_URL=redis://localhost:6379/0
```

If the Python application is later moved into the same Compose network, use
the Compose service name instead:

```text
REDIS_URL=redis://redis:6379/0
```

The current Redis port is safe for local development because it is bound only
to localhost. Add authentication/TLS and keep Redis on a private network for a
real deployment.

## Running the system

Run these commands from `backend`.

Start infrastructure:

```powershell
docker compose up -d
docker compose ps
docker exec uptime-redis redis-cli PING
```

Start the scheduler producer:

```powershell
..\.venv\Scripts\python.exe -m app.scheduler_main
```

Start two workers in two additional terminals:

```powershell
..\.venv\Scripts\python.exe -m app.workers.monitor_worker --name worker-1
```

```powershell
..\.venv\Scripts\python.exe -m app.workers.monitor_worker --name worker-2
```

The `--name` option is useful while learning and reading logs. If it is
omitted, the program creates a unique name from the hostname and process ID.

The FastAPI server remains a separate process:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Inspecting Redis

Useful development commands:

```powershell
# Number of queued or pending stream entries
docker exec uptime-redis redis-cli XLEN uptime:monitor-checks

# Consumer-group state
docker exec uptime-redis redis-cli XINFO GROUPS uptime:monitor-checks

# Messages delivered but not yet acknowledged
docker exec uptime-redis redis-cli XPENDING uptime:monitor-checks monitor-workers

# Jobs that exhausted their retries
docker exec uptime-redis redis-cli XRANGE uptime:monitor-checks:dead - + COUNT 20

# Outstanding per-monitor locks
docker exec uptime-redis redis-cli --scan --pattern "uptime:monitor-check:outstanding:*"
```

## Tests

Run all normal tests:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests
```

Run the live Redis tests:

```powershell
$env:RUN_REDIS_TESTS = "1"
..\.venv\Scripts\python.exe -m unittest -v tests.test_redis_integration tests.test_redis_queue_integration
```

The queue integration test uses isolated temporary keys. It verifies that two
consumer identities process separate jobs, a duplicate enqueue is refused,
ACK removes completed work, and the monitor can be scheduled again afterward.

## Current limitations and next improvements

1. The scheduler reloads active monitors from PostgreSQL every five seconds.
   New and reactivated monitors are scheduled immediately, interval changes
   start a new cadence, and inactive or deleted monitors are removed from the
   in-memory schedule. A database refresh failure keeps the last known schedule
   and is retried rather than stopping the service.
2. Delivery is at least once, not exactly once. Add a database-backed unique
   job ID for full result idempotency.
3. Retries happen immediately. A delayed retry stream or sorted set could add
   exponential backoff.
4. Dead-letter jobs require manual inspection and replay.
5. Local Redis is a single instance, not a highly available deployment.
6. If someone manually deletes a stream entry without deleting its outstanding
   key, that monitor remains blocked until the orphan key is removed.

## Terms introduced by this design

- **Deduplication:** preventing two outstanding scheduled jobs for one monitor.
- **Idempotency:** making repeated processing produce the same final state as
  processing once.
- **Distributed lock:** shared coordination state visible to separate processes.
- **At-least-once delivery:** a job is not intentionally lost, but may repeat.
- **Race condition:** behavior that depends on which concurrent operation wins.
- **ACK:** the worker tells Redis that processing completed.
- **Dead-letter stream:** storage for jobs that cannot succeed after retries.
