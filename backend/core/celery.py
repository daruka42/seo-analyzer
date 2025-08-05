from celery import Celery
from core.config import settings

# Create Celery instance
celery_app = Celery(
    "seo_analyzer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.crawler", "tasks.analyzer"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.crawler.*": {"queue": "crawler"},
        "tasks.analyzer.*": {"queue": "analyzer"},
    },
)

if __name__ == "__main__":
    celery_app.start()
