import logging
import os
from datetime import datetime, timezone
from uuid import UUID
from typing import Sequence

from celery import Celery

from relay.repositories.job_repository import JobRepository
from relay.schemas.job import JobCreate
from relay.models.job import Job

logger = logging.getLogger(__name__)

BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

celery_app = Celery("relay", broker=BROKER_URL)


class JobService:
    def __init__(
        self,
        repository: JobRepository | None = None,
        publisher: Celery | None = None,
    ) -> None:
        self.repository = repository or JobRepository()
        self.publisher = publisher or celery_app

    def submit_job(self, job_data: JobCreate, db) -> Job:
        """Persist a job, then publish it to the broker."""
        job = self.repository.create(db, job_data)
        task_id = str(job.id)
        try:
            self.publisher.send_task(
                "relay.tasks.execute_job",
                args=[task_id],
                task_id=task_id,
                priority=job.priority,
            )
            job.celery_task_id = task_id
            job.status = "queued"
            db.commit()
            db.refresh(job)
            return job
        except Exception as exc:
            logger.exception("Failed to queue job %s", job.id)
            job.status = "failed"
            job.error = f"Queue publication failed: {exc}"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(job)
            raise QueuePublicationError(job) from exc

    def get_job(self, job_id: UUID, db) -> Job:
        """Retrieve a job by UUID; raise ValueError if not found."""
        job = self.repository.get_by_id(db, job_id)
        if job is None:
            raise ValueError(f"Job with id {job_id} not found")
        return job

    def list_jobs(
        self,
        db,
        *,
        offset: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> Sequence[Job]:
        return self.repository.list(db, offset=offset, limit=limit, status=status)

    def cancel_job(self, job_id: UUID, db) -> Job:
        job = self.repository.get_by_id(db, job_id)
        if job is None:
            raise ValueError(f"Job with id {job_id} not found")
        if job.status == "running":
            raise CancellationNotAllowed("A running job cannot be safely cancelled")
        if job.status in {"completed", "failed", "cancelled"}:
            raise CancellationNotAllowed(f"Job is already {job.status}")
        if job.celery_task_id:
            self.publisher.control.revoke(job.celery_task_id, terminate=False)
        return self.repository.update_status(db, job, status="cancelled", completed=True)


class QueuePublicationError(Exception):
    def __init__(self, job: Job) -> None:
        super().__init__(f"Job {job.id} was persisted but could not be queued")
        self.job = job


class CancellationNotAllowed(Exception):
    pass
