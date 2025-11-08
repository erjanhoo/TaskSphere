from celery import shared_task
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import TemporaryUser


@shared_task
def send_otp_email(user_email,otp_code):
    send_mail(
        subject='Welcome to TaskSphere',
        message=f'Your OTP code is {otp_code}. If you did not send this request, please ignore this email.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )

@shared_task
def send_email(user_email, message):
    send_mail(
        subject='Welcome to TaskSphere',
        message=f'{message}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )



@shared_task
def cleanup_expired_temporary_users():
    """
    Delete temporary user records that are older than 1 hour.
    This prevents accumulation of abandoned registration attempts.
    Runs periodically via Celery Beat.
    """

    
    expiry_time = timezone.now() - timedelta(hours=1)
    deleted_count = TemporaryUser.objects.filter(
        otp_created_at__lt=expiry_time
    ).delete()[0]
    
    return f"Cleaned up {deleted_count} expired temporary user records"
