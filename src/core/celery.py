from celery import Celery
from celery.schedules import crontab
from core.settings import config
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

celery_app = Celery(
    'bitpin_articles'
)
celery_app.conf.beat_schedule = {
    'probable-spam-ratings': {
        'task': 'articles.tasks.handle_probable_spam_ratings',
        'schedule': crontab(minute=f'*/{config.SPAM_DETECTION_TASK_PERIOD_TIME}'),
    },
}
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()
celery_app.conf.broker_connection_retry_on_startup = True
