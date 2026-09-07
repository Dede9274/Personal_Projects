"""Load notification settings from the backend .env file."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from app.models.notification import NotificationChannel


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)

TRUE_VALUES = {"1", "true", "yes", "on"}
SMTP_SECURITY_VALUES = {"starttls", "ssl", "none"}


@dataclass(frozen=True)
class EmailSettings:
    host: str
    port: int
    username: str | None
    password: str | None = field(repr=False)
    from_email: str
    recipients: tuple[str, ...]
    security: str
    timeout_seconds: float


@dataclass(frozen=True)
class WebhookSettings:
    url: str
    bearer_token: str | None = field(repr=False)
    signing_secret: str | None = field(repr=False)
    timeout_seconds: float


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in TRUE_VALUES


def get_enabled_notification_channels() -> list[NotificationChannel]:
    """Return the channels explicitly enabled in environment settings."""
    channels: list[NotificationChannel] = []

    if _enabled("EMAIL_NOTIFICATIONS_ENABLED"):
        channels.append(NotificationChannel.EMAIL)

    if _enabled("WEBHOOK_NOTIFICATIONS_ENABLED"):
        channels.append(NotificationChannel.WEBHOOK)

    return channels


def get_email_settings() -> EmailSettings:
    host = os.getenv("SMTP_HOST", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    recipients = tuple(
        address.strip()
        for address in os.getenv("ALERT_EMAIL_TO", "").split(",")
        if address.strip()
    )
    username = os.getenv("SMTP_USERNAME") or None
    password = os.getenv("SMTP_PASSWORD") or None
    security = os.getenv("SMTP_SECURITY", "starttls").strip().lower()

    if not host:
        raise RuntimeError("SMTP_HOST is required for email notifications")
    if not from_email:
        raise RuntimeError(
            "SMTP_FROM_EMAIL is required for email notifications"
        )
    if not recipients:
        raise RuntimeError(
            "ALERT_EMAIL_TO is required for email notifications"
        )
    if (username is None) != (password is None):
        raise RuntimeError(
            "SMTP_USERNAME and SMTP_PASSWORD must be set together"
        )
    if security not in SMTP_SECURITY_VALUES:
        raise RuntimeError(
            "SMTP_SECURITY must be starttls, ssl, or none"
        )

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        timeout_seconds = float(os.getenv("SMTP_TIMEOUT_SECONDS", "10"))
    except ValueError as error:
        raise RuntimeError(
            "SMTP_PORT and SMTP_TIMEOUT_SECONDS must be numbers"
        ) from error

    if port <= 0 or timeout_seconds <= 0:
        raise RuntimeError(
            "SMTP_PORT and SMTP_TIMEOUT_SECONDS must be positive"
        )

    return EmailSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        from_email=from_email,
        recipients=recipients,
        security=security,
        timeout_seconds=timeout_seconds,
    )


def get_webhook_settings() -> WebhookSettings:
    url = os.getenv("ALERT_WEBHOOK_URL", "").strip()

    if not url:
        raise RuntimeError(
            "ALERT_WEBHOOK_URL is required for webhook notifications"
        )

    try:
        timeout_seconds = float(
            os.getenv("WEBHOOK_TIMEOUT_SECONDS", "10")
        )
    except ValueError as error:
        raise RuntimeError(
            "WEBHOOK_TIMEOUT_SECONDS must be a number"
        ) from error

    if timeout_seconds <= 0:
        raise RuntimeError(
            "WEBHOOK_TIMEOUT_SECONDS must be positive"
        )

    return WebhookSettings(
        url=url,
        bearer_token=os.getenv("WEBHOOK_BEARER_TOKEN") or None,
        signing_secret=os.getenv("WEBHOOK_SIGNING_SECRET") or None,
        timeout_seconds=timeout_seconds,
    )
