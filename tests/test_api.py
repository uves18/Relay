from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from relay.database.session import SessionLocal, get_db
from relay.main import app
from relay.models.job import Job
from relay.services import job_service


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    original_send_task = job_service.celery_app.send_task
    job_service.celery_app.send_task = lambda *args, **kwargs: None
    with TestClient(app) as test_client:
        yield test_client
    job_service.celery_app.send_task = original_send_task
    app.dependency_overrides.clear()


def test_submit_and_retrieve_job(client):
    submitted = client.post(
        "/api/v1/jobs",
        json={"task_type": "demo.echo", "payload": {"value": 7}, "priority": 3},
    )
    assert submitted.status_code == 201
    body = submitted.json()
    assert body["status"] == "queued"
    assert body["attempts"] == 0
    assert body["max_retries"] == 3

    retrieved = client.get(f"/api/v1/jobs/{body['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["payload"] == {"value": 7}


def test_invalid_submission(client):
    response = client.post(
        "/api/v1/jobs",
        json={"task_type": "", "payload": {}, "priority": 20},
    )
    assert response.status_code == 422


def test_unknown_and_invalid_uuid(client):
    assert client.get(f"/api/v1/jobs/{uuid4()}").status_code == 404
    assert client.get("/api/v1/jobs/not-a-uuid").status_code == 422


def test_list_pagination_and_status_filter(client):
    for value in range(3):
        response = client.post(
            "/api/v1/jobs",
            json={"task_type": "demo.add", "payload": {"left": value, "right": 1}},
        )
        assert response.status_code == 201

    listed = client.get("/api/v1/jobs?limit=2&offset=0")
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    filtered = client.get("/api/v1/jobs?status=queued")
    assert filtered.status_code == 200
    assert all(job["status"] == "queued" for job in filtered.json())


def test_cancel_queued_job(client):
    submitted = client.post(
        "/api/v1/jobs",
        json={"task_type": "demo.echo", "payload": {}},
    )
    job_id = submitted.json()["id"]
    cancelled = client.delete(f"/api/v1/jobs/{job_id}")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["completed_at"] is not None
