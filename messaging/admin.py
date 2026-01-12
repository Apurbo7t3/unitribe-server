from django.contrib import admin
from .models import Conversation, Message, UserMessageSettings

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_group', 'group_name', 'group_admin', 'created_at', 'updated_at')
    filter_horizontal = ('participants',)
    search_fields = ('group_name', 'participants__email')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'content', 'is_read', 'created_at')
    search_fields = ('sender__email', 'content')

@admin.register(UserMessageSettings)
class UserMessageSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'allow_messages_from', 'message_notifications', 'sound_notifications', 'created_at')
    search_fields = ('user__email',)
