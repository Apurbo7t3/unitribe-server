# clubs/admin.py
from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from .models import Club, ClubMembershipRequest, ClubRole
from users.models import User

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'status_display',  # Use custom display method
        'category', 
        'president_link', 
        'faculty_advisor_link',
        'member_count', 
        'upcoming_events_count',
        'created_at',
        'approval_actions'  # Quick approval actions
    )
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('name', 'description', 'president__email', 'faculty_advisor__email')
    readonly_fields = ('created_at', 'updated_at', 'member_count', 'active_member_count', 'upcoming_events_count')
    actions = ['approve_clubs', 'reject_clubs', 'activate_clubs', 'suspend_clubs']
    filter_horizontal = ('members',)
    
    # Custom fieldsets for better organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'status')
        }),
        ('Leadership', {
            'fields': ('president', 'faculty_advisor')
        }),
        ('Club Details', {
            'fields': ('logo', 'banner', 'website', 'contact_email', 'meeting_schedule', 'rules')
        }),
        ('Members', {
            'fields': ('members',)
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'member_count', 'active_member_count', 'upcoming_events_count'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom method to display status with colored badge
    def status_display(self, obj):
        status_colors = {
            'pending': 'orange',
            'active': 'green',
            'suspended': 'red',
            'inactive': 'gray'
        }
        color = status_colors.get(obj.status, 'blue')
        return format_html(
            '<span style="display: inline-block; padding: 3px 8px; border-radius: 12px; '
            'background-color: {}; color: white; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    # Link to president user
    def president_link(self, obj):
        if obj.president:
            url = reverse('admin:users_user_change', args=[obj.president.id])
            return format_html('<a href="{}">{}</a>', url, obj.president.email)
        return '-'
    president_link.short_description = 'President'
    
    # Link to faculty advisor user
    def faculty_advisor_link(self, obj):
        if obj.faculty_advisor:
            url = reverse('admin:users_user_change', args=[obj.faculty_advisor.id])
            return format_html('<a href="{}">{}</a>', url, obj.faculty_advisor.email)
        return '-'
    faculty_advisor_link.short_description = 'Faculty Advisor'
    
    # Quick approval actions in list view
    def approval_actions(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:clubs_club_approve', args=[obj.id])
            reject_url = reverse('admin:clubs_club_reject', args=[obj.id])
            return format_html(
                '<a href="{}" class="button" style="background: green; color: white; padding: 5px 10px; border-radius: 3px; margin-right: 5px;">✓ Approve</a>'
                '<a href="{}" class="button" style="background: red; color: white; padding: 5px 10px; border-radius: 3px;">✗ Reject</a>',
                approve_url, reject_url
            )
        return format_html(
            '<span style="color: gray; font-size: 12px;">{}</span>',
            obj.get_status_display()
        )
    approval_actions.short_description = 'Actions'
    
    # Custom admin actions
    def approve_clubs(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='active',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} club(s) approved successfully.')
    
    def reject_clubs(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='inactive')
        self.message_user(request, f'{updated} club(s) rejected.')
    
    def activate_clubs(self, request, queryset):
        updated = queryset.filter(status='inactive').update(status='active')
        self.message_user(request, f'{updated} club(s) activated.')
    
    def suspend_clubs(self, request, queryset):
        updated = queryset.update(status='suspended')
        self.message_user(request, f'{updated} club(s) suspended.')
    
    approve_clubs.short_description = "✓ Approve selected clubs"
    reject_clubs.short_description = "✗ Reject selected clubs"
    activate_clubs.short_description = "Activate selected clubs"
    suspend_clubs.short_description = "Suspend selected clubs"
    
    # Custom view URLs for approval
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:club_id>/approve/', self.admin_site.admin_view(self.approve_view), name='clubs_club_approve'),
            path('<int:club_id>/reject/', self.admin_site.admin_view(self.reject_view), name='clubs_club_reject'),
        ]
        return custom_urls + urls
    
    def approve_view(self, request, club_id):
        from django.shortcuts import get_object_or_404, redirect
        club = get_object_or_404(Club, id=club_id)
        if club.status == 'pending':
            club.status = 'active'
            club.approved_by = request.user
            club.approved_at = timezone.now()
            club.save()
            
            # Send notification to club president
            from notifications.models import Notification
            Notification.objects.create(
                user=club.president,
                notification_type='club',
                title='Club Approved',
                message=f'Your club "{club.name}" has been approved and is now active!',
                related_id=club.id
            )
            
            messages.success(request, f'Club "{club.name}" approved successfully.')
        else:
            messages.warning(request, f'Club "{club.name}" is already {club.get_status_display()}.')
        
        return redirect('admin:clubs_club_changelist')
    
    def reject_view(self, request, club_id):
        from django.shortcuts import get_object_or_404, redirect
        club = get_object_or_404(Club, id=club_id)
        if club.status == 'pending':
            club.status = 'inactive'
            club.save()
            
            # Send notification to club president
            from notifications.models import Notification
            Notification.objects.create(
                user=club.president,
                notification_type='club',
                title='Club Rejected',
                message=f'Your club "{club.name}" has been rejected.',
                related_id=club.id
            )
            
            messages.success(request, f'Club "{club.name}" rejected.')
        else:
            messages.warning(request, f'Club "{club.name}" is already {club.get_status_display()}.')
        
        return redirect('admin:clubs_club_changelist')

@admin.register(ClubMembershipRequest)
class ClubMembershipRequestAdmin(admin.ModelAdmin):
    list_display = ('club', 'user', 'status_display', 'created_at', 'processed_at', 'processed_by')
    list_filter = ('status', 'club', 'created_at')
    search_fields = ('user__email', 'club__name', 'message')
    readonly_fields = ('created_at', 'processed_at')
    actions = ['approve_requests', 'reject_requests']
    
    def status_display(self, obj):
        status_colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        color = status_colors.get(obj.status, 'blue')
        return format_html(
            '<span style="display: inline-block; padding: 3px 8px; border-radius: 12px; '
            'background-color: {}; color: white; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_status_display().upper()
        )
    status_display.short_description = 'Status'
    
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='approved',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        
        # Add users to clubs
        for request_obj in queryset.filter(status='approved'):
            request_obj.club.members.add(request_obj.user)
            from notifications.models import Notification
            Notification.objects.create(
                user=request_obj.user,
                notification_type='club',
                title='Membership Approved',
                message=f'Your membership request for {request_obj.club.name} has been approved.',
                related_id=request_obj.club.id
            )
        
        self.message_user(request, f'{updated} membership request(s) approved.')
    
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            processed_by=request.user,
            processed_at=timezone.now()
        )
        
        # Notify users
        for request_obj in queryset.filter(status='rejected'):
            from notifications.models import Notification
            Notification.objects.create(
                user=request_obj.user,
                notification_type='club',
                title='Membership Rejected',
                message=f'Your membership request for {request_obj.club.name} has been rejected.',
                related_id=request_obj.club.id
            )
        
        self.message_user(request, f'{updated} membership request(s) rejected.')
    
    approve_requests.short_description = "✓ Approve selected requests"
    reject_requests.short_description = "✗ Reject selected requests"

@admin.register(ClubRole)
class ClubRoleAdmin(admin.ModelAdmin):
    list_display = ('club', 'user', 'role_display', 'assigned_by', 'assigned_at')
    list_filter = ('role', 'club')
    search_fields = ('user__email', 'club__name', 'assigned_by__email')
    readonly_fields = ('assigned_at',)
    
    def role_display(self, obj):
        role_colors = {
            'president': 'purple',
            'vice_president': 'blue',
            'secretary': 'teal',
            'treasurer': 'green',
            'member': 'gray'
        }
        color = role_colors.get(obj.role, 'blue')
        return format_html(
            '<span style="display: inline-block; padding: 3px 8px; border-radius: 12px; '
            'background-color: {}; color: white; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_display.short_description = 'Role'