#unitribe_server/messaging/views.py

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Conversation, Message, UserMessageSettings
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer,
    MessageSerializer, UserMessageSettingsSerializer
)
from users.models import User
from notifications.models import Notification

class ConversationListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(participants=user).order_by('-updated_at')
    
    def perform_create(self, serializer):
        participant_ids = serializer.validated_data.pop('participant_ids')
        participants = User.objects.filter(id__in=participant_ids)
        
        # Add current user to participants
        participants = list(participants) + [self.request.user]
        
        # Check if conversation already exists (for 1-1)
        if not serializer.validated_data.get('is_group'):
            existing_conv = Conversation.objects.filter(
                is_group=False,
                participants__in=participants
            ).annotate(num_participants=Count('participants')).filter(num_participants=len(participants))
            
            if existing_conv.exists():
                raise serializers.ValidationError("Conversation already exists")
        
        conversation = serializer.save()
        conversation.participants.set(participants)
        
        if serializer.validated_data.get('is_group'):
            conversation.group_admin = self.request.user
            conversation.save()

class ConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if user is participant
        if request.user not in instance.participants.all():
            return Response(
                {'error': 'Not a participant'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark all messages as read
        instance.messages.filter(is_read=False).exclude(sender=request.user).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if user is group admin
        if instance.is_group and instance.group_admin != request.user:
            return Response(
                {'error': 'Only group admin can update'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.is_group and instance.group_admin != request.user:
            return Response(
                {'error': 'Only group admin can delete'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

class MessageListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Check if user is participant
        if self.request.user not in conversation.participants.all():
            return Message.objects.none()
        
        return Message.objects.filter(conversation=conversation).order_by('-created_at')[:100]
    
    def perform_create(self, serializer):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Check if user is participant
        if self.request.user not in conversation.participants.all():
            self.permission_denied(self.request)
        
        message = serializer.save(
            conversation=conversation,
            sender=self.request.user
        )
        
        # Create notifications for other participants
        for participant in conversation.participants.all():
            if participant != self.request.user:
                Notification.objects.create(
                    user=participant,
                    notification_type='message',
                    title='New Message',
                    message=f'New message from {self.request.user.get_full_name()}',
                    related_id=conversation.id
                )

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if user is in conversation
        if request.user not in instance.conversation.participants.all():
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark as read if not sender
        if instance.sender != request.user:
            instance.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class MarkAllAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        if request.user not in conversation.participants.all():
            return Response(
                {'error': 'Not a participant'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        updated = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'status': 'marked_as_read',
            'updated_count': updated
        })

class UserMessageSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMessageSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        obj, created = UserMessageSettings.objects.get_or_create(user=self.request.user)
        return obj

class SearchConversationsView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        search = self.request.query_params.get('search', '')
        user = self.request.user
        
        if not search:
            return Conversation.objects.none()
        
        # Search in conversation participants
        conversations = Conversation.objects.filter(
            participants=user
        ).filter(
            Q(group_name__icontains=search) |
            Q(messages__content__icontains=search)
        ).distinct().order_by('-updated_at')
        
        return conversations

class AddParticipantView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Check if user is group admin
        if not conversation.is_group or conversation.group_admin != request.user:
            return Response(
                {'error': 'Only group admin can add participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant_id = request.data.get('participant_id')
        if not participant_id:
            return Response(
                {'error': 'participant_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participant = User.objects.get(id=participant_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if participant in conversation.participants.all():
            return Response(
                {'error': 'User already in conversation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conversation.participants.add(participant)
        
        # Notify new participant
        Notification.objects.create(
            user=participant,
            notification_type='message',
            title='Added to Group',
            message=f'You have been added to group: {conversation.group_name}',
            related_id=conversation.id
        )
        
        return Response({
            'status': 'participant_added',
            'conversation': ConversationSerializer(conversation, context={'request': request}).data
        })

class RemoveParticipantView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Check if user is group admin
        if not conversation.is_group or conversation.group_admin != request.user:
            return Response(
                {'error': 'Only group admin can remove participants'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant_id = request.data.get('participant_id')
        if not participant_id:
            return Response(
                {'error': 'participant_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if participant_id == request.user.id:
            return Response(
                {'error': 'Cannot remove yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participant = User.objects.get(id=participant_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if participant not in conversation.participants.all():
            return Response(
                {'error': 'User not in conversation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conversation.participants.remove(participant)
        
        # Notify removed participant
        Notification.objects.create(
            user=participant,
            notification_type='message',
            title='Removed from Group',
            message=f'You have been removed from group: {conversation.group_name}',
            related_id=conversation.id
        )
        
        return Response({
            'status': 'participant_removed'
        })
    

