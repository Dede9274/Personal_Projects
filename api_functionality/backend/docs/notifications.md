# Email and webhook incident notifications

The notification system sends an alert after the third consecutive failed
check opens an incident. Additional failures update the incident but do not
send duplicate alerts.

## Delivery flow

```text
monitor worker
    -> save CheckResult
    -> process incident rules
    -> receive OPEN IncidentDB
    -> enqueue one Redis job per enabled channel

notification worker
    -> read one channel-specific Redis job
    -> load the incident and monitor from PostgreSQL
    -> send email or webhook
    -> mark that incident/channel pair SENT in Redis
```

Email and webhook use different jobs and different deduplication keys. If the
webhook fails after email succeeds, only the webhook is retried.

## Email configuration

SMTP credentials remain in the private project-root `.env` file and are not
stored in PostgreSQL or returned by the API. Configure the transport first:

Email with STARTTLS, commonly on port 587:

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password_or_app_password
SMTP_FROM_EMAIL=uptime@example.com
```

Use `SMTP_SECURITY=ssl` for implicit TLS, commonly on port 465. Use `none`
only for a trusted local development SMTP server. Username and password may
both be blank when the SMTP server does not require authentication.

Recreate the API and workers after changing environment values:

```bash
docker compose up -d --build --force-recreate api monitor-worker notification-worker
```

Open `http://localhost:3000/notifications`, enter one or more recipients,
enable email notifications, and save. The page stores those preferences in
PostgreSQL. Use **Send test email** to make a real SMTP delivery attempt before
waiting for an incident.

The dashboard and its API own these non-secret settings:

- Email and webhook enabled state
- Email recipients
- Webhook URL
- Email and webhook timeouts
- Incident-opened event selection

## Webhook configuration

The webhook URL and enabled state are saved in the dashboard. Optional webhook
credentials remain in `.env`:

```dotenv
WEBHOOK_BEARER_TOKEN=optional_bearer_token
WEBHOOK_SIGNING_SECRET=optional_shared_secret
```

Each channel can be enabled or disabled independently. `.env` is ignored by
Git; never commit SMTP passwords, app passwords, bearer tokens, or signing
secrets.

## Webhook request

The worker sends `POST` with `Content-Type: application/json`:

```json
{
  "event": "incident.opened",
  "event_id": "incident-opened:42",
  "sent_at": "2026-09-05T12:00:00+00:00",
  "monitor": {
    "id": 7,
    "name": "Production API",
    "url": "https://api.example.com"
  },
  "incident": {
    "id": 42,
    "monitor_id": 7,
    "status": "OPEN",
    "started_at": "2026-09-05T11:59:00+00:00",
    "failure_count": 3,
    "last_error": "Connection timed out"
  }
}
```

When a bearer token is configured, the request includes:

```text
Authorization: Bearer <token>
```

When a signing secret is configured, `X-Uptime-Signature` contains
`sha256=<hex digest>`, calculated with HMAC-SHA256 over the exact raw request
body. The receiving service should calculate the same value and use a
constant-time comparison.

## Running the worker

From `backend`, keep the existing API, scheduler, and monitor worker running.
Start the notification worker in another terminal:

```powershell
..\.venv\Scripts\python.exe -m app.workers.notification_worker --name notification-1
```

Multiple notification workers may use different names. They join the same
Redis consumer group and share jobs.

## Retry and deduplication behavior

Each notification gets three attempts. A successful channel receives a
persistent Redis marker:

```text
uptime:notification:incident-opened:{incident_id}:{channel} = SENT
```

A permanently failed channel is moved to `uptime:notifications:dead` and
marked `FAILED`. This prevents every later failed monitor check from starting
another delivery cycle.

Useful inspection commands:

```powershell
docker exec uptime-redis redis-cli XLEN uptime:notifications
docker exec uptime-redis redis-cli XINFO GROUPS uptime:notifications
docker exec uptime-redis redis-cli XRANGE uptime:notifications:dead - +
docker exec uptime-redis redis-cli --scan --pattern "uptime:notification:incident-opened:*"
```

The current design uses Redis persistence for notification delivery state.
A future PostgreSQL transactional outbox would close the small failure window
between committing an incident and enqueueing its first notification.
