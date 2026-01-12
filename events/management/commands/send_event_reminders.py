#unitribe_server/events/management/commands/send_event_reminders.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.models import Notification
from events.models import Event
from django.core.mail import send_mail
from django.conf import settings
import json

class Command(BaseCommand):
    help = 'Send scheduled event reminders'
    
    def handle(self, *args, **options):
        now = timezone.now()
        
        # Get notifications scheduled for now or earlier that haven't been sent
        reminders = Notification.objects.filter(
            notification_type='event',
            created_at__lte=now,
            title__contains='Reminder',
            is_read=False
        )
        
        for reminder in reminders:
            try:
                # Send email reminder
                event = Event.objects.get(id=reminder.related_id)
                
                subject = f'UniTribe Event Reminder: {event.title}'
                message = f"""
                Event Reminder:
                
                Title: {event.title}
                Time: {event.start_date.strftime("%Y-%m-%d %H:%M")}
                Location: {event.location}
                Description: {event.description[:200]}...
                
                View event details: {settings.FRONTEND_URL}/events/{event.id}/
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [reminder.user.email],
                    fail_silently=False,
                )
                
                # Mark as read
                reminder.is_read = True
                reminder.save()
                
                self.stdout.write(self.style.SUCCESS(f'Sent reminder to {reminder.user.email}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error sending reminder: {str(e)}'))


