#unitribe_server/messaging/urls.py

from django.urls import path
from .views import (
    ConversationListView, ConversationDetailView,
    MessageListView, MessageDetailView,
    MarkAllAsReadView, UserMessageSettingsView,
    SearchConversationsView, AddParticipantView,
    RemoveParticipantView
)

urlpatterns = [
    # Conversations
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/search/', SearchConversationsView.as_view(), name='search-conversations'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/mark-all-read/', MarkAllAsReadView.as_view(), name='mark-all-read'),
    path('conversations/<int:conversation_id>/add-participant/', AddParticipantView.as_view(), name='add-participant'),
    path('conversations/<int:conversation_id>/remove-participant/', RemoveParticipantView.as_view(), name='remove-participant'),
    
    # Messages
    path('conversations/<int:conversation_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    
    # Settings
    path('settings/', UserMessageSettingsView.as_view(), name='message-settings'),
]


