from dataclasses import dataclass
from datetime import datetime

@dataclass
class Monitor:
    name: str
    url: str
    interval_seconds: int
    timeout_seconds: float
    expected_status_code: int = 200
    purpose: str = ""
    id: int | None = None

@dataclass
class CheckResult:
    status_code: int | None
    latency_ms: float
    success: bool
    error: str | None
    checked_at: datetime
