from celery import shared_task
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from .models import Task, SubTask
from user.models import MyUser
from user.services import award_karma_to_user

user = get_user_model()

@shared_task
def create_task_with_recurrence_rule():
    now=timezone.now()
    tasks = Task.objects.filter(
                                recurrence_rule__next_occurance__lte=now,
                                is_recurring=True,
                                parent_recurring_task=None,
                                )
    with transaction.atomic():
        for template in tasks:
            today = timezone.now()
            task_copy_due_date = today.replace(
                hour=template.due_date.hour,
                minute=template.due_date.minute,
                second=0,
                microsecond=0
            )
            task_copy = Task.objects.create(
                user=template.user,
                title=template.title,
                description=template.description,
                is_completed=False,
                priority=template.priority,
                due_date = task_copy_due_date,
                is_recurring=False,
                category=template.category,
                parent_recurring_task=template
            )
            task_copy.tags.set(template.tags.all())
            for subtask in template.subtasks.all():
                SubTask.objects.create(
                    title=subtask.title,
                    parent_task=task_copy,
                    is_completed=False
                )
            template.recurrence_rule.calculate_next_occurrence()
            template.recurrence_rule.save()


@shared_task
def send_reminder_email():
    tasks = Task.objects.filter(reminder__isnull = False,
                                reminder__lte=timezone.now(),
                                is_completed=False,
                                expired=False,)
    for task in tasks:
        time_left = task.due_date - timezone.now() if task.due_date else None
        send_mail(
            subject='Reminder',
            message=f'Do not forget to complete "{task}" task. Time left: {time_left}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[task.user.email],
            fail_silently=False,
        )
        task.reminder = None
        task.save()


@shared_task
def check_tasks_expiration():
    # Don't need the for loop at all!
    Task.objects.filter(
        is_completed=False,
        expired=False,
        due_date__isnull=False,
        due_date__lt=timezone.now()
    ).update(expired=True)


@shared_task
def delete_old_expired_tasks():
    threshold_date = timezone.now() - timedelta(days=30)

    Task.objects.filter(
        expired=True,
        is_completed=False,
        due_date__lt=threshold_date
    ).delete()


@shared_task
def send_amount_of_tasks_for_today():
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    for user in MyUser.objects.filter(is_active=True):
        tasks_for_today = Task.objects.filter(
            user=user,
            is_completed=False,
            due_date__gte=today_start,
            due_date__lt=today_end,
        ).order_by('due_date', 'priority')

        if tasks_for_today.exists():
            send_mail(
                subject='TaskSphere',
                message=f'Hello {user.username}! You have {tasks_for_today.count()} tasks for today\n\n'
                        f'Have a productive day!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        else:
            send_mail(
                subject='TaskSphere',
                message=f'Hello {user.username}! You have no task for today.\n\n'
                        f'Have a nice day! ',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )


@shared_task
def send_amount_of_tasks_left_for_today():
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    for user in MyUser.objects.filter(is_active=True):
        tasks_for_today = Task.objects.filter(
            user=user,
            due_date__gte=today_start,
            due_date__lt=today_end,
            is_completed=False
        ).order_by('due_date', 'priority')

        if tasks_for_today.exists():
            send_mail(
                subject='TaskSphere',
                message=f'{user.username}, the day is nearing its end! .You have {tasks_for_today.count()} incompleted tasks left for today\n\n'
                        f'',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )


@shared_task
def send_weekly_reports():
    week_ago = timezone.now() - timedelta(days=7)

    for user in MyUser.objects.filter(is_active=True):
        completed_tasks = Task.objects.filter(
            user=user,
            is_completed=True,
            updated_at__gte=week_ago,
        ).count()

        total_tasks = Task.objects.filter(
            user=user,
            created_at__gte=week_ago
        ).count()

        if total_tasks > 0:
            completion_rate = (completed_tasks/total_tasks) * 100

            send_mail(
                subject='Your weekly progress report',
                message=f'Hello {user.username}! \n\n'
                        f'Tasks completed in this week: {completed_tasks}/{total_tasks}({completion_rate})\n'
                        f'Keep up the good work!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )


@shared_task
def calculate_user_streak():
    for user in MyUser.objects.filter(is_active=True):
        yesterday = timezone.now().date() - timedelta(days=1)
        completed_yesterday = Task.objects.filter(
            user=user,
            is_completed=True,
            updated_at__date = yesterday,
        ).exists()

        if completed_yesterday:
            user.current_streak += 1
            user.save()

            award_karma_to_user(user=user, amount=20, reason='Daily streak maintained')

            if user.current_streak % 7 == 0:
                award_karma_to_user(user=user, amount=350, reason='7 days streak bonus')

            if user.current_streak % 30 == 0:
                award_karma_to_user(user=user, amount=1000, reason='30 days streak bonus')

        else:
            # User missed a day - update highest streak if needed, then reset
            if user.current_streak > user.highest_streak:
                user.highest_streak = user.current_streak
            user.current_streak = 0
            user.save()


    