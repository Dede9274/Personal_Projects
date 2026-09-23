# Backend development

The backend provides the FastAPI application, PostgreSQL persistence,
scheduled monitor checks, incident detection, and email or webhook delivery.
Monitor targets are restricted to public HTTP(S) destinations, and every
redirect is resolved and revalidated before the worker follows it.

## Redis workers

Detailed design, failure semantics, and troubleshooting:

    docs/redis-workers.md
    docs/notifications.md

From the backend directory, start PostgreSQL, Redis, the migration job,
the scheduler, and a monitor worker:

    docker compose up -d --build

Confirm that checks are being scheduled and processed:

    docker compose ps
    docker compose logs -f scheduler monitor-worker

The scheduler and monitor worker are separate long-running services. Starting
only FastAPI and the frontend does not perform checks; those processes only
manage and display monitoring data.

For local development without the Dockerized Python services, start only the
infrastructure first:

    .\start_monitoring.ps1

This one command starts PostgreSQL and Redis, applies Alembic migrations, and
runs the scheduler plus one worker in the foreground. Keep that terminal open;
its output shows every queued and completed check. Press Ctrl+C to stop it.

You can still start every process manually when debugging:

    docker compose up -d postgres redis

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
