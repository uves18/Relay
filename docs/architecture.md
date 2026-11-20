# Relay Architecture

## Responsibilities

- **FastAPI** validates HTTP requests and exposes the job API. It persists submissions and
  publishes Celery messages, but it does not execute task handlers.
- **PostgreSQL** is the source of truth for job lifecycle, payload, result, error, attempts,
  timestamps, and cancellation state.
- **Redis** is the Celery message broker. It transports task messages; it is not an application
  database and is not authoritative for job state.
- **Celery workers** consume registered tasks, execute one allowlisted Python handler, and
  update PostgreSQL independently of the API process.

## Submission flow

1. The API validates a `JobCreate` request.
2. The job repository commits a `pending` job to PostgreSQL.
3. The service publishes `relay.tasks.execute_job` with the job UUID.
4. A successful publication changes the job to `queued`.
5. A publication error changes the job to `failed` and returns HTTP 503.

Database commits and broker publication are not atomic. An operator should recover from
edge cases caused by crashes between these operations by using a future durable outbox.

## Execution flow

The worker increments `attempts`, sets `running`, executes an allowlisted handler, and stores
either `completed` with JSONB `result` or `failed` with an error. Ordinary exceptions that
remain within `max_retries` set `retry_scheduled` and create a delayed Celery task.

## Cancellation

Queued, pending, and retry-scheduled jobs may be marked `cancelled` and revoked by Celery task
ID. Running jobs return HTTP 409 because Relay cannot safely guarantee termination of arbitrary
Python work. Terminal jobs return HTTP 409.
