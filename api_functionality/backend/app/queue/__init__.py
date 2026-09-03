"""Redis-backed monitor job queue."""

MONITOR_STREAM = "uptime:monitor-checks"
MONITOR_CONSUMER_GROUP = "monitor-workers"
MONITOR_DEAD_LETTER_STREAM = "uptime:monitor-checks:dead"
MONITOR_JOB_LOCK_PREFIX = "uptime:monitor-check:outstanding"

STREAM_MAX_LENGTH = 10_000
DEFAULT_MAX_ATTEMPTS = 3
