# Relay

**A distributed background job processing platform built with Python.**

Relay is a backend system designed to accept, persist, queue, and execute background jobs independently of the API layer.

The goal is to build a reliable job execution platform with persistent job tracking, independent workers, retries, and support for both conventional software tasks and AI-powered workloads.

> **Status:** Active development — building the MVP.

## Why Relay?

Many backend operations should not block an API request. Tasks such as sending emails, processing files, generating reports, and running AI workflows can take time and need reliable execution.

Relay aims to provide a system where applications can submit jobs through an API while independent workers handle execution in the background.

## Architecture

```text
                 Client
                   |
                   v
              FastAPI API
                   |
                   v
              Job Service
                   |
                   v
             Job Repository
                   |
                   v
              PostgreSQL
                   |
                   v
              Redis Queue
                   |
                   v
            Celery Workers
                   |
                   v
           Job Status Updates
```

*The architecture represents the intended system. Background worker integration is still under development.*

## Current Features

- REST API built with FastAPI.
- Job submission with Pydantic validation.
- UUID-based job identification.
- PostgreSQL persistence using SQLAlchemy.
- JSONB payload storage.
- Job priority and status fields.
- Database schema migrations with Alembic.
- Docker Compose development environment.
- Initial separation of API, service, repository, schema, and database layers.

### API Endpoints

| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| POST | `/api/v1/jobs` | Submit a job | Implemented |
| GET | `/api/v1/jobs/{job_id}` | Retrieve a job | Implemented; HTTP verification pending |
| GET | `/api/v1/jobs` | List jobs | Planned |
| DELETE | `/api/v1/jobs/{job_id}` | Cancel a job | Planned |

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core language |
| FastAPI | REST API |
| Pydantic | Data validation and serialization |
| SQLAlchemy | ORM and database access |
| PostgreSQL | Persistent job storage |
| Alembic | Database migrations |
| Redis | Message broker (integration planned) |
| Celery | Background task execution (integration planned) |
| Docker Compose | Local infrastructure |
| Pytest | Testing |

## Project Structure

```text
relay/
├── alembic/
│   └── versions/
├── src/
│   └── relay/
│       ├── api/
│       │   └── routes/
│       ├── database/
│       ├── models/
│       ├── repositories/
│       ├── schemas/
│       ├── services/
│       └── main.py
├── docker-compose.yml
├── alembic.ini
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12+
- Docker Desktop with Docker Compose
- Git

### 1. Clone the repository

```bash
git clone https://github.com/uves18/Relay.git
cd relay
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy "psycopg[binary]" alembic python-dotenv
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Set your PostgreSQL credentials and database URL in `.env`.

### 5. Start infrastructure

```bash
docker compose up -d
```

### 6. Apply database migrations

```bash
PYTHONPATH=src alembic upgrade head
```

### 7. Start the API

```bash
PYTHONPATH=src python -m uvicorn relay.main:app --reload
```

### 8. Explore the API

Open:

`http://127.0.0.1:8000/docs`

## Job Lifecycle

The intended job lifecycle is:

```text
pending → queued → running → completed
                              |
                              v
                            failed
```

Additional states and retry transitions will be introduced as worker execution is implemented.

## Development Roadmap

- [x] FastAPI application foundation
- [x] Docker Compose infrastructure
- [x] PostgreSQL connectivity
- [x] SQLAlchemy job model
- [x] Alembic migrations
- [x] Database-backed job submission
- [x] Job retrieval implementation
- [ ] Complete API verification and automated tests
- [ ] Job listing and pagination
- [ ] Job cancellation
- [ ] Redis and Celery integration
- [ ] Independent background workers
- [ ] Retry and failure handling
- [ ] Observability and production deployment
- [ ] AI-powered job execution

## Engineering Principles

Relay is being developed with an emphasis on:

- Separation of concerns.
- Persistent state and reliable execution.
- Explicit API contracts.
- Database migration discipline.
- Independent worker processes.
- Testability and maintainability.
- Production-oriented engineering practices.

## License

To be decided.