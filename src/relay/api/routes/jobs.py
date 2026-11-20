from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID

from relay.database.session import get_db
from relay.schemas.job import JobCreate, JobResponse
from relay.services.job_service import (
    CancellationNotAllowed,
    JobService,
    QueuePublicationError,
)

router = APIRouter()


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_job(job: JobCreate, db=Depends(get_db)) -> JobResponse:
    """Persist a job and queue it for independent worker execution."""
    service = JobService()
    try:
        return service.submit_job(job, db)
    except QueuePublicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Job {exc.job.id} was persisted but could not be queued",
        ) from exc


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
)
def get_job(job_id: UUID, db=Depends(get_db)) -> JobResponse:
    """Retrieve an existing job by its UUID."""
    service = JobService()
    try:
        job = service.get_job(job_id, db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    return job


@router.get(
    "/jobs",
    response_model=list[JobResponse],
)
def list_jobs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status_filter: str | None = Query(default=None, alias="status"),
    db=Depends(get_db),
) -> list[JobResponse]:
    allowed = {"pending", "queued", "running", "retry_scheduled", "completed", "failed", "cancelled"}
    if status_filter is not None and status_filter not in allowed:
        raise HTTPException(status_code=422, detail="Unknown job status")
    return list(JobService().list_jobs(db, offset=offset, limit=limit, status=status_filter))


@router.delete(
    "/jobs/{job_id}",
    response_model=JobResponse,
)
def cancel_job(job_id: UUID, db=Depends(get_db)) -> JobResponse:
    service = JobService()
    try:
        return service.cancel_job(job_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CancellationNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
