
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    """Request schema for submitting a new job."""

    task_type: str = Field(min_length=1)
    payload: dict[str, Any]
    priority: int = Field(default=1, ge=1, le=10)
    max_retries: int = Field(default=3, ge=0, le=10)


class JobResponse(BaseModel):
    """Response schema returned after a job is accepted."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_type: str
    payload: dict[str, Any]
    priority: int
    status: str
    created_at: datetime
    result: dict[str, Any] | None = None
    error: str | None = None
    attempts: int = 0
    max_retries: int = 3
    started_at: datetime | None = None
    completed_at: datetime | None = None
