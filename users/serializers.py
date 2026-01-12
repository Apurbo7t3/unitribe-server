#unitribe/users/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import User
import uuid
from django.utils import timezone

User = get_user_model()

# ============ BASIC SERIALIZERS (for other apps) ============
class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info serializer for nested relationships"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'student_id', 'department', 'profile_picture',
            'is_verified'
        ]
        read_only_fields = fields

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for lists and search results"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'role', 'department', 'profile_picture'
        ]
        read_only_fields = fields

# ============ AUTHENTICATION SERIALIZERS ============
class UserRegisterRequestSerializer(serializers.ModelSerializer):
    """Serializer for user registration (REQUEST only)"""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'},
        min_length=8
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 
            'first_name', 'last_name', 'role',
            'student_id', 'department'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': False},
            'student_id': {'required': False},
            'department': {'required': False},
        }
    
    def validate(self, attrs):
        # Password match validation
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        
        # Email uniqueness
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "A user with this email already exists."
            })
        
        # Role validation - prevent admin registration
        role = attrs.get('role', 'student')
        if role not in ['student', 'faculty']:
            raise serializers.ValidationError({
                "role": "Only 'student' or 'faculty' roles can be registered."
            })
        
        # Faculty validation
        if role == 'faculty' and attrs.get('student_id'):
            raise serializers.ValidationError({
                "student_id": "Faculty members should not have student ID."
            })
        
        # Student validation
        if role == 'student' and not attrs.get('student_id'):
            raise serializers.ValidationError({
                "student_id": "Student ID is required for students."
            })
        
        # Student ID uniqueness
        student_id = attrs.get('student_id')
        if student_id and User.objects.filter(student_id=student_id).exists():
            raise serializers.ValidationError({
                "student_id": "A user with this student ID already exists."
            })
        
        return attrs
    
    def create(self, validated_data):
        # Remove password2 from validated data
        validated_data.pop('password2')  # FIXED
        
        token = uuid.uuid4()
        
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', 'student'),
            student_id=validated_data.get('student_id'),
            department=validated_data.get('department', ''),
            email_verification_token=token
        )
        
        # Send verification email
        self._send_verification_email(user)
        return user
    
    def _send_verification_email(self, user):
        """Send email verification link"""
        subject = 'Verify your UniTribe account'
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}/"
        message = f"""
        Welcome to UniTribe, {user.first_name}!
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        The UniTribe Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

class UserRegisterResponseSerializer(serializers.ModelSerializer):
    """Serializer for user registration (RESPONSE only)"""
    message = serializers.CharField(default="Registration successful. Verification email sent.")
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'department', 'is_verified', 'message'
        ]
        read_only_fields = fields

class UserLoginRequestSerializer(serializers.Serializer):
    """Serializer for login request"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        fields = ['email', 'password']

class UserLoginResponseSerializer(serializers.ModelSerializer):
    """Serializer for login response"""
    access = serializers.CharField(source='access_token', read_only=True)
    refresh = serializers.CharField(source='refresh_token', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'access', 'refresh',
            'id', 'email', 'first_name', 'last_name',
            'role', 'department', 'student_id',
            'profile_picture', 'is_verified'
        ]
        read_only_fields = fields

# ============ PROFILE SERIALIZERS ============
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (GET/PUT)"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'student_id', 'department', 'bio',
            'profile_picture', 'interests', 'is_verified',
            'show_email', 'show_profile', 'date_joined',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'student_id',
            'is_verified', 'date_joined', 'created_at', 'updated_at'
        ]

# ============ VERIFICATION SERIALIZERS ============
class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.UUIDField(required=True)
    
    class Meta:
        fields = ['token']

class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending verification email"""
    email = serializers.EmailField(required=True)
    
    class Meta:
        fields = ['email']

# ============ PASSWORD RESET SERIALIZERS ============
class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField(required=True)
    
    class Meta:
        fields = ['email']

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        min_length=8
    )
    
    class Meta:
        fields = ['token', 'new_password']

# ============ OTHER SERIALIZERS ============
class LogoutSerializer(serializers.Serializer):
    """Serializer for logout"""
    refresh = serializers.CharField(required=True)
    
    class Meta:
        fields = ['refresh']

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin user updates"""
    class Meta:
        model = User
        fields = ['role', 'is_active', 'is_verified']
        
    def validate_role(self, value):
        request_user = self.context['request'].user
        if not request_user.role == 'admin':
            raise serializers.ValidationError("Only admins can change user roles.")
        return value
    
