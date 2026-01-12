# unitribe_server/clubs/serializers.py - FIXED VERSION

from rest_framework import serializers
from .models import Club, ClubMembershipRequest, ClubRole
from users.serializers import UserBasicSerializer
from users.models import User  # Add this import
from django.utils import timezone

class ClubRoleSerializer(serializers.ModelSerializer):
    user_details = UserBasicSerializer(source='user', read_only=True)
    assigned_by_details = UserBasicSerializer(source='assigned_by', read_only=True)

    class Meta:
        model = ClubRole
        fields = '__all__'
        read_only_fields = ('assigned_at',)

class ClubMembershipRequestSerializer(serializers.ModelSerializer):
    user_details = UserBasicSerializer(source='user', read_only=True)
    club_name = serializers.CharField(source='club.name', read_only=True)
    processed_by_details = UserBasicSerializer(source='processed_by', read_only=True)

    class Meta:
        model = ClubMembershipRequest
        fields = '__all__'
        read_only_fields = ('created_at', 'processed_at', 'processed_by')

class ClubSerializer(serializers.ModelSerializer):
    president_details = UserBasicSerializer(source='president', read_only=True)
    faculty_advisor_details = UserBasicSerializer(source='faculty_advisor', read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    active_member_count = serializers.IntegerField(read_only=True)
    upcoming_events_count = serializers.IntegerField(read_only=True)
    is_member = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    executive_members = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'approved_by', 'approved_at', 'president')

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_member(request.user)
        return False

    def get_can_manage(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_manage(request.user)
        return False

    def get_executive_members(self, obj):
        executive_roles = ClubRole.objects.filter(
            club=obj,
            role__in=['president', 'vice_president', 'secretary', 'treasurer']
        )[:10]
        return ClubRoleSerializer(executive_roles, many=True).data

class ClubCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ('name', 'description', 'faculty_advisor', 'logo', 'banner',
                  'category', 'website', 'contact_email', 'meeting_schedule', 'rules')
        extra_kwargs = {
            'faculty_advisor': {'required': False, 'allow_null': True},
            'logo': {'required': False, 'allow_null': True},
            'banner': {'required': False, 'allow_null': True},
            'category': {'required': False, 'allow_blank': True},  
            'website': {'required': False, 'allow_blank': True},
            'contact_email': {'required': False, 'allow_blank': True},
            'meeting_schedule': {'required': False, 'allow_blank': True},
            'rules': {'required': False, 'allow_blank': True},
        }

    def validate_faculty_advisor(self, value):
        if value and value.role != 'faculty':
            raise serializers.ValidationError("Faculty advisor must be a faculty member.")
        return value
    
    def validate(self, attrs):
        # Make faculty_advisor optional by setting it to None if not provided
        if 'faculty_advisor' not in attrs:
            attrs['faculty_advisor'] = None
        return attrs

class ClubUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ('description', 'logo', 'banner', 'category',
                  'website', 'contact_email', 'meeting_schedule', 'rules')