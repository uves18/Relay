"""add job execution fields

Revision ID: 4b2a1c7d9e31
Revises: ff4e3b666b39
Create Date: 2026-11-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "4b2a1c7d9e31"
down_revision = "ff4e3b666b39"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("result", postgresql.JSONB(), nullable=True))
    op.add_column("jobs", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("jobs", sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("jobs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("celery_task_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_jobs_celery_task_id", "jobs", ["celery_task_id"])


def downgrade() -> None:
    op.drop_constraint("uq_jobs_celery_task_id", "jobs", type_="unique")
    op.drop_column("jobs", "celery_task_id")
    op.drop_column("jobs", "completed_at")
    op.drop_column("jobs", "started_at")
    op.drop_column("jobs", "max_retries")
    op.drop_column("jobs", "attempts")
    op.drop_column("jobs", "error")
    op.drop_column("jobs", "result")
