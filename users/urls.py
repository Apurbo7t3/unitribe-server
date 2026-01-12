#unitribe/users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, UserProfileView,
    VerifyEmailView, ResendVerificationEmailView,
    PasswordResetRequestView, PasswordResetConfirmView,
    LogoutView, LogoutAllView, AdminUserManageView
)

urlpatterns = [
    # Registration
    path('register/', RegisterView.as_view(), name='register'),
    
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout-all/', LogoutAllView.as_view(), name='logout-all'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # Email Verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    
    # Password Reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # Admin
    path('admin/users/<int:user_id>/', AdminUserManageView.as_view(), name='admin-user-manage'),
]

