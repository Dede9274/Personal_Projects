"""Send incident-opened notifications through SMTP email."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.database.models import IncidentDB
from app.models.monitor import Monitor
from app.notifications.config import EmailSettings, get_email_settings


def build_incident_email(
    *,
    incident: IncidentDB,
    monitor: Monitor,
    settings: EmailSettings,
) -> EmailMessage:
    """Build the email without performing network I/O."""
    safe_monitor_name = monitor.name.replace("\r", " ").replace("\n", " ")
    error_message = incident.last_error or "No error details available"

    message = EmailMessage()
    message["Subject"] = f"[DOWN] {safe_monitor_name}"
    message["From"] = settings.from_email
    message["To"] = ", ".join(settings.recipients)
    message.set_content(
        "Monitor incident opened\n\n"
        f"Monitor: {monitor.name}\n"
        f"URL: {monitor.url}\n"
        f"Incident ID: {incident.id}\n"
        f"Started at: {incident.started_at.isoformat()}\n"
        f"Failure count: {incident.failure_count}\n"
        f"Latest error: {error_message}\n"
    )
    return message


def _send_email_sync(
    message: EmailMessage,
    settings: EmailSettings,
) -> None:
    """Perform blocking SMTP work; called through asyncio.to_thread()."""
    tls_context = ssl.create_default_context()

    if settings.security == "ssl":
        server_context = smtplib.SMTP_SSL(
            settings.host,
            settings.port,
            timeout=settings.timeout_seconds,
            context=tls_context,
        )
    else:
        server_context = smtplib.SMTP(
            settings.host,
            settings.port,
            timeout=settings.timeout_seconds,
        )

    with server_context as server:
        if settings.security == "starttls":
            server.starttls(context=tls_context)

        if settings.username is not None:
            server.login(settings.username, settings.password or "")

        server.send_message(message)


async def send_incident_opened_email(
    *,
    incident: IncidentDB,
    monitor: Monitor,
    settings: EmailSettings | None = None,
) -> None:
    settings = settings or get_email_settings()
    message = build_incident_email(
        incident=incident,
        monitor=monitor,
        settings=settings,
    )
    await asyncio.to_thread(_send_email_sync, message, settings)
