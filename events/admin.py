from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'club', 'organizer', 'start_date', 'end_date', 'is_active', 'attendee_count', 'is_full')
    list_filter = ('event_type', 'club', 'is_active')
    search_fields = ('title', 'description', 'organizer__email', 'club__name')
    readonly_fields = ('created_at', 'updated_at', 'attendee_count', 'is_full')
    filter_horizontal = ('attendees',)
