# unitribe_server/clubs/views.py - COMPLETED VERSION

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from .models import Club, ClubMembershipRequest, ClubRole
from .serializers import (
    ClubSerializer, ClubCreateSerializer, ClubUpdateSerializer,
    ClubMembershipRequestSerializer, ClubRoleSerializer
)
from users.serializers import UserBasicSerializer
from users.models import User
from notifications.models import Notification
import json

class ClubListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClubCreateSerializer
        return ClubSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = Club.objects.filter(status='active')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Filter by search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        
        # Filter by user membership
        if self.request.query_params.get('my_clubs') == 'true':
            queryset = queryset.filter(members=self.request.user)
        
        # Ordering
        order_by = self.request.query_params.get('order_by', 'name')
        if order_by in ['name', 'member_count', 'created_at']:
            if order_by == 'member_count':
                queryset = queryset.annotate(member_count=Count('members')).order_by('-member_count')
            else:
                queryset = queryset.order_by(order_by)
        
        return queryset
    
    def perform_create(self, serializer):
        # Set president to current user
        club = serializer.save(president=self.request.user)
        
        # Auto-join creator as member
        club.members.add(self.request.user)
        
        # Create president role
        ClubRole.objects.create(
            club=club,
            user=self.request.user,
            role='president',
            assigned_by=self.request.user
        )
        
        # Notify faculty advisor if provided
        if club.faculty_advisor:
            Notification.objects.create(
                user=club.faculty_advisor,
                notification_type='club',
                title='New Club Created',
                message=f'You have been assigned as faculty advisor for {club.name}',
                related_id=club.id
            )

class ClubDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ClubUpdateSerializer
        return ClubSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        club = self.get_object()
        if not club.can_manage(request.user):
            return Response(
                {'error': 'You do not have permission to edit this club'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        club = self.get_object()
        if not (request.user.role == 'admin' or request.user == club.president):
            return Response(
                {'error': 'You do not have permission to delete this club'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

class JoinClubView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, club_id):
        club = get_object_or_404(Club, id=club_id, status='active')
        
        if club.is_member(request.user):
            return Response(
                {'error': 'Already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if requires approval
        if club.rules and 'approval' in club.rules.lower():
            # Create membership request
            membership_request, created = ClubMembershipRequest.objects.get_or_create(
                club=club,
                user=request.user,
                defaults={'message': request.data.get('message', '')}
            )
            
            if not created:
                return Response(
                    {'error': 'Membership request already pending'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Notify club president and faculty advisor
            for user in [club.president, club.faculty_advisor]:
                if user:
                    Notification.objects.create(
                        user=user,
                        notification_type='club',
                        title='New Membership Request',
                        message=f'{request.user.get_full_name()} wants to join {club.name}',
                        related_id=club.id
                    )
            
            return Response({
                'status': 'pending_approval',
                'message': 'Membership request sent for approval'
            })
        else:
            # Direct join
            club.members.add(request.user)
            ClubRole.objects.create(
                club=club,
                user=request.user,
                role='member',
                assigned_by=request.user
            )
            
            Notification.objects.create(
                user=request.user,
                notification_type='club',
                title='Joined Club',
                message=f'You have successfully joined {club.name}',
                related_id=club.id
            )
            
            return Response({
                'status': 'joined',
                'club': ClubSerializer(club, context={'request': request}).data
            })

class LeaveClubView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, club_id):
        club = get_object_or_404(Club, id=club_id)
        
        if not club.is_member(request.user):
            return Response(
                {'error': 'Not a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is president
        if request.user == club.president:
            return Response(
                {'error': 'President cannot leave. Transfer presidency first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        club.members.remove(request.user)
        ClubRole.objects.filter(club=club, user=request.user).delete()
        
        return Response({'status': 'left'})

class ClubMembersView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserBasicSerializer
    
    def get_queryset(self):
        club = get_object_or_404(Club, id=self.kwargs['club_id'])
        if not (club.is_member(self.request.user) or club.can_manage(self.request.user)):
            return User.objects.none()
        return club.members.filter(is_active=True).order_by('first_name', 'last_name')

class UserClubsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClubSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        return self.request.user.clubs_joined.filter(status='active').order_by('name')

class ClubMembershipRequestsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClubMembershipRequestSerializer
    
    def get_queryset(self):
        club = get_object_or_404(Club, id=self.kwargs['club_id'])
        if not club.can_manage(self.request.user):
            return ClubMembershipRequest.objects.none()
        return ClubMembershipRequest.objects.filter(club=club, status='pending')

class ProcessMembershipRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, club_id, request_id):
        club = get_object_or_404(Club, id=club_id)
        membership_request = get_object_or_404(
            ClubMembershipRequest, 
            id=request_id, 
            club=club
        )
        
        if not club.can_manage(request.user):
            return Response(
                {'error': 'You do not have permission to process this request'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        action = request.data.get('action')  # 'approve' or 'reject'
        
        if action == 'approve':
            membership_request.status = 'approved'
            membership_request.processed_at = timezone.now()
            membership_request.processed_by = request.user
            membership_request.save()
            
            # Add user to club
            club.members.add(membership_request.user)
            ClubRole.objects.create(
                club=club,
                user=membership_request.user,
                role='member',
                assigned_by=request.user
            )
            
            # Notify user
            Notification.objects.create(
                user=membership_request.user,
                notification_type='club',
                title='Membership Approved',
                message=f'Your membership request for {club.name} has been approved',
                related_id=club.id
            )
            
            return Response({'status': 'approved'})
        
        elif action == 'reject':
            membership_request.status = 'rejected'
            membership_request.processed_at = timezone.now()
            membership_request.processed_by = request.user
            membership_request.save()
            
            # Notify user
            Notification.objects.create(
                user=membership_request.user,
                notification_type='club',
                title='Membership Rejected',
                message=f'Your membership request for {club.name} has been rejected',
                related_id=club.id
            )
            
            return Response({'status': 'rejected'})
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )

class ClubRolesView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClubRoleSerializer
    
    def get_queryset(self):
        club = get_object_or_404(Club, id=self.kwargs['club_id'])
        if not club.can_manage(self.request.user):
            return ClubRole.objects.none()
        return ClubRole.objects.filter(club=club)
    
    def perform_create(self, serializer):
        club = get_object_or_404(Club, id=self.kwargs['club_id'])
        if not club.can_manage(self.request.user):
            self.permission_denied(self.request)
        serializer.save(club=club, assigned_by=self.request.user)

class AdminClubApprovalView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['admin', 'faculty']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        clubs = Club.objects.filter(status='pending')
        serializer = ClubSerializer(clubs, many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, club_id):
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can approve clubs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        club = get_object_or_404(Club, id=club_id)
        action = request.data.get('action')  # 'approve' or 'reject'
        
        if action == 'approve':
            club.status = 'active'
            club.approved_by = request.user
            club.approved_at = timezone.now()
            club.save()
            
            # Notify club president
            Notification.objects.create(
                user=club.president,
                notification_type='club',
                title='Club Approved',
                message=f'Your club {club.name} has been approved and is now active',
                related_id=club.id
            )
            
            return Response({
                'status': 'approved',
                'club': ClubSerializer(club, context={'request': request}).data
            })
        
        elif action == 'reject':
            reason = request.data.get('reason', '')
            club.status = 'inactive'
            club.save()
            
            # Notify club president
            Notification.objects.create(
                user=club.president,
                notification_type='club',
                title='Club Rejected',
                message=f'Your club {club.name} has been rejected. Reason: {reason}',
                related_id=club.id
            )
            
            return Response({'status': 'rejected'})
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )