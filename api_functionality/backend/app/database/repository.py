from datetime import datetime, timezone

from sqlalchemy import select

from app.database.connection import async_session_factory
from app.database.models import CheckResultDB, IncidentDB, MonitorDB
from app.models.monitor import CheckResult, Monitor


def _monitor_to_domain(monitor_db: MonitorDB) -> Monitor:
    return Monitor(
        id=monitor_db.id,
        name=monitor_db.name,
        url=monitor_db.url,
        interval_seconds=monitor_db.interval_seconds,
        timeout_seconds=monitor_db.timeout_seconds,
        expected_status_code=monitor_db.expected_status_code,
    )


def _check_result_to_domain(result_db: CheckResultDB) -> CheckResult:
    return CheckResult(
        status_code=result_db.status_code,
        latency_ms=result_db.latency_ms,
        success=result_db.success,
        error=result_db.error,
        checked_at=result_db.checked_at,
    )


async def create_monitor(
    name: str,
    url: str,
    interval_seconds: int,
    timeout_seconds: float,
    expected_status_code: int = 200,
) -> Monitor:
    monitor_db = MonitorDB(
        name=name,
        url=url,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
        expected_status_code=expected_status_code,
    )

    async with async_session_factory() as session:
        session.add(monitor_db)

        try:
            await session.commit()
            await session.refresh(monitor_db)
        except Exception:
            await session.rollback()
            raise

    return _monitor_to_domain(monitor_db)


async def get_active_monitors() -> list[Monitor]:
    statement = (
        select(MonitorDB)
        .where(MonitorDB.is_active.is_(True))
        .order_by(MonitorDB.id)
    )

    async with async_session_factory() as session:
        query_result = await session.execute(statement)
        monitor_rows = query_result.scalars().all()

    return [
        _monitor_to_domain(monitor_db)
        for monitor_db in monitor_rows
    ]


async def get_active_monitor(monitor_id: int) -> Monitor | None:
    """Return one active monitor for a worker, if it still exists."""
    statement = select(MonitorDB).where(
        MonitorDB.id == monitor_id,
        MonitorDB.is_active.is_(True),
    )

    async with async_session_factory() as session:
        result = await session.execute(statement)
        monitor_db = result.scalar_one_or_none()

    if monitor_db is None:
        return None

    return _monitor_to_domain(monitor_db)


async def save_check_result(
    monitor_id: int,
    check_result: CheckResult,
) -> None:
    result_db = CheckResultDB(
        monitor_id=monitor_id,
        checked_at=check_result.checked_at,
        status_code=check_result.status_code,
        latency_ms=check_result.latency_ms,
        success=check_result.success,
        error=check_result.error,
    )

    async with async_session_factory() as session:
        session.add(result_db)

        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_check_results(
    monitor_id: int,
    limit: int = 100,
) -> list[CheckResult]:
    if limit <= 0:
        raise ValueError("limit must be positive")

    statement = (
        select(CheckResultDB)
        .where(CheckResultDB.monitor_id == monitor_id)
        .order_by(
            CheckResultDB.checked_at.desc(),
            CheckResultDB.id.desc(),
        )
        .limit(limit)
    )

    async with async_session_factory() as session:
        query_result = await session.execute(statement)
        result_rows = query_result.scalars().all()

    return [
        _check_result_to_domain(result_db)
        for result_db in result_rows
    ]


async def get_active_incident(monitor_id: int) -> IncidentDB | None:
    """Return the currently open incident for one monitor, if present."""
    statement = select(IncidentDB).where(
        IncidentDB.monitor_id == monitor_id,
        IncidentDB.status == "OPEN",
    )

    async with async_session_factory() as session:
        result = await session.execute(statement)
        return result.scalar_one_or_none()


async def get_incidents() -> list[IncidentDB]:
    """Return all incidents across all monitors, newest first."""
    statement = select(IncidentDB).order_by(
        IncidentDB.started_at.desc(),
        IncidentDB.id.desc(),
    )

    async with async_session_factory() as session:
        result = await session.execute(statement)
        return list(result.scalars().all())


async def get_incident(incident_id: int) -> IncidentDB | None:
    """Return one incident by its primary key, if it exists."""
    async with async_session_factory() as session:
        return await session.get(IncidentDB, incident_id)


async def get_incidents_for_monitor(
    monitor_id: int,
) -> list[IncidentDB]:
    """Return one monitor's complete incident history, newest first."""
    statement = (
        select(IncidentDB)
        .where(IncidentDB.monitor_id == monitor_id)
        .order_by(
            IncidentDB.started_at.desc(),
            IncidentDB.id.desc(),
        )
    )

    async with async_session_factory() as session:
        result = await session.execute(statement)
        return list(result.scalars().all())


async def get_open_incidents() -> list[IncidentDB]:
    """Return all currently open incidents, newest first."""
    statement = (
        select(IncidentDB)
        .where(IncidentDB.status == "OPEN")
        .order_by(IncidentDB.started_at.desc())
    )

    async with async_session_factory() as session:
        result = await session.execute(statement)
        return list(result.scalars().all())


async def create_incident(
    monitor_id: int,
    started_at: datetime,
    last_error: str | None = None,
) -> IncidentDB:
    incident_db = IncidentDB(
        monitor_id=monitor_id,
        started_at=started_at,
        last_failure_at=started_at,
        resolved_at=None,
        status="OPEN",
        failure_count=1,
        last_error=last_error,
    )

    async with async_session_factory() as session:
        session.add(incident_db)

        try:
            await session.commit()
            await session.refresh(incident_db)
        except Exception:
            await session.rollback()
            raise

    return incident_db


async def resolve_incident(
    monitor_id: int,
    resolved_at: datetime,
) -> IncidentDB | None:
    statement = select(IncidentDB).where(
        IncidentDB.monitor_id == monitor_id,
        IncidentDB.status == "OPEN",
    )

    async with async_session_factory() as session:
        result = await session.execute(statement)
        incident = result.scalar_one_or_none()

        if incident is None:
            return None

        incident.status = "RESOLVED"
        incident.resolved_at = resolved_at

        try:
            await session.commit()
            await session.refresh(incident)
        except Exception:
            await session.rollback()
            raise

    return incident


async def increment_incident(
    incident_id: int,
    last_error: str,
    *,
    last_failure_at: datetime | None = None,
) -> IncidentDB | None:
    statement = (
        select(IncidentDB)
        .where(
            IncidentDB.id == incident_id,
            IncidentDB.status == "OPEN",
        )
        .with_for_update()
    )

    async with async_session_factory() as session:
        result = await session.execute(statement)
        incident = result.scalar_one_or_none()

        if incident is None:
            return None

        incident.failure_count += 1
        incident.last_error = last_error
        incident.last_failure_at = (
            last_failure_at
            if last_failure_at is not None
            else datetime.now(timezone.utc)
        )

        try:
            await session.commit()
            await session.refresh(incident)
        except Exception:
            await session.rollback()
            raise

    return incident


async def update_incident(
    incident_id: int,
    changes: dict[str, object],
) -> IncidentDB | None:
    allowed_fields = {
        "last_error",
        "last_failure_at",
        "status",
        "resolved_at",
    }

    if not changes:
        raise ValueError("No incident fields were reported")

    invalid_fields = set(changes) - allowed_fields

    if invalid_fields:
        invalid_names = ", ".join(sorted(invalid_fields))
        raise ValueError(
            f"These incident fields cannot be updated: {invalid_names}"
        )

    if "status" in changes:
        status = changes["status"]

        if not isinstance(status, str) or status not in {
            "OPEN",
            "RESOLVED",
        }:
            raise ValueError("status must be OPEN or RESOLVED")

    if "last_error" in changes:
        last_error = changes["last_error"]

        if last_error is not None and not isinstance(last_error, str):
            raise ValueError("last_error must be a string or None")

    if "last_failure_at" in changes:
        last_failure_at = changes["last_failure_at"]

        if (
            not isinstance(last_failure_at, datetime)
            or last_failure_at.tzinfo is None
            or last_failure_at.utcoffset() is None
        ):
            raise ValueError(
                "last_failure_at must be a timezone-aware datetime"
            )

    if "resolved_at" in changes:
        resolved_at = changes["resolved_at"]

        if resolved_at is not None and (
            not isinstance(resolved_at, datetime)
            or resolved_at.tzinfo is None
            or resolved_at.utcoffset() is None
        ):
            raise ValueError(
                "resolved_at must be a timezone-aware datetime or None"
            )

    async with async_session_factory() as session:
        incident = await session.get(
            IncidentDB,
            incident_id,
            with_for_update=True,
        )

        if incident is None:
            return None

        was_resolved = incident.status == "RESOLVED"

        try:
            for field_name, new_value in changes.items():
                setattr(incident, field_name, new_value)

            if was_resolved and incident.status == "OPEN":
                raise ValueError(
                    "A resolved incident cannot be reopened; "
                    "create a new incident instead"
                )

            if incident.status == "OPEN" and incident.resolved_at is not None:
                raise ValueError("An OPEN incident cannot have resolved_at")

            if incident.status == "RESOLVED" and incident.resolved_at is None:
                raise ValueError("A RESOLVED incident requires resolved_at")

            if incident.last_failure_at < incident.started_at:
                raise ValueError(
                    "last_failure_at cannot be before started_at"
                )

            if (
                incident.resolved_at is not None
                and incident.resolved_at < incident.last_failure_at
            ):
                raise ValueError(
                    "resolved_at cannot be before last_failure_at"
                )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

        # Refresh after a successful commit. A refresh failure cannot undo
        # an update that PostgreSQL has already committed.
        await session.refresh(incident)

    return incident
