from typing import Optional, Sequence
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import desc, select

from sqlalchemy.orm import Session

from relay.models.job import Job
from relay.schemas.job import JobCreate


class JobRepository:
    def create(self, db: Session, job_data: JobCreate) -> Job:
        """Persist a new job and return the saved row."""
        job = Job(
            task_type=job_data.task_type,
            payload=job_data.payload,
            priority=job_data.priority,
            max_retries=job_data.max_retries,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job

    def get_by_id(self, db: Session, job_id: UUID) -> Optional[Job]:
        """Retrieve a job by its UUID, returning None if not found."""
        return db.query(Job).filter(Job.id == job_id).first()

    def list(
        self,
        db: Session,
        *,
        offset: int,
        limit: int,
        status: str | None = None,
    ) -> Sequence[Job]:
        statement = select(Job)
        if status:
            statement = statement.where(Job.status == status)
        statement = statement.order_by(desc(Job.created_at), desc(Job.id)).offset(offset).limit(limit)
        return db.scalars(statement).all()

    def update_status(
        self,
        db: Session,
        job: Job,
        *,
        status: str,
        result: dict | None = None,
        error: str | None = None,
        started: bool = False,
        completed: bool = False,
    ) -> Job:
        job.status = status
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        if started:
            job.started_at = datetime.now(timezone.utc)
        if completed:
            job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job