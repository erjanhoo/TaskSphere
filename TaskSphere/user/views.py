from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDate

from .models import TemporaryUser, UserBadge, Badges, KarmaTransaction
from .serializers import (
    UserOTPVerificationSerializer, 
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    ForgotPasswordSerializer, 
    ForgotPasswordOTPVerificationSerializer,

    UserProfileSerializer,
)
from .tasks import send_otp_email, send_email
from .services import generate_otp
from .throttling import OTPVerificationThrottle, OTPResendThrottle, ForgotPasswordThrottle

from task.models import Task

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


User = get_user_model()

"""
USER AUTHENTICATION
"""
class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                if User.objects.filter(email=serializer.validated_data['email']).exists():
                    return Response({
                        'message': 'Email already exists',
                    }, status=status.HTTP_400_BAD_REQUEST)

                if TemporaryUser.objects.filter(email=serializer.validated_data['email']).exists():
                    TemporaryUser.objects.filter(email=serializer.validated_data['email']).delete()

                otp = generate_otp()

                with transaction.atomic():
                    temp_reg = TemporaryUser.objects.create(
                        email=serializer.validated_data['email'],
                        username=serializer.validated_data['username'],
                        password=serializer.validated_data['password'],
                        otp_code=otp,
                        otp_created_at=timezone.now()
                    )
                    temp_reg.save()
                    transaction.on_commit(lambda: send_otp_email.delay(temp_reg.email, temp_reg.otp_code))

                    return Response({
                        'message': 'OTP code was sent to your email, please confirm it to complete registration',
                        'user_id': temp_reg.id,
                    }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'message': str(e),
                })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserLoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = authenticate(
                request=request,
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user.is_2fa_enabled:
                otp_code = generate_otp()
                user.otp_code = otp_code
                user.otp_created = timezone.now()
                user.save()

                send_otp_email.delay(user.email, otp_code)
                return Response({
                    'user_id':user.id
                }, status=status.HTTP_200_OK)
            else:
                refresh = RefreshToken.for_user(user=user)
                
                return Response({
                    'refresh_token':str(refresh),
                    'access':str(refresh.access_token),
                    'message':'You have successfully logged it'
                })
        


class UserResendOTPView(APIView):
    throttle_classes = [OTPResendThrottle]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'message': 'Email is required',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            temp_user = TemporaryUser.objects.get(email=email)
            new_otp = generate_otp()
            temp_user.otp_code = new_otp
            temp_user.save()

            send_otp_email.delay(temp_user.email, temp_user.otp_code)
            return Response({
                'message': 'New OTP code was sent to your email',
            }, status=status.HTTP_200_OK)
        except TemporaryUser.DoesNotExist:
            return Response({
                'message': 'User with this email does not exist',
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UserForgotPasswordView(APIView):
    throttle_classes = [ForgotPasswordThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                # Use email to find user, not user_id (user doesn't know their ID)
                user = User.objects.get(email=serializer.validated_data['email'])
            except User.DoesNotExist:
                # Don't reveal if email exists or not (security best practice)
                return Response({
                    'message': 'If this email exists, a password reset code has been sent'
                }, status=status.HTTP_200_OK)
            
            forgot_password_otp = generate_otp()
            user.forgot_password_otp = forgot_password_otp
            user.forgot_password_otp_created_at = timezone.now()  # Track when OTP was created
            user.save()

            send_otp_email.delay(user.email, forgot_password_otp)
            
            # Return user_id so frontend can send it back with OTP
            return Response({
                'message': 'Password reset code has been sent to your email',
                'user_id': user.id  # Frontend needs this for the next request
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Invalid information provided'
        }, status=status.HTTP_400_BAD_REQUEST)
        


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({
                    'message': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'message': 'You have successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'message': 'Invalid token or token already blacklisted'
            }, status=status.HTTP_400_BAD_REQUEST)




"""
OTP Verifications
"""
class UserForgotPasswordOTPVerificationView(APIView):
    """
    This view handles BOTH OTP verification AND password change in ONE request.
    
    Frontend sends from the "Reset Password" page:
    - user_id (received from UserForgotPasswordView response)
    - otp_code (from email)
    - new_password (user types)
    - confirm_password (user types)
    
    Backend logic:
    1. Verify OTP is correct
    2. Check OTP hasn't expired
    3. If OTP valid → change password
    4. If OTP invalid → return error, password NOT changed
    """
    throttle_classes = [OTPVerificationThrottle]
    
    def post(self, request):
        serializer = ForgotPasswordOTPVerificationSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            try:
                user = User.objects.get(id=serializer.validated_data['user_id'])
            except User.DoesNotExist:
                return Response({
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user has a password reset OTP
            if not user.forgot_password_otp:
                return Response({
                    'message': 'No password reset request found. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify OTP matches
            if user.forgot_password_otp != serializer.validated_data['otp_code']:
                return Response({
                    'message': 'Incorrect OTP code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check OTP expiry (5 minutes)
            if user.forgot_password_otp_created_at:
                otp_expiry_minutes = 5
                time_elapsed = (timezone.now() - user.forgot_password_otp_created_at).total_seconds()
                
                if time_elapsed > (otp_expiry_minutes * 60):
                    # Clear expired OTP
                    user.forgot_password_otp = None
                    user.forgot_password_otp_created_at = None
                    user.save()
                    
                    return Response({
                        'message': 'OTP has expired. Please request a new password reset.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # OTP is valid! Now change the password
            user.set_password(serializer.validated_data['new_password'])
            
            # Clear the OTP fields after successful password change
            user.forgot_password_otp = None
            user.forgot_password_otp_created_at = None
            user.save()
            
            return Response({
                'message': 'Password has been successfully reset. You can now login with your new password.'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Invalid information provided'
        }, status=status.HTTP_400_BAD_REQUEST)



class UserRegistrationOTPVerificationView(APIView):

    throttle_classes = [OTPVerificationThrottle]

    def post(self, request):
        serializer = UserOTPVerificationSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            temp_reg_id = serializer.validated_data['user_id']
            entered_otp_code = serializer.validated_data['otp_code']

            try:
                temp_reg = TemporaryUser.objects.get(id=temp_reg_id)
            except TemporaryUser.DoesNotExist:
                return Response('Registration request not found', status=status.HTTP_400_BAD_REQUEST)
            
            otp_expiry = 5
            temp_reg_otp_created_at = temp_reg.otp_created_at
            current_time = timezone.now()

            if (current_time - temp_reg_otp_created_at).total_seconds() > otp_expiry * 60:
                return Response('OTP code has expired', status=status.HTTP_400_BAD_REQUEST)

            if temp_reg.otp_code == entered_otp_code:
                user = User(
                    username=temp_reg.username,
                    email=temp_reg.email,
                    
                )
                user.set_password(temp_reg.password)
                user.save()
                
                # Initialize user with beginner badge
                beginner_badge = Badges.objects.filter(name='beginner').first()
                if beginner_badge:
                    UserBadge.objects.create(user=user, badge=beginner_badge)
                
                temp_reg.delete()

                refresh = RefreshToken.for_user(user)

                send_email.delay(user.email, 'You have successfully registered in TaskSphere! ')

                return Response({
                    'refresh_token':str(refresh),
                    'access_token':str(refresh.access_token),
                    'user_id':user.id,
                    'message':'Successfully registered'
                },status=status.HTTP_201_CREATED)

            else:
                return Response('Incorrect OTP code', status=status.HTTP_400_BAD_REQUEST)



class UserLoginOTPVerificationView(APIView):
    throttle_classes = [OTPVerificationThrottle]
    
    def post(self, request):
        serializer = UserOTPVerificationSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            try:
                user = User.objects.get(id=serializer.validated_data['user_id'])
            except User.DoesNotExist:
                return Response('User not found', status=status.HTTP_404_NOT_FOUND)
            
            if not user.otp_code == serializer.validated_data['otp_code']:
                return Response('Incorrect OTP, try again', status=status.HTTP_400_BAD_REQUEST)
            
            user_otp_created_at = user.otp_created_at
            otp_expiry = 2

            if (timezone.now() - user_otp_created_at).total_seconds() > (otp_expiry * 60):
                return Response('OTP has expired, try again', status=status.HTTP_400_BAD_REQUEST)
            
            refresh = RefreshToken.for_user(user=user)

            return Response({
                'refresh_token':str(refresh),
                'access_token':str(refresh.access_token),
                'user_id':user.id,
                'message':'Welcome Back!'
            },status=status.HTTP_200_OK)
        return Response('Invalid information provided')
                
            

"""
USER INTERFACE
"""
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Add authentication requirement
    
    def get(self, request):
        # Use user ID instead of username for cache key (more reliable)
        cache_key = f'profile_info_user_{request.user.id}'
        cache_data = cache.get(cache_key)

        if cache_data:
            return Response(cache_data, status=status.HTTP_200_OK)

        user = request.user
        total_completed_tasks = Task.objects.filter(
            user=request.user,
            is_completed=True
        ).count()


        """
        Get amount of completed tasks on each day for
        the past 7days
        """
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)
        
        
        # Get completed tasks in range
        completed_tasks = Task.objects.filter(
            user=user,
            is_completed=True,
            updated_at__date__gte=seven_days_ago,
            updated_at__date__lte=today
        )
        
        # Group by date and count
        daily_stats = completed_tasks.annotate(
            completion_date=TruncDate('updated_at')
        ).values('completion_date').annotate(
            count=Count('id')
        ).order_by('completion_date')
        
        # Initialize all dates with 0
        date_range = {}
        current_date = seven_days_ago
        while current_date <= today:
            date_range[current_date] = 0
            current_date += timedelta(days=1)
        
        # Fill in actual counts
        for stat in daily_stats:
            date_range[stat['completion_date']] = stat['count']
        
        # Convert to list
        daily_completions = [
            {
                'date': str(date_key),
                'count': count,
                'day_name': date_key.strftime('%A')  # Monday, Tuesday, etc.
            }
            for date_key, count in sorted(date_range.items())
        ]

        # Get user's current badge level based on karma
        current_badge_level = Badges.objects.filter(
            karma_min__lte=user.karma,
            karma_max__gte=user.karma
        ).first()
        
        # Get all user badges (earned achievements)
        all_earned_badges = UserBadge.objects.filter(user=user).select_related('badge').order_by('-awarded_at')
        
        # Calculate totals
        total_completed_for_the_past_7d = sum(item['count'] for item in daily_completions)


        data = {
            'username': user.username,
            'karma': user.karma,
            'current_badge_level': {
                'name': current_badge_level.name if current_badge_level else 'No Badge',
                'karma_min': current_badge_level.karma_min if current_badge_level else 0,
                'karma_max': current_badge_level.karma_max if current_badge_level else 0,
                'progress_percentage': round(((user.karma - current_badge_level.karma_min) / (current_badge_level.karma_max - current_badge_level.karma_min)) * 100, 2) if current_badge_level and current_badge_level.karma_max > current_badge_level.karma_min else 100,
                'karma_to_next_level': max(0, current_badge_level.karma_max + 1 - user.karma) if current_badge_level else 0,
            } if current_badge_level else None,
            'earned_badges': [
                {
                    'name': ub.badge.name,
                    'awarded_at': ub.awarded_at,
                    'karma_range': f'{ub.badge.karma_min}-{ub.badge.karma_max}',
                } for ub in all_earned_badges
            ],
            'current_streak': user.current_streak,
            'highest_streak': user.highest_streak if user.highest_streak != 0 else user.current_streak,
            'start_date': str(seven_days_ago),
            'end_date': str(today),
            'total_amount_of_completed_tasks': total_completed_tasks,
            'total_amount_of_completed_tasks_for_the_past_7d': total_completed_for_the_past_7d,
            'amount_of_tasks_completed_on_each_day_for_the_past_7d': daily_completions,

        }

        cache.set(cache_key, data, timeout=60*5)

        return Response(data, status=status.HTTP_200_OK)


class UserBadgesView(APIView):
    """View all badges the user has earned"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_badges = UserBadge.objects.filter(user=request.user).select_related('badge').order_by('-awarded_at')
        
        badges_data = [
            {
                'id': ub.id,
                'name': ub.badge.name,
                'karma_min': ub.badge.karma_min,
                'karma_max': ub.badge.karma_max,
                'awarded_at': ub.awarded_at,
            }
            for ub in user_badges
        ]
        
        return Response({
            'total_badges': user_badges.count(),
            'badges': badges_data,
        }, status=status.HTTP_200_OK)


class AllBadgesView(APIView):
    """View all available badges in the system"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        all_badges = Badges.objects.all().order_by('karma_min')
        user_badge_ids = UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True)
        
        # Find current badge level based on user's karma
        user_karma = request.user.karma
        current_badge = Badges.objects.filter(
            karma_min__lte=user_karma,
            karma_max__gte=user_karma
        ).first()
        
        badges_data = [
            {
                'id': badge.id,
                'name': badge.name,
                'karma_min': badge.karma_min,
                'karma_max': badge.karma_max,
                'earned': badge.id in user_badge_ids,
                'is_current_level': badge.id == current_badge.id if current_badge else False,
                'karma_needed': max(0, badge.karma_min - user_karma) if user_karma < badge.karma_min else 0,
            }
            for badge in all_badges
        ]
        
        return Response({
            'total_available_badges': all_badges.count(),
            'badges': badges_data,
            'user_karma': user_karma,
            'current_badge': {
                'name': current_badge.name,
                'karma_min': current_badge.karma_min,
                'karma_max': current_badge.karma_max,
                'progress': {
                    'current': user_karma,
                    'min': current_badge.karma_min,
                    'max': current_badge.karma_max,
                    'percentage': round(((user_karma - current_badge.karma_min) / (current_badge.karma_max - current_badge.karma_min)) * 100, 2) if current_badge.karma_max > current_badge.karma_min else 100,
                    'karma_to_next_level': max(0, current_badge.karma_max + 1 - user_karma)
                }
            } if current_badge else None,
        }, status=status.HTTP_200_OK)



class LeaderboardView(APIView):
    """View top users by karma"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        top_users = User.objects.filter(is_active=True).order_by('-karma')[:limit]
        
        leaderboard_data = []
        for idx, user in enumerate(top_users, start=1):
            # Get current badge level based on karma, not earned badges
            current_badge_level = Badges.objects.filter(
                karma_min__lte=user.karma,
                karma_max__gte=user.karma
            ).first()
            
            leaderboard_data.append({
                'rank': idx,
                'username': user.username,
                'karma': user.karma,
                'current_streak': user.current_streak,
                'highest_streak': user.highest_streak,
                'current_badge_level': current_badge_level.name if current_badge_level else 'No Badge',
            })
        
        # Find current user's rank
        current_user_rank = User.objects.filter(is_active=True, karma__gt=request.user.karma).count() + 1
        
        return Response({
            'leaderboard': leaderboard_data,
            'your_rank': current_user_rank,
            'your_karma': request.user.karma,
        }, status=status.HTTP_200_OK)


class KarmaHistoryView(APIView):
    """View karma transaction history for the current user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .models import KarmaTransaction
        from datetime import datetime, timedelta
        from django.db.models import Sum
        
        # Get filter parameters
        days = int(request.query_params.get('days', 30))  # Last 30 days by default
        limit = int(request.query_params.get('limit', 50))  # Max 50 transactions
        
        # Get transactions
        transactions = KarmaTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')[:limit]
        
        # Calculate statistics
        today = timezone.now().date()
        start_date = today - timedelta(days=days)
        
        recent_transactions = KarmaTransaction.objects.filter(
            user=request.user,
            created_at__date__gte=start_date
        )
        
        total_earned = recent_transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
        total_lost = abs(recent_transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0)
        
        transactions_data = [
            {
                'id': t.id,
                'amount': t.amount,
                'reason': t.reason,
                'created_at': t.created_at,
                'type': 'earned' if t.amount > 0 else 'lost'
            }
            for t in transactions
        ]
        
        return Response({
            'current_karma': request.user.karma,
            'statistics': {
                'period_days': days,
                'total_earned': total_earned,
                'total_lost': total_lost,
                'net_change': total_earned - total_lost,
            },
            'transactions': transactions_data,
            'total_transactions': KarmaTransaction.objects.filter(user=request.user).count(),
        }, status=status.HTTP_200_OK)





        




