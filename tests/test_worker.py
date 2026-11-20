from relay.database.session import SessionLocal
from relay.models.job import Job
from relay.tasks import execute_job
from relay.worker import celery_app


def create_job(task_type: str, payload: dict, max_retries: int = 0) -> Job:
    db = SessionLocal()
    job = Job(
        task_type=task_type,
        payload=payload,
        priority=1,
        status="queued",
        max_retries=max_retries,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    db.close()
    return job


def test_successful_task_completion():
    job = create_job("demo.add", {"left": 4, "right": 6})
    execute_job.run(str(job.id))

    db = SessionLocal()
    updated = db.get(Job, job.id)
    assert updated.status == "completed"
    assert updated.result == {"sum": 10}
    assert updated.attempts == 1
    assert updated.started_at is not None
    assert updated.completed_at is not None
    db.close()


def test_unknown_task_fails_without_retry():
    job = create_job("demo.missing", {}, max_retries=0)
    execute_job.run(str(job.id))

    db = SessionLocal()
    updated = db.get(Job, job.id)
    assert updated.status == "failed"
    assert updated.attempts == 1
    assert "Unknown task type" in updated.error
    assert updated.completed_at is not None
    db.close()


def test_task_schedules_a_bounded_retry(monkeypatch):
    job = create_job("demo.missing", {}, max_retries=2)
    sent = []
    monkeypatch.setattr(
        celery_app,
        "send_task",
        lambda name, **kwargs: sent.append((name, kwargs)),
    )

    execute_job.run(str(job.id))

    db = SessionLocal()
    updated = db.get(Job, job.id)
    assert updated.status == "retry_scheduled"
    assert updated.attempts == 1
    assert "Unknown task type" in updated.error
    db.close()
    assert sent[0][0] == "relay.tasks.execute_job"
