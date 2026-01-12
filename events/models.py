#unitribe_server/events/models.py

from django.db import models
from users.models import User
from clubs.models import Club

class Event(models.Model):
    EVENT_TYPES = [
        ('academic', 'Academic'),
        ('social', 'Social'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_organized')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    attendees = models.ManyToManyField(User, related_name='events_attending', blank=True)
    max_participants = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    @property
    def attendee_count(self):
        return self.attendees.count()
    
    @property
    def is_full(self):
        if self.max_participants:
            return self.attendee_count >= self.max_participants
        return False
    

