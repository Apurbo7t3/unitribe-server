from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import os

from users.models import User
from events.models import Event
from posts.models import Post
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Clean up old data from the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep data (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"Cleaning up data older than {days} days (before {cutoff_date})")
        
        # Clean old notifications
        old_notifications = Notification.objects.filter(created_at__lt=cutoff_date)
        self.stdout.write(f"Found {old_notifications.count()} old notifications")
        
        if not dry_run:
            deleted_count, _ = old_notifications.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} old notifications"))
        
        # Clean old read notifications
        read_notifications = Notification.objects.filter(is_read=True, created_at__lt=cutoff_date - timedelta(days=30))
        self.stdout.write(f"Found {read_notifications.count()} old read notifications")
        
        if not dry_run:
            deleted_count, _ = read_notifications.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} old read notifications"))
        
        # Deactivate inactive users (no login for 180 days)
        inactive_cutoff = timezone.now() - timedelta(days=180)
        inactive_users = User.objects.filter(
            last_login__lt=inactive_cutoff,
            is_active=True
        ).exclude(role='admin')
        
        self.stdout.write(f"Found {inactive_users.count()} inactive users")
        
        if not dry_run:
            for user in inactive_users:
                user.is_active = False
                user.save()
            self.stdout.write(self.style.SUCCESS(f"Deactivated {inactive_users.count()} inactive users"))
        
        # Archive old events
        old_events = Event.objects.filter(end_date__lt=cutoff_date, is_active=True)
        self.stdout.write(f"Found {old_events.count()} old events to archive")
        
        if not dry_run:
            old_events.update(is_active=False)
            self.stdout.write(self.style.SUCCESS(f"Archived {old_events.count()} old events"))
        
        # Clean orphaned media files (you'd need to implement this based on your storage)
        # This is a placeholder for actual file cleanup logic
        
        self.stdout.write(self.style.SUCCESS("Cleanup completed successfully!"))