from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Fields shown in list view
    list_display = (
        'email', 'first_name', 'last_name', 'role', 'department', 
        'is_verified', 'is_active', 'student_id', 'date_joined'
    )
    list_filter = ('role', 'department', 'is_verified', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'student_id')
    ordering = ('-date_joined',)
    
    # Fields for add/edit user form
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'username', 'profile_picture', 'bio', 'department', 'interests')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
        ('Verification', {'fields': ('is_verified', 'email_verification_token', 'reset_password_token')}),
        ('Privacy', {'fields': ('show_email', 'show_profile')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role', 'is_active'),
        }),
    )
