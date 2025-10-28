from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


@shared_task
def send_otp_email(user_email,otp_code):
    send_mail(
        subject='Code',
        message=f'Your OTP code is {otp_code}',
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
    from .models import TemporaryUser
    
    expiry_time = timezone.now() - timedelta(hours=1)
    deleted_count = TemporaryUser.objects.filter(
        otp_created_at__lt=expiry_time
    ).delete()[0]
    
    return f"Cleaned up {deleted_count} expired temporary user records"
