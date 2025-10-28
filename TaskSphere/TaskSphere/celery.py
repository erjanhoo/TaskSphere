from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.broker_connection_retry_on_startup = True

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-expired-temporary-users': {
        'task': 'user.tasks.cleanup_expired_temporary_users',
        'schedule': crontab(minute='0', hour='*/2'),  # Run every 2 hours
    },
}
