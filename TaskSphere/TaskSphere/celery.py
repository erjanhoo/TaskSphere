from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TaskSphere.settings')

app = Celery('TaskSphere')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.broker_connection_retry_on_startup = True

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-expired-temporary-users': {
        'task': 'user.tasks.cleanup_expired_temporary_users',
        'schedule': crontab(minute='0', hour='*/2'),  # Run every 2 hours
    },
    'create_new_tasks_with_recurrance_rule':{
        'task':'task.tasks.create_task_with_recurrence_rule',
        'schedule':crontab(hour=0, minute=0)
    },
    'send_reminder_email':{
        'task':'task.tasks.send_reminder_email',
        'schedule':crontab(minute='*/3')
    },
    'check_tasks_expiration': {
        'task': 'task.tasks.check_tasks_expiration',
        'schedule':crontab(minute='*/10')

    },
    'delete_old_expired_tasks':{
        'task':'task.tasks.delete_old_expired_tasks',
        'schedule':crontab(hour=0, minute=0, day_of_month=1)
    },
    'send_amount_of_users_tasks_for_today':{
        'task':'task.tasks.send_amount_of_tasks_for_today',
        'schedule':crontab(hour=8, minute=0)
    },
    'send_amount_of_users_left_tasks_for_today':{
        'task':'task.tasks.send_amount_of_tasks_left_for_today',
        'schedule':crontab(hour=18, minute=0)
    },
    'send_weekly_reports':{
        'task':'task.tasks.send_weekly_reports',
        'schedule':crontab(day_of_week='sunday', hour=0, minute=0)
    },
    'calculate_user_streak':{
        'task':'task.tasks.calculate_user_streak',
        'schedule':crontab(hour=0, minute=0)
    }
}
