# unitribe_server/clubs/urls.py

from django.urls import path
from .views import (
    ClubListCreateView, ClubDetailView, JoinClubView, 
    LeaveClubView, ClubMembersView, UserClubsView,
    ClubMembershipRequestsView, ProcessMembershipRequestView,
    ClubRolesView, AdminClubApprovalView
)

urlpatterns = [
    # Clubs
    path('', ClubListCreateView.as_view(), name='club-list-create'),
    path('my-clubs/', UserClubsView.as_view(), name='user-clubs'),
    path('<int:pk>/', ClubDetailView.as_view(), name='club-detail'),
    path('<int:club_id>/join/', JoinClubView.as_view(), name='join-club'),
    path('<int:club_id>/leave/', LeaveClubView.as_view(), name='leave-club'),
    path('<int:club_id>/members/', ClubMembersView.as_view(), name='club-members'),
    
    # Membership Requests
    path('<int:club_id>/membership-requests/', ClubMembershipRequestsView.as_view(), name='club-membership-requests'),
    path('<int:club_id>/membership-requests/<int:request_id>/process/', ProcessMembershipRequestView.as_view(), name='process-membership-request'),
    
    # Club Roles
    path('<int:club_id>/roles/', ClubRolesView.as_view(), name='club-roles'),
    
    # Admin
    path('admin/pending/', AdminClubApprovalView.as_view(), name='admin-club-pending'),
    path('admin/<int:club_id>/approve/', AdminClubApprovalView.as_view(), name='admin-club-approve'),
]

