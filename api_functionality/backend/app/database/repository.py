from sqlalchemy import select

from app.database.connection import async_session_factory
from app.database.models import CheckResultDB, MonitorDB
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
        .order_by(CheckResultDB.checked_at.desc())
        .limit(limit)
    )

    async with async_session_factory() as session:
        query_result = await session.execute(statement)
        result_rows = query_result.scalars().all()

    return [
        _check_result_to_domain(result_db)
        for result_db in result_rows
    ]
