# unitribe_server/notifications/models.py

from django.db import models
from users.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('event', 'Event'),
        ('post', 'Post'),
        ('club', 'Club'),
        ('message', 'Message'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user}"
    
    class Meta:
        ordering = ['-created_at']


