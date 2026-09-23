"""Load private notification transport settings from the environment."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)

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


@dataclass(frozen=True)
class SmtpConfigurationStatus:
    configured: bool
    host: str | None
    port: int | None
    security: str | None
    from_email: str | None
    error: str | None


def _smtp_transport_values() -> tuple[
    str,
    int,
    str | None,
    str | None,
    str,
    str,
]:
    host = os.getenv("SMTP_HOST", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    username = os.getenv("SMTP_USERNAME") or None
    password = os.getenv("SMTP_PASSWORD") or None
    security = os.getenv("SMTP_SECURITY", "starttls").strip().lower()

    if not host or host == "smtp.example.com":
        raise RuntimeError("Set SMTP_HOST to a real mail server")
    if not from_email or from_email == "uptime@example.com":
        raise RuntimeError("Set SMTP_FROM_EMAIL to a real sender address")
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
    except ValueError as error:
        raise RuntimeError("SMTP_PORT must be a number") from error

    if port <= 0:
        raise RuntimeError("SMTP_PORT must be positive")

    return host, port, username, password, from_email, security


def get_smtp_configuration_status() -> SmtpConfigurationStatus:
    """Return a browser-safe summary without exposing SMTP credentials."""
    try:
        host, port, _, _, from_email, security = _smtp_transport_values()
    except RuntimeError as error:
        return SmtpConfigurationStatus(
            configured=False,
            host=os.getenv("SMTP_HOST") or None,
            port=None,
            security=os.getenv("SMTP_SECURITY") or None,
            from_email=os.getenv("SMTP_FROM_EMAIL") or None,
            error=str(error),
        )

    return SmtpConfigurationStatus(
        configured=True,
        host=host,
        port=port,
        security=security,
        from_email=from_email,
        error=None,
    )


def get_email_settings(
    *,
    recipients: tuple[str, ...] | None = None,
    timeout_seconds: float | None = None,
) -> EmailSettings:
    (
        host,
        port,
        username,
        password,
        from_email,
        security,
    ) = _smtp_transport_values()

    if recipients is None:
        recipients = tuple(
            address.strip()
            for address in os.getenv("ALERT_EMAIL_TO", "").split(",")
            if address.strip()
        )
    if not recipients:
        raise RuntimeError(
            "ALERT_EMAIL_TO is required for email notifications"
        )

    if timeout_seconds is None:
        try:
            timeout_seconds = float(
                os.getenv("SMTP_TIMEOUT_SECONDS", "10")
            )
        except ValueError as error:
            raise RuntimeError(
                "SMTP_TIMEOUT_SECONDS must be a number"
            ) from error

    if timeout_seconds <= 0:
        raise RuntimeError("SMTP_TIMEOUT_SECONDS must be positive")

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


def get_webhook_settings(
    *,
    url: str | None = None,
    timeout_seconds: float | None = None,
) -> WebhookSettings:
    url = url or os.getenv("ALERT_WEBHOOK_URL", "").strip()

    if not url:
        raise RuntimeError(
            "ALERT_WEBHOOK_URL is required for webhook notifications"
        )

    if timeout_seconds is None:
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
