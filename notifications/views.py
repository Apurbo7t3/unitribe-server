# unitribe_server/notifications/views.py

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

class UnreadNotificationCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        return Response({'unread_count': count})

class MarkNotificationAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, notification_id):
        notification = Notification.objects.get(
            id=notification_id, 
            user=request.user
        )
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class MarkAllNotificationsAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True)
        return Response({'status': 'all marked as read'})
    


