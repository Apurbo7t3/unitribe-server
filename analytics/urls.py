from django.urls import path
from .views import AdminDashboardView, UserEngagementAnalyticsView, PlatformHealthView

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('user-engagement/', UserEngagementAnalyticsView.as_view(), name='user-engagement'),
    path('platform-health/', PlatformHealthView.as_view(), name='platform-health'),
]