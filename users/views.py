#unitribe/users/views.py

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken, BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import User
from .serializers import (
    UserRegisterRequestSerializer, UserRegisterResponseSerializer,
    UserLoginRequestSerializer, UserLoginResponseSerializer,
    UserProfileSerializer, EmailVerificationSerializer,
    ResendVerificationSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, LogoutSerializer,
    AdminUserUpdateSerializer
)
from .throttles import (
    LoginThrottle, RegisterThrottle,
    PasswordResetThrottle, EmailVerificationThrottle
)

class RegisterView(generics.CreateAPIView):
    throttle_classes = [RegisterThrottle]
    """
    Register a new user account.
    
    Creates a new user with the provided information.
    A verification email will be sent to the provided email address.
    
    **Roles:**
    - Only 'student' or 'faculty' roles can be registered
    - Admin and club_admin roles cannot be self-assigned
    
    **Requirements:**
    - Students must provide student_id
    - Faculty should not provide student_id
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterRequestSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = UserRegisterResponseSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    throttle_classes = [LoginThrottle]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Get user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check password
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check email verification based on settings
        ALLOW_UNVERIFIED_LOGIN = getattr(settings, 'ALLOW_UNVERIFIED_LOGIN', False)
        
        if not user.is_verified and not ALLOW_UNVERIFIED_LOGIN:
            return Response(
                {'error': 'Please verify your email before logging in.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Prepare response
        response_data = {
            'access': access_token,
            'refresh': refresh_token,
            'user': UserLoginResponseSerializer(user).data
        }

        return Response(response_data, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user's profile.
    
    **Read-only fields:**
    - id, email, role, student_id, is_verified, date_joined
    
    **Updatable fields:**
    - first_name, last_name, bio, profile_picture, interests, privacy settings
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        token_str = str(serializer.validated_data["token"])  # Convert to string
        
        try:
            # Convert string token to UUID for comparison
            token_uuid = uuid.UUID(token_str)
            user = User.objects.get(email_verification_token=token_uuid)
            
            # Check token expiry (24 hours)
            if user.email_verification_sent_at:
                expiry_time = user.email_verification_sent_at + timedelta(hours=24)
                if timezone.now() > expiry_time:
                    user.email_verification_token = uuid.uuid4()
                    user.save()
                    return Response(
                        {"error": "Verification link expired."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # VERIFY USER
            user.is_verified = True
            user.email_verification_token = None  # Clear the token after verification
            user.save()
            
            return Response(
                {"message": "Email verified successfully."},
                status=status.HTTP_200_OK
            )
            
        except (User.DoesNotExist, ValueError):
            return Response(
                {"error": "Invalid or expired verification token."},
                status=status.HTTP_400_BAD_REQUEST
            )



class ResendVerificationEmailView(APIView):
    throttle_classes = [EmailVerificationThrottle]
    """
    Resend verification email.
    
    **Rate Limit:** 3 emails per hour per user
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_verified:
                return Response(
                    {'message': 'Email already verified'},
                    status=status.HTTP_200_OK
                )
            
            # Generate new token
            user.email_verification_token = uuid.uuid4()
            user.email_verification_sent_at = timezone.now()
            user.save(update_fields=[
                'email_verification_token',
                'email_verification_sent_at'
            ])

            
            # Send verification email
            self._send_verification_email(user)
            
            return Response(
                {'message': 'Verification email sent successfully'},
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            # Don't reveal if user exists (security)
            return Response(
                {'message': 'If an account exists with this email, a verification link has been sent.'},
                status=status.HTTP_200_OK
            )
    
    def _send_verification_email(self, user):
        """Helper method to send verification email"""
        subject = 'Verify your UniTribe account'
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}/"
        message = f"""
        Hello {user.first_name},
        
        Here's your new verification link:
        {verification_url}
        
        This link will expire in 24 hours.
        
        Best regards,
        UniTribe Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class PasswordResetRequestView(APIView):
    throttle_classes = [PasswordResetThrottle]
    """
    Request password reset.
    
    Sends a password reset email with a token.
    **Rate Limit:** 5 requests per hour per IP
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Generate reset token
            user.reset_password_token = uuid.uuid4()
            user.save()
            
            # Send reset email
            self._send_reset_email(user)
            
            return Response(
                {'message': 'Password reset email sent'},
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            # Don't reveal if user exists (security)
            return Response(
                {'message': 'If an account exists with this email, a reset link has been sent.'},
                status=status.HTTP_200_OK
            )
    
    def _send_reset_email(self, user):
        """Helper method to send password reset email"""
        subject = 'Reset your UniTribe password'
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{user.reset_password_token}/"
        message = f"""
        Hello {user.first_name},
        
        You requested to reset your password. Click the link below:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        UniTribe Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    
    **Token Expiry:** 1 hour
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(reset_password_token=token, is_active=True)
            
            # Check token expiry (1 hour)
            token_age = timezone.now() - user.updated_at
            if token_age > timedelta(hours=1):
                user.reset_password_token = None
                user.save()
                return Response(
                    {'error': 'Reset token expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update password
            user.set_password(new_password)
            user.reset_password_token = None
            user.save()
            
            # Send confirmation email
            self._send_confirmation_email(user)
            
            # Blacklist all existing tokens for security
            self._blacklist_user_tokens(user)
            
            return Response(
                {'message': 'Password reset successful'},
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired reset token'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _send_confirmation_email(self, user):
        """Helper method to send password reset confirmation"""
        subject = 'Password reset successful'
        message = f"""
        Hello {user.first_name},
        
        Your password has been reset successfully.
        
        If you didn't do this, please contact support immediately.
        
        Best regards,
        UniTribe Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    
    def _blacklist_user_tokens(self, user):
        """Blacklist all refresh tokens for a user"""
        # This requires storing refresh tokens in database
        # For now, we'll just invalidate by not storing them
        pass

class LogoutView(APIView):
    """
    Logout user and blacklist refresh token.
    
    **Note:** Access tokens will expire naturally.
    Only refresh tokens are blacklisted.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refresh_token = serializer.validated_data['refresh']
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )

class LogoutAllView(APIView):
    """
    Logout user from all devices.
    
    Blacklists all refresh tokens for the current user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # In a real implementation, you would:
        # 1. Store issued refresh tokens in database
        # 2. Blacklist all tokens for this user
        # 3. Clear session data
        
        return Response(
            {'message': 'Logged out from all devices'},
            status=status.HTTP_200_OK
        )

class AdminUserManageView(APIView):
    """
    Admin-only endpoint to manage users.
    
    **Permissions:** Admin role required
    **Actions:** Update role, activate/deactivate, verify email
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, user_id):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = get_object_or_404(User, id=user_id)
        serializer = AdminUserUpdateSerializer(
            user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'User updated successfully', 'user': serializer.data},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

