from app.database.models import IncidentDB
from app.database.repository import (
    create_incident,
    get_active_incident,
    get_check_results,
    increment_incident,
    resolve_incident,
)
from app.models.monitor import CheckResult


CONSECUTIVE_FAILURES_TO_OPEN = 3


def _failure_message(check_result: CheckResult) -> str:
    if check_result.error is not None:
        return check_result.error

    if check_result.status_code is not None:
        return f"Unexpected HTTP status {check_result.status_code}"

    return "Monitor check failed"


async def process_check_result(
    monitor_id: int,
    check_result: CheckResult,
) -> IncidentDB | None:
    """Update incident state after the check result has been persisted."""
    if check_result.security_rejected:
        return None

    active_incident = await get_active_incident(monitor_id)

    if check_result.success:
        if active_incident is None:
            return None

        return await resolve_incident(
            monitor_id=monitor_id,
            resolved_at=check_result.checked_at,
        )

    current_error = _failure_message(check_result)

    if active_incident is not None:
        return await increment_incident(
            incident_id=active_incident.id,
            last_error=current_error,
            last_failure_at=check_result.checked_at,
        )

    recent_results = await get_check_results(
        monitor_id=monitor_id,
        limit=CONSECUTIVE_FAILURES_TO_OPEN,
    )

    if len(recent_results) < CONSECUTIVE_FAILURES_TO_OPEN:
        return None

    if any(
        result.success or result.security_rejected
        for result in recent_results
    ):
        return None

    failures = sorted(
        recent_results,
        key=lambda result: result.checked_at,
    )
    first_failure = failures[0]

    incident = await create_incident(
        monitor_id=monitor_id,
        started_at=first_failure.checked_at,
        last_error=_failure_message(first_failure),
    )

    # create_incident() represents failure one. Replay failures two and
    # three so the newly opened incident accurately represents the streak.
    for failure in failures[1:]:
        updated_incident = await increment_incident(
            incident_id=incident.id,
            last_error=_failure_message(failure),
            last_failure_at=failure.checked_at,
        )

        if updated_incident is None:
            raise RuntimeError(
                "A newly created incident could not be incremented"
            )

        incident = updated_incident

    return incident
