from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from users.models import User
from clubs.models import Club
from events.models import Event
from posts.models import Post

class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Time ranges
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        
        user_stats = {
            'total': total_users,
            'active': active_users,
            'verified': verified_users,
            'by_role': list(User.objects.values('role').annotate(count=Count('role'))),
            'new_today': User.objects.filter(date_joined__date=today).count(),
            'new_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
            'new_month': User.objects.filter(date_joined__date__gte=month_ago).count(),
        }
        
        # Club statistics
        total_clubs = Club.objects.count()
        active_clubs = Club.objects.filter(status='active').count()
        pending_clubs = Club.objects.filter(status='pending').count()
        
        club_stats = {
            'total': total_clubs,
            'active': active_clubs,
            'pending': pending_clubs,
            'by_category': list(Club.objects.filter(status='active').values('category').annotate(count=Count('category'))),
            'top_clubs': list(Club.objects.annotate(member_count=Count('members')).order_by('-member_count')[:10].values('id', 'name', 'member_count')),
        }
        
        # Event statistics
        total_events = Event.objects.count()
        upcoming_events = Event.objects.filter(start_date__gte=timezone.now()).count()
        past_events = Event.objects.filter(end_date__lt=timezone.now()).count()
        
        event_stats = {
            'total': total_events,
            'upcoming': upcoming_events,
            'past': past_events,
            'by_type': list(Event.objects.values('event_type').annotate(count=Count('event_type'))),
            'events_this_week': Event.objects.filter(
                start_date__date__gte=week_ago,
                start_date__date__lte=today
            ).count(),
        }
        
        # Post statistics
        total_posts = Post.objects.count()
        
        post_stats = {
            'total': total_posts,
            'by_type': list(Post.objects.values('post_type').annotate(count=Count('post_type'))),
            'posts_today': Post.objects.filter(created_at__date=today).count(),
            'posts_week': Post.objects.filter(created_at__date__gte=week_ago).count(),
        }
        
        # Engagement metrics
        engagement_stats = {
            'avg_clubs_per_user': Club.objects.annotate(member_count=Count('members')).aggregate(avg=models.Avg('member_count'))['avg'] or 0,
            'avg_events_per_user': Event.objects.annotate(attendee_count=Count('attendees')).aggregate(avg=models.Avg('attendee_count'))['avg'] or 0,
            'posts_per_day': Post.objects.filter(
                created_at__date__gte=month_ago
            ).extra({'date': "date(created_at)"}).values('date').annotate(count=Count('id')).order_by('date'),
        }
        
        # Recent activities
        recent_activities = {
            'new_users': User.objects.order_by('-date_joined')[:5].values('id', 'username', 'email', 'role', 'date_joined'),
            'new_clubs': Club.objects.order_by('-created_at')[:5].values('id', 'name', 'president__username', 'status', 'created_at'),
            'recent_events': Event.objects.order_by('-created_at')[:5].values('id', 'title', 'organizer__username', 'start_date', 'created_at'),
            'recent_posts': Post.objects.order_by('-created_at')[:5].values('id', 'title', 'author__username', 'post_type', 'created_at'),
        }
        
        return Response({
            'user_stats': user_stats,
            'club_stats': club_stats,
            'event_stats': event_stats,
            'post_stats': post_stats,
            'engagement_stats': engagement_stats,
            'recent_activities': recent_activities,
            'timestamp': timezone.now(),
        })

class UserEngagementAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Daily signups
        daily_signups = User.objects.filter(
            date_joined__date__gte=start_date
        ).extra({'date': "date(date_joined)"}).values('date').annotate(count=Count('id')).order_by('date')
        
        # Daily logins (approximation using last_login)
        daily_logins = User.objects.filter(
            last_login__date__gte=start_date
        ).extra({'date': "date(last_login)"}).values('date').annotate(count=Count('id')).order_by('date')
        
        # Active users by day (users who performed any activity)
        # This is simplified - in production you'd want a more accurate metric
        
        return Response({
            'daily_signups': list(daily_signups),
            'daily_logins': list(daily_logins),
            'period': {
                'start_date': start_date,
                'end_date': timezone.now().date(),
                'days': days,
            }
        })

class PlatformHealthView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # System health metrics
        health_metrics = {
            'database': {
                'users': User.objects.count(),
                'clubs': Club.objects.count(),
                'events': Event.objects.count(),
                'posts': Post.objects.count(),
            },
            'unverified_users': User.objects.filter(is_verified=False).count(),
            'pending_clubs': Club.objects.filter(status='pending').count(),
            'unread_notifications': sum(user.notifications.filter(is_read=False).count() for user in User.objects.all()),
            'reported_content': 0,  # Would come from a reporting system
            'active_sessions': 0,  # Would come from session tracking
        }
        
        # Issues to address
        issues = []
        
        if health_metrics['unverified_users'] > 50:
            issues.append({
                'type': 'users',
                'message': f'{health_metrics["unverified_users"]} users need email verification',
                'priority': 'medium'
            })
        
        if health_metrics['pending_clubs'] > 10:
            issues.append({
                'type': 'clubs',
                'message': f'{health_metrics["pending_clubs"]} clubs pending approval',
                'priority': 'high'
            })
        
        return Response({
            'health_metrics': health_metrics,
            'issues': issues,
            'timestamp': timezone.now(),
            'status': 'healthy' if len(issues) == 0 else 'needs_attention'
        })