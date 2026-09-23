"""Request and response schemas for notification preferences."""

import re
from datetime import datetime
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


EMAIL_PATTERN = re.compile(r"^[^@\s,]+@[^@\s,]+\.[^@\s,]+$")


class NotificationPreferencesUpdate(BaseModel):
    """Dashboard-controlled notification settings."""

    model_config = ConfigDict(extra="forbid")

    email_enabled: bool
    email_recipients: list[str] = Field(max_length=20)
    email_timeout_seconds: float = Field(gt=0, le=120, allow_inf_nan=False)
    webhook_enabled: bool
    webhook_url: HttpUrl | None = None
    webhook_timeout_seconds: float = Field(
        gt=0,
        le=120,
        allow_inf_nan=False,
    )
    notify_incident_opened: bool

    @field_validator("email_recipients")
    @classmethod
    def normalize_recipients(cls, recipients: list[str]) -> list[str]:
        normalized: list[str] = []

        for recipient in recipients:
            address = recipient.strip()
            if not EMAIL_PATTERN.fullmatch(address):
                raise ValueError(f"Invalid email address: {recipient}")
            if address not in normalized:
                normalized.append(address)

        return normalized

    @model_validator(mode="after")
    def validate_enabled_channels(self) -> Self:
        if self.email_enabled and not self.email_recipients:
            raise ValueError(
                "At least one recipient is required when email is enabled"
            )
        if self.webhook_enabled and self.webhook_url is None:
            raise ValueError(
                "A webhook URL is required when webhooks are enabled"
            )
        return self


class NotificationPreferencesResponse(BaseModel):
    """Persisted preferences plus safe SMTP transport status."""

    email_enabled: bool
    email_recipients: list[str]
    email_timeout_seconds: float
    webhook_enabled: bool
    webhook_url: str | None
    webhook_timeout_seconds: float
    notify_incident_opened: bool
    smtp_configured: bool
    smtp_host: str | None
    smtp_port: int | None
    smtp_security: str | None
    smtp_from_email: str | None
    smtp_configuration_error: str | None
    updated_at: datetime


class TestEmailResponse(BaseModel):
    """Confirmation returned after SMTP accepts a test message."""

    message: str
    recipients: list[str]
