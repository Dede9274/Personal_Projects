"""HTTP endpoints for persisted notification preferences and email tests."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.database.repository import (
    get_notification_preferences,
    update_notification_preferences,
)
from app.models.notification import NotificationPreferences
from app.notifications.config import (
    get_email_settings,
    get_smtp_configuration_status,
)
from app.notifications.email import send_test_email
from app.schemas.notification import (
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    TestEmailResponse,
)


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/notification-settings",
    tags=["notifications"],
)


def _response(
    preferences: NotificationPreferences,
) -> NotificationPreferencesResponse:
    smtp = get_smtp_configuration_status()
    return NotificationPreferencesResponse(
        email_enabled=preferences.email_enabled,
        email_recipients=list(preferences.email_recipients),
        email_timeout_seconds=preferences.email_timeout_seconds,
        webhook_enabled=preferences.webhook_enabled,
        webhook_url=preferences.webhook_url,
        webhook_timeout_seconds=preferences.webhook_timeout_seconds,
        notify_incident_opened=preferences.notify_incident_opened,
        smtp_configured=smtp.configured,
        smtp_host=smtp.host,
        smtp_port=smtp.port,
        smtp_security=smtp.security,
        smtp_from_email=smtp.from_email,
        smtp_configuration_error=smtp.error,
        updated_at=preferences.updated_at,
    )


@router.get("", response_model=NotificationPreferencesResponse)
async def read_notification_preferences() -> NotificationPreferencesResponse:
    preferences = await get_notification_preferences()
    return _response(preferences)


@router.patch("", response_model=NotificationPreferencesResponse)
async def save_notification_preferences(
    data: NotificationPreferencesUpdate,
) -> NotificationPreferencesResponse:
    smtp = get_smtp_configuration_status()
    if data.email_enabled and not smtp.configured:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=smtp.error or "SMTP transport is not configured",
        )

    current = await get_notification_preferences()
    preferences = NotificationPreferences(
        email_enabled=data.email_enabled,
        email_recipients=tuple(data.email_recipients),
        email_timeout_seconds=data.email_timeout_seconds,
        webhook_enabled=data.webhook_enabled,
        webhook_url=(
            str(data.webhook_url) if data.webhook_url is not None else None
        ),
        webhook_timeout_seconds=data.webhook_timeout_seconds,
        notify_incident_opened=data.notify_incident_opened,
        updated_at=current.updated_at,
    )
    saved = await update_notification_preferences(preferences)
    return _response(saved)


@router.post("/test-email", response_model=TestEmailResponse)
async def test_email_delivery() -> TestEmailResponse:
    preferences = await get_notification_preferences()

    if not preferences.email_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Enable and save email notifications first",
        )

    try:
        settings = get_email_settings(
            recipients=preferences.email_recipients,
            timeout_seconds=preferences.email_timeout_seconds,
        )
        await send_test_email(settings=settings)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("Test email delivery failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "The SMTP server did not accept the test email. "
                "Check the API logs for details."
            ),
        ) from error

    return TestEmailResponse(
        message="Test email accepted by the SMTP server",
        recipients=list(preferences.email_recipients),
    )
