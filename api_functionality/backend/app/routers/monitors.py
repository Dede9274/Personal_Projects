"""HTTP endpoints for monitor management."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session
from app.database.models import MonitorDB
from app.schemas.monitor import MonitorCreate, MonitorRead, MonitorUpdate
from app.services import monitor_service


router = APIRouter(
    prefix="/monitors",
    tags=["monitors"],
)

SessionDependency = Annotated[
    AsyncSession,
    Depends(get_session),
]
MonitorId = Annotated[
    int,
    Path(gt=0),
]


@router.post(
    "",
    response_model=MonitorRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_monitor(
    data: MonitorCreate,
    session: SessionDependency,
) -> MonitorDB:
    return await monitor_service.create_monitor(session, data)


@router.get(
    "",
    response_model=list[MonitorRead],
)
async def list_monitors(
    session: SessionDependency,
) -> list[MonitorDB]:
    return await monitor_service.list_monitors(session)


@router.get(
    "/{monitor_id}",
    response_model=MonitorRead,
)
async def get_monitor(
    monitor_id: MonitorId,
    session: SessionDependency,
) -> MonitorDB:
    monitor = await monitor_service.get_monitor(session, monitor_id)

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitor {monitor_id} was not found",
        )

    return monitor


@router.patch(
    "/{monitor_id}",
    response_model=MonitorRead,
)
async def update_monitor(
    monitor_id: MonitorId,
    data: MonitorUpdate,
    session: SessionDependency,
) -> MonitorDB:
    monitor = await monitor_service.update_monitor(
        session,
        monitor_id,
        data,
    )

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitor {monitor_id} was not found",
        )

    return monitor


@router.delete(
    "/{monitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_monitor(
    monitor_id: MonitorId,
    session: SessionDependency,
) -> Response:
    deleted = await monitor_service.delete_monitor(session, monitor_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitor {monitor_id} was not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
