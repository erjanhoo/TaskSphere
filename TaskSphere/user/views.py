from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth import authenticate

from .models import TemporaryUser
from .serializers import (
    UserOTPVerificationSerializer, 
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    ForgotPasswordSerializer, 
    ForgotPasswordOTPVerificationSerializer
)
from .tasks import send_otp_email
from .services import generate_otp
from .throttling import OTPVerificationThrottle, OTPResendThrottle, ForgotPasswordThrottle

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


User = get_user_model()

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
                    }, status=status.HTTP_200.OK)

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
            }, status=status.HTTP_200.OK)
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
                temp_reg.delete()

                refresh = RefreshToken.for_user(user)

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
                
            





