# Relay

Relay is a distributed background job platform built with FastAPI, PostgreSQL, Redis, Celery,
and SQLAlchemy. It persists jobs, queues them through Redis, executes them in independent
workers, and exposes lifecycle state through a REST API.

## Architecture

```text
Client -> FastAPI -> Job Service -> PostgreSQL
                       |
                       +-> Redis/Celery -> Worker -> Task Handler
                                                    |
                                                    v
                                                PostgreSQL
```

PostgreSQL is the application-level source of truth. Redis is the message broker, not the
source of truth for job status.

## Features

- UUID job identification and Pydantic v2 validation
- PostgreSQL JSONB payloads and results
- Paginated job listing and status filtering
- Redis-backed Celery queue
- Independent API and worker processes
- Allowlisted demo tasks:
  - `demo.echo`
  - `demo.add`
  - `demo.process_text`
- Attempt counting, bounded retries, errors, and timestamps
- Honest cancellation behavior

## Job lifecycle

```text
pending -> queued -> running -> completed
                 |       |
                 |       +-> failed
                 |
                 +-> retry_scheduled -> running

pending/queued/retry_scheduled -> cancelled
```

`running` jobs cannot be reported as cancelled reliably. Calling `DELETE` for a running job
returns HTTP 409. See [architecture notes](docs/architecture.md).

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/jobs` | Persist and queue a job |
| `GET` | `/api/v1/jobs/{job_id}` | Retrieve a job |
| `GET` | `/api/v1/jobs?offset=0&limit=100&status=queued` | List or filter jobs |
| `DELETE` | `/api/v1/jobs/{job_id}` | Cancel a cancellable job |
| `GET` | `/health` | Health check |

## Project structure

```text
relay/
├── src/relay/
│   ├── api/routes/
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── tasks/
│   │   └── handlers.py
│   ├── worker.py
│   └── main.py
├── alembic/versions/
├── tests/
├── docs/architecture.md
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Local setup

Prerequisites: Python 3.12+, Docker with Compose, and Git.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
```

Start the API:

```bash
PYTHONPATH=src uvicorn relay.main:app --reload
```

Start a worker in a separate terminal:

```bash
PYTHONPATH=src celery -A relay.worker.celery_app worker --loglevel=info
```

Open `http://127.0.0.1:8000/docs`.

## Docker Compose

Copy `.env.example` to `.env`, change the development password, then run:

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, the FastAPI API, and a Celery worker. Stop services with:

```bash
docker compose down
```

The `relay_pgdata` named volume preserves PostgreSQL records. `docker compose down -v`
would remove that volume and is not used by the normal development workflow.

## Environment variables

| Variable | Purpose |
|---|---|
| `POSTGRES_USER` | PostgreSQL role |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL database |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL |
| `CELERY_BROKER_URL` | Redis broker URL |
| `CELERY_RETRY_DELAY_SECONDS` | Delay before a scheduled retry |

Inside Compose, hosts are `postgres` and `redis`; outside Compose, use `localhost`.
Never commit `.env` or real credentials.

## Example submission

```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "task_type": "demo.add",
    "payload": {"left": 19, "right": 23},
    "priority": 5,
    "max_retries": 2
  }'
```

Retrieve the returned UUID:

```bash
curl http://127.0.0.1:8000/api/v1/jobs/JOB_UUID
```

Successful response data includes `status: "completed"` and `result: {"sum": 42}`.

## Testing

```bash
./.venv/bin/pytest -q
```

The suite covers handlers, API validation, retrieval, pagination, cancellation, persistence,
success, unknown tasks, error storage, and retry scheduling.

For a real end-to-end check:

```bash
docker compose up --build
curl -X POST http://127.0.0.1:8000/api/v1/jobs \
  -H 'Content-Type: application/json' \
  -d '{"task_type":"demo.add","payload":{"left":19,"right":23},"max_retries":2}'
```

Use the returned UUID with `GET /api/v1/jobs/{job_id}` and wait briefly for the worker.

## Migrations

Apply migrations explicitly:

```bash
alembic upgrade head
```

Downgrade one migration:

```bash
alembic downgrade -1
```

Schema migrations preserve existing `jobs` data and do not drop the original table.

## Current limitations

- PostgreSQL commit and Redis publication are not atomic. Publication failure is handled by
  storing a failed state and returning HTTP 503, but crashes between commit and publish can
  leave a pending job.
- Retries are broker-scheduled, not a durable database outbox.
- Execution is at-least-once in the presence of crashes; duplicate side effects are possible.
- Cancellation is best-effort for queued messages and is refused for running jobs.
- Celery's internal result backend is not used; PostgreSQL is authoritative.

An outbox/relay table is the recommended future improvement for stronger submit guarantees.

## Future roadmap

- Durable outbox for database/broker consistency
- Dead-letter handling and queue observability
- Scheduled jobs
- Authentication and authorization
- Worker concurrency and resource controls
- AI-powered task integrations
