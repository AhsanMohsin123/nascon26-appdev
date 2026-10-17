from celery import Celery
from app.config import settings

celery_app = Celery("nascon26", broker=settings.redis_url)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
