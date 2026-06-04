from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "skilltree",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.test_task",
        "app.tasks.embedding_tasks"
    ]
)