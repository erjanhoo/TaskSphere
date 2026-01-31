from django.urls import path
from .views import (
    UserRegistrationView,
    # UserRegistrationOTPVerificationView,
    UserLoginView,
    # UserLoginOTPVerificationView,
    UserResendOTPView,
    UserForgotPasswordView,
    # UserForgotPasswordOTPVerificationView,
    UserLogoutView,
    UserProfileView,
    UserBadgesView,
    AllBadgesView,
    LeaderboardView,
    KarmaHistoryView,
)

urlpatterns = [
    # Registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    # path('register/verify-otp/', UserRegistrationOTPVerificationView.as_view(), name='register-verify-otp'),
    path('resend-otp/', UserResendOTPView.as_view(), name='resend-otp'),
    
    # Login
    path('login/', UserLoginView.as_view(), name='user-login'),
    # path('login/verify-otp/', UserLoginOTPVerificationView.as_view(), name='login-verify-otp'),
    
    # Password Reset
    path('forgot-password/', UserForgotPasswordView.as_view(), name='forgot-password'),
    # path('forgot-password/verify/', UserForgotPasswordOTPVerificationView.as_view(), name='forgot-password-verify'),
    
    # Logout
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    
    # Profile & Gamification
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('badges/', UserBadgesView.as_view(), name='user-badges'),
    path('badges/all/', AllBadgesView.as_view(), name='all-badges'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('karma/history/', KarmaHistoryView.as_view(), name='karma-history'),
]
