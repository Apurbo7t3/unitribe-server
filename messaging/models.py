#unitribe_server/messaging/models.py

from django.db import models
from users.models import User
from django.utils import timezone

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=200, blank=True)
    group_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group:
            return self.group_name
        participants = list(self.participants.all())
        if len(participants) == 2:
            return f"{participants[0]} - {participants[1]}"
        return f"Group: {self.group_name}"
    
    def get_other_participant(self, user):
        if not self.is_group:
            return self.participants.exclude(id=user.id).first()
        return None

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    file = models.FileField(upload_to='message_files/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class UserMessageSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='message_settings')
    allow_messages_from = models.CharField(max_length=20, choices=[
        ('everyone', 'Everyone'),
        ('contacts', 'Contacts Only'),
        ('none', 'No One'),
    ], default='everyone')
    message_notifications = models.BooleanField(default=True)
    sound_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Message settings for {self.user}"

