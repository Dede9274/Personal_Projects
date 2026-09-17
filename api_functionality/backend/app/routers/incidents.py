"""HTTP endpoints for reading and managing incidents."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from app.database import repository
from app.database.models import IncidentDB
from app.models.incident import IncidentTransitionError
from app.schemas.incident import IncidentResponse, IncidentStatusUpdate


router = APIRouter(tags=["incidents"])

IncidentId = Annotated[int, Path(gt=0)]
MonitorId = Annotated[int, Path(gt=0)]


@router.get(
    "/incidents",
    response_model=list[IncidentResponse],
)
async def list_incidents() -> list[IncidentDB]:
    """Return current and historical incidents for every monitor."""
    return await repository.get_incidents()


# This static route must be declared before /incidents/{incident_id} so that
# FastAPI does not try to interpret the word "open" as an integer ID.
@router.get(
    "/incidents/open",
    response_model=list[IncidentResponse],
)
async def list_open_incidents() -> list[IncidentDB]:
    """Return all incidents that have not yet been resolved."""
    return await repository.get_open_incidents()


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
async def get_incident(incident_id: IncidentId) -> IncidentDB:
    """Return one incident using the incident's ID."""
    incident = await repository.get_incident(incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} was not found",
        )

    return incident


@router.patch(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
async def update_incident_status(
    incident_id: IncidentId,
    data: IncidentStatusUpdate,
) -> IncidentDB:
    """Persist a valid manual incident status transition."""
    try:
        incident = await repository.transition_incident_status(
            incident_id,
            data.status,
        )
    except IncidentTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} was not found",
        )

    return incident


@router.get(
    "/monitors/{monitor_id}/incidents",
    response_model=list[IncidentResponse],
)
async def list_monitor_incidents(
    monitor_id: MonitorId,
) -> list[IncidentDB]:
    """Return the complete incident history for one monitor."""
    return await repository.get_incidents_for_monitor(monitor_id)
