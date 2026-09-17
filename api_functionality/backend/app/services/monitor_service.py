#Business and database operations for monitor management.
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import CheckResultDB, MonitorDB
from app.schemas.monitor import MonitorCreate, MonitorUpdate


async def _save_monitor(session: AsyncSession, monitor: MonitorDB) -> None:
    try:
        await session.flush() #use flush instead of commit because it doesn't make changes permanent like commit() and can also be rolled back
        await session.refresh(monitor)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
 
async def create_monitor(session: AsyncSession, data: MonitorCreate) ->MonitorDB:
    values = data.model_dump() #converts pudantic model object to a python dictionary
    values["url"] = str(data.url)

    monitor = MonitorDB(**values) # ** -> dictionary unpacking
    session.add(monitor)
    await _save_monitor(session, monitor)
    return monitor

async def list_monitors(session: AsyncSession,) -> list[MonitorDB]:
    statement = select(MonitorDB).order_by(MonitorDB.id)

    result = await session.scalars(statement)
    return list(result.all())

async def get_monitor(session: AsyncSession, monitor_id: int,) -> MonitorDB | None:
    return await session.get(MonitorDB, monitor_id)


async def list_monitor_checks(
    session: AsyncSession,
    monitor_id: int,
    limit: int,
) -> list[CheckResultDB] | None:
    """Return one monitor's latest checks, or None if it does not exist."""
    monitor = await get_monitor(session, monitor_id)

    if monitor is None:
        return None

    statement = (
        select(CheckResultDB)
        .where(CheckResultDB.monitor_id == monitor_id)
        .order_by(
            CheckResultDB.checked_at.desc(),
            CheckResultDB.id.desc(),
        )
        .limit(limit)
    )

    result = await session.scalars(statement)
    return list(result.all())


async def update_monitor(session: AsyncSession, monitor_id: int, data: MonitorUpdate,) -> MonitorDB | None:
    monitor = await get_monitor(session, monitor_id)

    if monitor is None:
        return None

    changes = data.model_dump(exclude_unset=True)
    if "url" in changes:
        changes["url"] = str(changes["url"])

    for field_name, value in changes.items():
        setattr(monitor, field_name, value)

    await _save_monitor(session, monitor)
    return monitor

async def delete_monitor(session: AsyncSession, monitor_id:int) -> bool:
    monitor = await get_monitor(session, monitor_id)

    if monitor is None: 
        return None

    try:
        await session.delete(monitor)
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return True
