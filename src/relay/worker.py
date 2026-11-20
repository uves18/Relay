import os

from celery import Celery


BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

celery_app = Celery(
    "relay",
    broker=BROKER_URL,
    include=["relay.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    enable_utc=True,
)
