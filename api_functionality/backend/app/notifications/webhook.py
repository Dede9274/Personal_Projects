"""Send signed JSON incident notifications to a generic webhook."""

import hashlib
import hmac
import json
from datetime import datetime, timezone

import httpx

from app.database.models import IncidentDB
from app.models.monitor import Monitor
from app.notifications.config import WebhookSettings, get_webhook_settings


def build_incident_opened_payload(
    *,
    incident: IncidentDB,
    monitor: Monitor,
) -> dict[str, object]:
    """Return the stable JSON structure received by webhook consumers."""
    return {
        "event": "incident.opened",
        "event_id": f"incident-opened:{incident.id}",
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "monitor": {
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
        },
        "incident": {
            "id": incident.id,
            "monitor_id": incident.monitor_id,
            "status": incident.status,
            "started_at": incident.started_at.isoformat(),
            "failure_count": incident.failure_count,
            "last_error": incident.last_error,
        },
    }


async def send_incident_opened_webhook(
    *,
    incident: IncidentDB,
    monitor: Monitor,
    settings: WebhookSettings | None = None,
) -> None:
    settings = settings or get_webhook_settings()
    payload = build_incident_opened_payload(
        incident=incident,
        monitor=monitor,
    )
    body = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "X-Uptime-Event": "incident.opened",
        "X-Uptime-Event-Id": f"incident-opened:{incident.id}",
    }

    if settings.bearer_token is not None:
        headers["Authorization"] = f"Bearer {settings.bearer_token}"

    if settings.signing_secret is not None:
        digest = hmac.new(
            settings.signing_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        headers["X-Uptime-Signature"] = f"sha256={digest}"

    async with httpx.AsyncClient(
        timeout=settings.timeout_seconds,
    ) as client:
        response = await client.post(
            settings.url,
            content=body,
            headers=headers,
        )
        response.raise_for_status()
