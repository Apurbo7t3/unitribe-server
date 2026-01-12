from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="UniTribe API",
        default_version='v1',
        description="""
        # UniTribe - University Community Engagement Platform API
        
        ## Overview
        UniTribe is a unified digital ecosystem that consolidates academic, social, and administrative interactions 
        into one integrated platform for university communities.
        
        ## Authentication
        This API uses JWT (JSON Web Token) authentication. To authenticate:
        
        1. Register a new user at `/api/auth/register/`
        2. Login at `/api/auth/login/` to get your access token
        3. Use the token in your requests:
           ```
           Authorization: Bearer <your_access_token>
           ```
        
        ## User Roles
        - **Student**: Can join clubs, attend events, create posts
        - **Faculty**: Can create clubs, organize events, manage courses
        - **Admin**: Full system access, can manage all resources
        
        ## Rate Limiting
        - Anonymous users: 100 requests per day
        - Authenticated users: 1000 requests per day
        
        ## Error Responses
        All error responses follow the same format:
        ```json
        {
            "error": "Error message description"
        }
        ```
        
        ## Status Codes
        - 200: Success
        - 201: Created
        - 400: Bad Request
        - 401: Unauthorized
        - 403: Forbidden
        - 404: Not Found
        - 429: Too Many Requests
        - 500: Internal Server Error
        """,
        terms_of_service="https://unitribe.example.com/terms/",
        contact=openapi.Contact(email="support@unitribe.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)