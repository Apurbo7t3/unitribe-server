#unitribe_server/messaging/serializers.py

from rest_framework import serializers
from .models import Conversation, Message, UserMessageSettings
from users.serializers import UserBasicSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserBasicSerializer(source='sender', read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('created_at', 'read_at', 'is_read')

class ConversationSerializer(serializers.ModelSerializer):
    participants_details = UserBasicSerializer(source='participants', many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_group:
            other = obj.get_other_participant(request.user)
            if other:
                return UserBasicSerializer(other).data
        return None

class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = Conversation
        fields = ('participant_ids', 'is_group', 'group_name')
    
    def validate(self, attrs):
        participant_ids = attrs.get('participant_ids', [])
        
        if len(participant_ids) < 2:
            raise serializers.ValidationError("At least 2 participants required")
        
        if len(participant_ids) > 2 and not attrs.get('is_group'):
            raise serializers.ValidationError("Group conversation must have is_group=True")
        
        if attrs.get('is_group') and not attrs.get('group_name'):
            raise serializers.ValidationError("Group name required for group conversations")
        
        return attrs

class UserMessageSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMessageSettings
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')



