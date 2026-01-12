# unitribe_server/events/views.py - COMPLETED VERSION

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import Event
from .serializers import EventSerializer, EventCreateSerializer
from notifications.models import Notification
import json

class EventListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EventCreateSerializer
        return EventSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = Event.objects.filter(is_active=True)
        
        # Filter by type
        event_type = self.request.query_params.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by club
        club_id = self.request.query_params.get('club')
        if club_id:
            queryset = queryset.filter(club_id=club_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'upcoming':
            queryset = queryset.filter(start_date__gte=timezone.now())
        elif status_filter == 'past':
            queryset = queryset.filter(end_date__lt=timezone.now())
        elif status_filter == 'ongoing':
            queryset = queryset.filter(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
        
        # Filter by my events
        if self.request.query_params.get('my_events') == 'true':
            queryset = queryset.filter(
                Q(organizer=self.request.user) |
                Q(attendees=self.request.user)
            ).distinct()
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
        
        # Ordering
        order_by = self.request.query_params.get('order_by', 'start_date')
        if order_by in ['start_date', 'end_date', 'title', 'created_at']:
            if order_by == 'start_date':
                queryset = queryset.order_by('start_date')
            else:
                queryset = queryset.order_by(order_by)
        
        return queryset
    
    def perform_create(self, serializer):
        event = serializer.save(organizer=self.request.user)
        
        # Auto-RSVP organizer
        event.attendees.add(self.request.user)
        
        # Create notification for club members if event belongs to a club
        if event.club:
            for member in event.club.members.all():
                if member != self.request.user:
                    Notification.objects.create(
                        user=member,
                        notification_type='event',
                        title='New Club Event',
                        message=f'{event.club.name} has a new event: {event.title}',
                        related_id=event.id
                    )

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        event = self.get_object()
        if event.organizer != request.user and request.user.role not in ['admin', 'faculty']:
            return Response(
                {'error': 'You can only edit your own events'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        if event.organizer != request.user and request.user.role not in ['admin', 'faculty']:
            return Response(
                {'error': 'You can only delete your own events'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

class RSVPEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id, is_active=True)
        
        if event.is_full:
            return Response(
                {'error': 'Event is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event.start_date < timezone.now():
            return Response(
                {'error': 'Cannot RSVP to past events'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if event.attendees.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Already RSVPed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event.attendees.add(request.user)
        
        # Create notification for organizer
        Notification.objects.create(
            user=event.organizer,
            notification_type='event',
            title='New RSVP',
            message=f'{request.user.get_full_name()} has RSVPed to your event: {event.title}',
            related_id=event.id
        )
        
        return Response({
            'status': 'rsvp_success',
            'event': EventSerializer(event, context={'request': request}).data
        })

class CancelRSVPEventView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        if not event.attendees.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Not RSVPed to this event'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event.attendees.remove(request.user)
        
        # Notify organizer
        Notification.objects.create(
            user=event.organizer,
            notification_type='event',
            title='RSVP Cancelled',
            message=f'{request.user.get_full_name()} cancelled RSVP to your event: {event.title}',
            related_id=event.id
        )
        
        return Response({'status': 'rsvp_cancelled'})

class UpcomingEventsView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        return Event.objects.filter(
            is_active=True,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:50]

class UserEventsView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        user = self.request.user
        # Events user is attending or organizing
        return Event.objects.filter(
            Q(organizer=user) | Q(attendees=user),
            is_active=True
        ).distinct().order_by('start_date')