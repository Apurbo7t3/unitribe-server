#unitribe/unitribe_server/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.views.generic import TemplateView

schema_view = get_schema_view(
    openapi.Info(
        title="UniTribe API",
        default_version='v1',
        description="""UniTribe - University Community Engagement Platform API Documentation.
        
        ## Quick Links
        - [User Authentication](#tag/Authentication)
        - [User Management](#tag/Users)
        - [Clubs Management](#tag/Clubs)
        - [Events Management](#tag/Events)
        - [Posts & Feed](#tag/Posts)
        - [Messaging](#tag/Messaging)
        - [Notifications](#tag/Notifications)
        - [Admin Dashboard](#tag/Admin)
        
        ## API Base URL
        ```
        http://localhost:8000/api/
        ```
        
        ## Authentication
        This API uses JWT authentication. Include the token in the header:
        ```
        Authorization: Bearer <your_access_token>
        ```
        """,
        terms_of_service="https://unitribe.example.com/terms/",
        contact=openapi.Contact(email="support@unitribe.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('', TemplateView.as_view(template_name='swagger_redirect.html'), name='home'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/auth/', include('users.urls')),
    path('api/clubs/', include('clubs.urls')),
    path('api/events/', include('events.urls')),
    path('api/posts/', include('posts.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/analytics/', include('analytics.urls')),
    
    # Health Check
    path('health/', TemplateView.as_view(template_name='health.html'), name='health'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

