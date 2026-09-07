"""Redis-backed monitor and notification job queues."""

# Monitor-check queue
MONITOR_STREAM = "uptime:monitor-checks"
MONITOR_CONSUMER_GROUP = "monitor-workers"
MONITOR_DEAD_LETTER_STREAM = "uptime:monitor-checks:dead"
MONITOR_JOB_LOCK_PREFIX = "uptime:monitor-check:outstanding"


# Incident-notification queue
NOTIFICATION_STREAM = "uptime:notifications"
NOTIFICATION_CONSUMER_GROUP = "notification-workers"
NOTIFICATION_DEAD_LETTER_STREAM = "uptime:notifications:dead"
NOTIFICATION_LOCK_PREFIX = "uptime:notification:incident-opened"
STREAM_MAX_LENGTH = 10_000
DEFAULT_MAX_ATTEMPTS = 3
