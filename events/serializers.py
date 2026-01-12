#unitribe_server/events/serializers.py

from rest_framework import serializers
from .models import Event
from clubs.serializers import ClubSerializer
from users.serializers import UserBasicSerializer
from django.utils import timezone

class EventSerializer(serializers.ModelSerializer):
    club_details = ClubSerializer(source='club', read_only=True)
    organizer_details = UserBasicSerializer(source='organizer', read_only=True)
    attendee_count = serializers.IntegerField(read_only=True)
    is_attending = serializers.SerializerMethodField()
    is_past = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_is_attending(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.attendees.filter(id=request.user.id).exists()
        return False
    
    def get_is_past(self, obj):
        return obj.end_date < timezone.now()

class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('title', 'description', 'event_type', 'club', 
                 'start_date', 'end_date', 'location', 'max_participants')
        

