# users/swagger_docs.py
# Don't import views here - create decorators only
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Common Response Schemas
error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING),
        'detail': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

success_message_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

# Register Swagger decorator
def get_register_swagger():
    from .serializers import UserRegisterRequestSerializer, UserRegisterResponseSerializer
    
    return swagger_auto_schema(
        operation_description="""
        Register a new user account.
        
        ### Roles:
        - **student**: Must provide student_id
        - **faculty**: Should not provide student_id
        
        ### Security:
        - Passwords are hashed and never returned
        - Admin roles cannot be self-assigned
        - Verification email sent automatically
        
        ### Response:
        - Returns user info without sensitive data
        - Verification email sent to provided email
        """,
        request_body=UserRegisterRequestSerializer,
        responses={
            201: UserRegisterResponseSerializer,
            400: error_response_schema,
            429: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
        },
        tags=['Authentication']
    )

# Login Swagger decorator
def get_login_swagger():
    from .serializers import UserLoginRequestSerializer
    
    return swagger_auto_schema(
        operation_description="""
        Authenticate user and return JWT tokens.
        
        ### Authentication:
        - Email and password required
        - Returns access and refresh tokens
        
        ### Security:
        - Rate limited: 5 attempts per minute
        - Unverified users may be blocked (configurable)
        - IP address logged for security
        
        ### Response:
        - Access token (short-lived, 1 day)
        - Refresh token (long-lived, 7 days)
        - User profile information
        """,
        request_body=UserLoginRequestSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            ),
            401: error_response_schema,
            403: error_response_schema,
            429: error_response_schema,
        },
        tags=['Authentication']
    )

# Logout Swagger decorator
def get_logout_swagger():
    from .serializers import LogoutSerializer
    
    return swagger_auto_schema(
        operation_description="""
        Logout user and blacklist refresh token.
        
        ### Security:
        - Refresh token blacklisted
        - Access tokens expire naturally
        - User must be authenticated
        
        ### Note:
        - Only refresh tokens are blacklisted
        - Access tokens remain valid until expiry
        """,
        request_body=LogoutSerializer,
        responses={
            200: success_message_schema,
            400: error_response_schema,
            401: error_response_schema,
        },
        tags=['Authentication']
    )

# Verify Email Swagger decorator
def get_verify_email_swagger():
    from .serializers import EmailVerificationSerializer
    
    return swagger_auto_schema(
        operation_description="""
        Verify email address with token.
        
        ### Token Expiry:
        - Tokens expire after 24 hours
        - Expired tokens trigger new email
        
        ### Flow:
        1. User registers → receives verification email
        2. User clicks link → token sent to this endpoint
        3. If valid → email verified
        4. If expired → new email sent
        """,
        request_body=EmailVerificationSerializer,
        responses={
            200: success_message_schema,
            400: error_response_schema,
        },
        tags=['Authentication']
    )

# Password Reset Swagger decorator
def get_password_reset_swagger():
    from .serializers import PasswordResetRequestSerializer
    
    return swagger_auto_schema(
        operation_description="""
        Request password reset.
        
        ### Security:
        - Rate limited: 5 requests per hour
        - Doesn't reveal if email exists
        - Reset link expires in 1 hour
        
        ### Flow:
        1. User requests reset → email sent
        2. User clicks link → goes to frontend
        3. Frontend calls reset-confirm with new password
        """,
        request_body=PasswordResetRequestSerializer,
        responses={
            200: success_message_schema,
            400: error_response_schema,
            429: error_response_schema,
        },
        tags=['Authentication']
    )