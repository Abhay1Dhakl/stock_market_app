from celery import Celery

from app.core.config import settings

celery_app = Celery("stock_market_app")
celery_app.conf.broker_url = settings.redis_url
celery_app.conf.result_backend = settings.redis_url
celery_app.autodiscover_tasks(["app.tasks"])

