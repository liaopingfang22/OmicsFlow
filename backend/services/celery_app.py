"""
Celery application for OmicsFlow task queue.
Migrates from asyncio to production-grade distributed task execution.
"""
from celery import Celery
from config import get_settings

settings = get_settings()

celery_app = Celery(
    "omicsflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=172800,
    task_time_limit=180000,
    task_default_queue="omicsflow_default",
    task_routes={
        "services.celery_tasks.run_pipeline": {"queue": "omicsflow_pipelines"},
        "services.celery_tasks.run_pipeline_gpu": {"queue": "omicsflow_gpu"},
    },
    beat_schedule={
        "cleanup-old-downloads": {
            "task": "services.celery_tasks.cleanup_downloads",
            "schedule": 86400.0,
        },
        "health-check": {
            "task": "services.celery_tasks.health_check",
            "schedule": 300.0,
        },
    },
)
