from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("stock_market_app")
celery_app.conf.broker_url = settings.redis_url
celery_app.conf.result_backend = settings.redis_url
celery_app.conf.beat_schedule = {
    "weekday-full-crawl": {
        "task": "crawl.schedule_full",
        "schedule": crontab(minute=15, hour=18, day_of_week="1-5"),
    }
}
celery_app.autodiscover_tasks(["app.tasks"])
