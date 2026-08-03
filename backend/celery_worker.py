"""
Celery worker configuration.
Broker: Redis. Result backend: Redis (separate DB index).
"""

from celery import Celery
import os

BROKER_URL  = os.getenv("CELERY_BROKER_URL",  "redis://localhost:6379/0")
RESULT_URL  = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "ecometric",
    broker=BROKER_URL,
    backend=RESULT_URL,
    include=[
        "tasks.lca_compute",   # LCA matrix computation jobs (Phase 4)
        "tasks.lca_compute_v2",# Full LCA calculation jobs (current API path)
        "tasks.pdf_generate",  # WeasyPrint PDF generation jobs (Phase 5)
        "tasks.nlp_tasks",     # Active learning weight calibration
    ],
)

from celery.schedules import crontab

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry failed tasks up to 3 times with exponential backoff
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_max_retries=3,
    # Task time limits
    task_soft_time_limit=90,   # Soft: raise SoftTimeLimitExceeded
    task_time_limit=120,       # Hard: kill task
)

celery_app.conf.beat_schedule = {
    "weekly-nlp-calibration": {
        "task": "tasks.nlp_tasks.calibrate_nlp_weights_job",
        "schedule": crontab(minute=0, hour=0, day_of_week="sunday"),
    }
}

