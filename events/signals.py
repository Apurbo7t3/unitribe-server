# unitribe_server/events/signals.py - ENHANCED VERSION

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Event
from notifications.models import Notification

@receiver(post_save, sender=Event)
def create_event_notifications(sender, instance, created, **kwargs):
    if created:
        # Notify club members if event is for a club
        if instance.club:
            for member in instance.club.members.all():
                if member != instance.organizer:
                    Notification.objects.create(
                        user=member,
                        notification_type='event',
                        title='New Club Event',
                        message=f'{instance.club.name} has a new event: {instance.title}',
                        related_id=instance.id
                    )
        
        # Notify organizer
        Notification.objects.create(
            user=instance.organizer,
            notification_type='event',
            title='Event Created',
            message=f'Your event "{instance.title}" has been created successfully',
            related_id=instance.id
        )
        
        # Schedule reminders for new event
        schedule_event_reminder(instance)

@receiver(pre_save, sender=Event)
def update_event_reminders(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Event.objects.get(pk=instance.pk)
            # Check if start date changed
            if old_instance.start_date != instance.start_date:
                # Delete existing reminders and create new ones
                Notification.objects.filter(
                    notification_type='event',
                    related_id=instance.id,
                    title__contains='Reminder'
                ).delete()
                # Schedule new reminders
                schedule_event_reminder(instance)
        except Event.DoesNotExist:
            pass

@receiver(pre_delete, sender=Event)
def delete_event_reminders(sender, instance, **kwargs):
    # Delete all notifications related to this event
    Notification.objects.filter(
        related_id=instance.id,
        notification_type='event'
    ).delete()

def schedule_event_reminder(event):
    """Schedule event reminders at different intervals"""
    reminder_times = [
        (event.start_date - timedelta(hours=24), '24 hours'),
        (event.start_date - timedelta(hours=1), '1 hour'),
        (event.start_date - timedelta(minutes=15), '15 minutes'),
    ]
    
    for reminder_time, time_text in reminder_times:
        if reminder_time > timezone.now():
            # Schedule reminder for organizer
            Notification.objects.create(
                user=event.organizer,
                notification_type='event',
                title=f'Event Reminder: {time_text}',
                message=f'Your event "{event.title}" starts in {time_text}',
                related_id=event.id,
                created_at=timezone.now()  # Current time for ordering
            )
            
            # Schedule reminders for attendees
            for attendee in event.attendees.all():
                if attendee != event.organizer:
                    Notification.objects.create(
                        user=attendee,
                        notification_type='event',
                        title=f'Event Reminder: {time_text}',
                        message=f'Event "{event.title}" starts in {time_text}',
                        related_id=event.id,
                        created_at=timezone.now()
                    )