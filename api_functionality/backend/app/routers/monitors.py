"""HTTP endpoints for monitor management."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session
from app.database.models import CheckResultDB, MonitorDB
from app.queue.producer import enqueue_monitor_check
from app.schemas.check_result import (
    CheckEnqueueResponse,
    CheckEnqueueStatus,
    CheckResultResponse,
)
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
CheckResultLimit = Annotated[
    int,
    Query(ge=1, le=500),
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


@router.get(
    "/{monitor_id}/checks",
    response_model=list[CheckResultResponse],
)
async def list_monitor_checks(
    monitor_id: MonitorId,
    session: SessionDependency,
    limit: CheckResultLimit = 500,
) -> list[CheckResultDB]:
    """Return the latest persisted checks for one monitor."""
    checks = await monitor_service.list_monitor_checks(
        session,
        monitor_id,
        limit,
    )

    if checks is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitor {monitor_id} was not found",
        )

    return checks


@router.post(
    "/{monitor_id}/checks",
    response_model=CheckEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_200_OK: {
            "model": CheckEnqueueResponse,
            "description": "A check for this monitor is already outstanding.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "The monitor is inactive.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "The monitor-check queue is unavailable.",
        },
    },
)
async def run_monitor_check(
    monitor_id: MonitorId,
    session: SessionDependency,
    response: Response,
) -> CheckEnqueueResponse:
    """Queue an extra check without changing the scheduler's cadence."""
    monitor = await monitor_service.get_monitor(session, monitor_id)

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitor {monitor_id} was not found",
        )

    if not monitor.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Monitor {monitor_id} is inactive",
        )

    try:
        job_id = await enqueue_monitor_check(monitor_id)
    except RedisError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The monitor-check queue is unavailable",
        ) from error

    if job_id is None:
        response.status_code = status.HTTP_200_OK
        return CheckEnqueueResponse(
            monitor_id=monitor_id,
            status=CheckEnqueueStatus.ALREADY_OUTSTANDING,
            job_id=None,
        )

    return CheckEnqueueResponse(
        monitor_id=monitor_id,
        status=CheckEnqueueStatus.QUEUED,
        job_id=job_id,
    )


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
