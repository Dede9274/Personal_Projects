DISTRIBUTED UPTIME MONITOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORE
[ ] HTTP checker
[ ] Monitor CRUD
[ ] PostgreSQL
[ ] Automatic scheduling
[ ] Check history

INCIDENT ENGINE
[ ] Consecutive failures
[ ] DOWN transition
[ ] Incident creation
[ ] Recovery
[ ] Incident history

DISTRIBUTED SYSTEM
[x] Redis Stream
[x] Scheduler producer
[x] Worker consumer
[x] Multiple workers
[x] ACK/retry
[x] Duplicate protection

FRONTEND
[ ] Monitor list
[ ] Monitor creation
[ ] Monitor details
[ ] Latency graph
[ ] Incident history
[ ] Dashboard statistics

ADVANCED
[ ] Alerts
[ ] Public status page
[ ] Remote agent
[ ] Agent heartbeat
[ ] Multiple regions

ENGINEERING
[ ] Unit tests
[ ] Integration tests
[ ] Docker
[ ] Docker Compose
[ ] CI
[ ] Load testing
[ ] Prometheus
[ ] Deployment

FINAL
[ ] Architecture diagram
[ ] README
[ ] Screenshots
[ ] Demo video
[ ] Resume description

STEP 1 -- Done
HTTP checker

STEP 2 -- Done
Monitor + CheckResult models

STEP 3 -- Done
Scheduler that runs monitors repeatedly

STEP 4 -- Done
PostgreSQL persistence

STEP 5 -- Done
FastAPI REST API

STEP 6 -- Done
Background workers / Redis queue

STEP 7
Incident detection

STEP 8
Notifications

STEP 9
React dashboard

STEP 10
Docker + deployment + monitoringSTEP 1 ✅
HTTP checker


REDIS WORKER DEVELOPMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Detailed design, failure semantics, and troubleshooting:

    docs/redis-workers.md
    docs/notifications.md

From the backend directory, start PostgreSQL and Redis:

    docker compose up -d

Start the scheduler producer in one terminal:

    ..\.venv\Scripts\python.exe -m app.scheduler_main

Start one or more workers in separate terminals:

    ..\.venv\Scripts\python.exe -m app.workers.monitor_worker --name worker-1
    ..\.venv\Scripts\python.exe -m app.workers.monitor_worker --name worker-2

Start the email/webhook notification worker in another terminal:

    ..\.venv\Scripts\python.exe -m app.workers.notification_worker --name notification-1

Every worker joins the same Redis consumer group. Redis gives each queued
message to one worker, and the worker acknowledges it only after the check
result and incident processing complete.

Run the Redis connectivity and queue integration tests:

    $env:RUN_REDIS_TESTS = "1"
    ..\.venv\Scripts\python.exe -m unittest -v tests.test_redis_integration tests.test_redis_queue_integration

