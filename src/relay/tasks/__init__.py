import logging
import os
from datetime import datetime, timezone
from uuid import UUID

from relay.database.session import SessionLocal
from relay.models.job import Job
from relay.tasks.handlers import execute_registered_task
from relay.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="relay.tasks.execute_job", max_retries=0)
def execute_job(self, job_id: str) -> dict:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == UUID(job_id)).first()
        if job is None:
            raise ValueError(f"Job {job_id} not found")

        if job.status == "cancelled":
            return {"cancelled": True, "job_id": job_id}

        job.status = "running"
        job.started_at = job.started_at or datetime.now(timezone.utc)
        job.attempts += 1
        job.error = None
        db.commit()

        try:
            result = execute_registered_task(job.task_type, job.payload)
        except Exception as exc:
            db.rollback()
            job = db.query(Job).filter(Job.id == UUID(job_id)).first()
            if job is None:
                raise
            if job.attempts <= job.max_retries:
                delay = int(os.getenv("CELERY_RETRY_DELAY_SECONDS", "5"))
                job.status = "retry_scheduled"
                job.error = f"{type(exc).__name__}: {exc}"
                db.commit()
                logger.warning(
                    "Job %s failed on attempt %s; retry scheduled",
                    job_id,
                    job.attempts,
                )
                try:
                    celery_app.send_task(
                        "relay.tasks.execute_job",
                        args=[job_id],
                        task_id=job_id,
                        countdown=delay,
                        priority=job.priority,
                    )
                except Exception:
                    db.rollback()
                    job = db.query(Job).filter(Job.id == UUID(job_id)).first()
                    job.status = "failed"
                    job.error = f"{type(exc).__name__}: Retry could not be queued"
                    job.completed_at = datetime.now(timezone.utc)
                    db.commit()
                return {"retry_scheduled": True, "attempt": job.attempts}

            job.status = "failed"
            job.error = f"{type(exc).__name__}: {exc}"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error("Job %s failed after %s attempts", job_id, job.attempts)
            return {"failed": True, "attempt": job.attempts, "error": job.error}

        job.status = "completed"
        job.result = result
        job.error = None
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("Job %s completed on attempt %s", job_id, job.attempts)
        return result
    finally:
        db.close()
