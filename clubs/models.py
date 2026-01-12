# unitribe_server/clubs/models.py


from django.db import models
from users.models import User
from django.utils import timezone

class Club(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    president = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clubs_presiding')
    faculty_advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clubs_advising')
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='club_banners/', blank=True, null=True)
    members = models.ManyToManyField(User, related_name='clubs_joined', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    category = models.CharField(max_length=100, blank=True)  # Academic, Cultural, Sports, etc.
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    meeting_schedule = models.TextField(blank=True)  # e.g., "Every Tuesday, 4 PM"
    rules = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='clubs_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def active_member_count(self):
        return self.members.filter(is_active=True).count()
    
    @property
    def upcoming_events_count(self):
        from events.models import Event
        return self.events.filter(is_active=True, start_date__gte=timezone.now()).count()
    
    def is_member(self, user):
        return self.members.filter(id=user.id).exists()
    
    def can_manage(self, user):
        return (user == self.president or 
                user == self.faculty_advisor or
                user.role in ['admin', 'faculty'])

class ClubMembershipRequest(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='membership_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_membership_requests')
    
    class Meta:
        unique_together = ['club', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} -> {self.club}"

class ClubRole(models.Model):
    ROLE_CHOICES = [
        ('president', 'President'),
        ('vice_president', 'Vice President'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='roles')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='club_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['club', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.role} in {self.club}"
    

