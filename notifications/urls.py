# unitribe_server/notifications/urls.py

from django.urls import path
from .views import (NotificationListView, UnreadNotificationCountView, 
                   MarkNotificationAsReadView, MarkAllNotificationsAsReadView)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', UnreadNotificationCountView.as_view(), name='unread-notification-count'),
    path('<int:notification_id>/mark-as-read/', MarkNotificationAsReadView.as_view(), name='mark-notification-read'),
    path('mark-all-as-read/', MarkAllNotificationsAsReadView.as_view(), name='mark-all-notifications-read'),
]




