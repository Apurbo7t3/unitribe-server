#unitribe_server/events/urls.py

from django.urls import path
from .views import (EventListCreateView, EventDetailView, RSVPEventView, 
                   CancelRSVPEventView, UpcomingEventsView, UserEventsView)

urlpatterns = [
    path('', EventListCreateView.as_view(), name='event-list-create'),
    path('upcoming/', UpcomingEventsView.as_view(), name='upcoming-events'),
    path('my-events/', UserEventsView.as_view(), name='user-events'),
    path('<int:pk>/', EventDetailView.as_view(), name='event-detail'),
    path('<int:event_id>/rsvp/', RSVPEventView.as_view(), name='rsvp-event'),
    path('<int:event_id>/cancel-rsvp/', CancelRSVPEventView.as_view(), name='cancel-rsvp-event'),
]

